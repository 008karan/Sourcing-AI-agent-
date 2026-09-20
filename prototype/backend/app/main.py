from __future__ import annotations
import csv
import io
import json
import re
from pathlib import Path
from typing import Literal
from uuid import uuid4
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from . import repository as repo, pipeline, graph, jobs, rfx_intake, suppliers, insights
from .ai import draft_rfx, has_ai, interpret_scenario, ai_extract_text, transcribe_audio
from .scenario import solve_scenario, ValidatedSpec
from .store import ROOT, DATA_DIR

app=FastAPI(title='Aerchain Sourcing Decision Room',version='1.0.0')
app.mount('/assets',StaticFiles(directory=ROOT/'frontend'),name='assets')

@app.exception_handler(ValueError)
async def bad_value(request,exc):return JSONResponse(status_code=422,content={'detail':str(exc)})
@app.exception_handler(KeyError)
async def not_found(request,exc):return JSONResponse(status_code=404,content={'detail':str(exc)})
@app.exception_handler(RuntimeError)
async def unavailable(request,exc):return JSONResponse(status_code=503,content={'detail':str(exc)})

@app.middleware('http')
async def local_writes(request:Request,call_next):
    origin=request.headers.get('origin')
    if request.method not in {'GET','HEAD','OPTIONS'} and origin and origin != str(request.base_url).rstrip('/'):
        return JSONResponse(status_code=403,content={'detail':'Cross-origin writes are disabled.'})
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    return response

class Ask(BaseModel):question:str=Field(min_length=1,max_length=3000)
class IntakeMessage(BaseModel):message:str=Field(min_length=1,max_length=4000)
class NewSupplier(BaseModel):
    model_config=ConfigDict(extra='forbid')
    name:str=Field(min_length=2,max_length=120)
    email:str=Field(default='',max_length=200)
class Draft(BaseModel):prompt:str=Field(min_length=1,max_length=6000)
class WorkflowRequest(BaseModel):
    action:Literal['start','resume','retry']
    approved:bool=False
    actor:str=Field(default='Priya Menon',min_length=1,max_length=100)
    use_ai:bool=True
class Resolve(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    action:Literal['accept','correct','conversion','remap','not_quoted','exclude']
    actor:str=Field(min_length=1,max_length=100)
    reason:str=Field(min_length=1,max_length=3000)
    expected_version:int
    changes:dict={}
    target_line:int|None=None
    clarification_id:str|None=None
class Clarification(BaseModel):
    action:Literal['draft','send','reply']
    actor:str=Field(default='Priya Menon',min_length=1,max_length=100)
    text:str=Field(default='',max_length=10000)
    clarification_id:str|None=None

@app.get('/')
def home():return FileResponse(ROOT/'frontend'/'index.html')
@app.get('/health')
def health():return {'status':'ok','ai_configured':has_ai(),'version':'1.0.0'}
@app.get('/api/state')
def state():return repo.read()
@app.get('/api/event')
def event():
    d=repo.read();r=d['rfx']
    return {**{k:r[k] for k in ['event_id','title','category','buyer','expected_annual_spend_inr']},'dataset_version':d['dataset_version'],'stage':d['stage'],'rfx_status':d['rfx_status'],'line_count':len(r['items']),'vendor_count':len(d['vendors']),'exception_count':sum(e['status']!='resolved_by_buyer' for e in d['exceptions'])}
@app.get('/api/rfx')
def rfx():return repo.read()['rfx']
@app.post('/api/rfx/draft')
def draft(req:Draft):
    d=repo.read();r=d['rfx']
    if d['rfx_status']=='approved':raise ValueError('This released RFx is frozen for the sourcing event.')
    baseline={'scope':r['scope'],'line_count':len(r['items']),'questionnaire':[{'question':q['question'],'answer_type':q['type'],'mandatory':q['mandatory'],'qualification_rule':str(q.get('maximum',q.get('minimum',''))) or None} for q in r['questionnaire']], 'commercial_terms':{'comparison_basis':'landed cost excluding GST','base_currency':'INR','tax_treatment':'GST excluded','freight_requirement':'State freight explicitly','quote_validity_days':60}}
    result,mode=draft_rfx(req.prompt,baseline)
    # The fixed event retains its 30 specifications and qualification IDs. Copilot
    # proposals are versioned alongside the released contract, never silently remapped.
    repo.change('rfx_drafted','buyer',lambda d:d.update(draft=result,draft_mode=mode,rfx_version=d['rfx_version']+1))
    return {'draft':result,'mode':mode,'note':'30 baseline lines and original qualification rules are retained; proposed questionnaire changes are advisory.'}
@app.get('/api/rfx/checklist')
def checklist():
    d=repo.read()
    return {'checklist':d.get('rfx_checklist') or rfx_intake.blank_checklist(),'chat':d.get('rfx_chat',[]),
            'ready':bool(d.get('rfx_ready')),'rfx_status':d['rfx_status']}

@app.post('/api/rfx/chat')
def rfx_chat(req:IntakeMessage):
    d=repo.read()
    if d['rfx_status']=='approved':raise ValueError('This RFx is released and frozen for the sourcing event.')
    history=list(d.get('rfx_chat') or [])
    if len(history)>60:raise ValueError('This intake conversation is too long. Release the RFx or start again.')
    history.append({'role':'buyer','text':req.message,'at':repo.now()})
    result,mode=rfx_intake.run_turn(history,d.get('rfx_checklist'),d['rfx'])
    history.append({'role':'copilot','text':result['reply'],'at':repo.now(),
                    'questions':result['next_questions'],'mode':mode})
    def mutate(data):
        data.update(rfx_chat=history,rfx_checklist=result['checklist'],rfx_intake_mode=mode,
                    rfx_ready=result['ready'],rfx_confirmation=result['confirmation_summary'])
    repo.change('rfx_intake_turn',d['rfx']['buyer'],mutate)
    return {**result,'mode':mode}

@app.post('/api/rfx/chat/reset')
def rfx_chat_reset():
    if repo.read()['rfx_status']=='approved':raise ValueError('A released RFx cannot be restarted.')
    repo.change('rfx_intake_reset','buyer',lambda d:d.update(
        rfx_chat=[],rfx_checklist=rfx_intake.blank_checklist(),rfx_ready=False,rfx_confirmation=None,draft=None))
    return {'checklist':rfx_intake.blank_checklist(),'chat':[],'ready':False}

@app.get('/api/suppliers/match')
def supplier_match_preview():
    d=repo.read()
    return suppliers.match(d['rfx'],d['vendors'],d.get('rfx_checklist'))

@app.post('/api/rfx/share')
def share(req:WorkflowRequest|None=None):
    """Release the RFx to matched suppliers. The match itself is deterministic."""
    d=repo.read()
    actor=(req.actor if req else None) or d['rfx']['buyer']
    if not d.get('rfx_ready') and d['rfx_status']!='approved':
        raise ValueError('Complete every required checklist item before sharing this RFx.')
    if d['rfx_status']!='approved':
        if not d.get('workflow_id'):graph.run('start',use_ai=True,actor=actor)
        graph.run('resume',approved=True,actor=actor)
    result=suppliers.match(repo.read()['rfx'],repo.read()['vendors'],d.get('rfx_checklist'))
    result['shared_at']=repo.now()
    result['actor']=actor
    repo.change('rfx_shared_with_suppliers',actor,lambda data:data.update(supplier_match=result))
    return result

@app.post('/api/suppliers')
def add_supplier(req:NewSupplier):
    """Register a supplier the buyer wants to test this event with."""
    d=repo.read()
    name=req.name.strip()
    slug=re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')[:32] or 'supplier'
    if any(v['name'].strip().lower()==name.lower() for v in d['vendors'].values()):
        raise ValueError('A supplier with this name is already in this event.')
    vid=slug
    n=2
    while vid in d['vendors']:
        vid=f'{slug}-{n}';n+=1
    repo.change('supplier_added:'+vid,d['rfx']['buyer'],
                lambda data:data['vendors'].__setitem__(vid,repo.blank_vendor(vid,name,email=req.email.strip() or None,custom=True)))
    return {'vendor':repo.read()['vendors'][vid],'dataset_version':repo.read()['dataset_version']}

@app.delete('/api/suppliers/{vid}')
def remove_supplier(vid:str):
    d=repo.read()
    v=d['vendors'].get(vid)
    if not v:raise KeyError('Unknown supplier')
    if not v.get('custom'):raise ValueError('Only suppliers you added can be removed.')
    def mutate(data):
        data['vendors'].pop(vid,None)
        data['exceptions']=[e for e in data['exceptions'] if e['vendor_id']!=vid]
        pipeline.rebuild(data)
    repo.change('supplier_removed:'+vid,d['rfx']['buyer'],mutate)
    return {'dataset_version':repo.read()['dataset_version']}

@app.get('/api/insights/suppliers')
def supplier_insights():return insights.supplier_metrics(repo.read())

@app.get('/api/insights/scenarios')
def scenario_board():
    """Scenario-wise supplier standings: one row per buying priority."""
    return build_scenario_board(repo.read())

@app.post('/api/analyze')
def analyze(req:Ask):
    d=repo.read()
    if d['rfx_status']!='approved' or not d['comparison']:
        raise ValueError('Approve the RFx and process responses before analysis')
    vendor_ids=list(d['vendors'])
    plan,mode=insights.route(req.question,vendor_ids)
    if plan['intent']=='award_scenario':
        spec,spec_mode=interpret_scenario(req.question,vendor_ids)
        scenario=run_scenario(spec,req.question,spec_mode)
        charts=[]
        if scenario['status']=='ok':
            charts=[insights.savings_stat(scenario),insights.award_mix_chart(scenario),insights.award_lines_chart(scenario)]
        return {'mode':'scenario','router':mode,'scenario':scenario,'charts':charts,'question':req.question}
    if plan['intent']=='award_mix':
        latest=next((s for s in repo.scenarios() if s.get('status')=='ok'),None)
        if not latest:
            return {'mode':'chart','router':mode,'question':req.question,'title':'No award yet',
                    'narrative':'Run an award scenario first — then the share of spend can be charted.',
                    'charts':[]}
        return {'mode':'chart','router':mode,'question':req.question,'title':plan['title'],
                'narrative':plan['narrative'] or 'How the most recent award divides across suppliers.',
                'charts':[insights.award_mix_chart(latest),insights.award_lines_chart(latest)],
                'scenario_id':latest['id']}
    metric=plan['metric'] if plan['metric'] in insights.METRICS else 'landed_avg'
    chart=insights.metric_chart(metric,d,plan['supplier_ids'] or None,
                                'bar' if plan['chart_type'] not in {'donut','stat'} else plan['chart_type'],
                                plan['title'] or None)
    narrative=plan['narrative'] or _default_narrative(chart)
    return {'mode':'chart','router':mode,'question':req.question,'title':chart.get('title'),
            'narrative':narrative,'charts':[chart],'metric':metric}

def _default_narrative(chart):
    if chart['type']=='empty' or not chart.get('series'):return chart.get('note','')
    leader=next((s for s in chart['series'] if s['id']==chart.get('leader_id')),None)
    if not leader:return chart.get('note','')
    direction='lowest' if chart.get('better')=='lower' else 'highest'
    return f"{leader['full_label']} has the {direction} value at {leader['display']}, across {len(chart['series'])} suppliers with a reviewed number."

SCENARIO_ROWS=[
    ('best_price','Best price','Lowest average landed cost per piece','landed_avg'),
    ('best_value','Best value vs last year','Largest reduction against the FY26 baseline','price_index'),
    ('most_complete','Most complete quote','Most requirement lines with a usable price','coverage'),
    ('fastest','Fastest delivery','Shortest declared lead time','lead_days'),
    ('most_compliant','Quality & compliance','Qualification gates cleared, fewest open reviews','open_reviews'),
    ('proven','Proven relationship','Strongest delivery record and previous award history','on_time_pct'),
    ('most_awarded','Previous deals','Most events already awarded to this supplier','past_awards'),
    ('lowest_risk','Cleanest data','Highest extraction confidence on priced lines','confidence'),
]

def build_scenario_board(d):
    rows=insights.supplier_metrics(d)
    vendors=[v for v in rows.values() if v['response_status']=='processed'] or list(rows.values())
    order=[v['vendor_id'] for v in vendors]
    board=[]
    for key,label,meaning,metric in SCENARIO_ROWS:
        spec=insights.METRICS[metric]
        cells=[]
        for vid in order:
            value=rows[vid].get(metric)
            cells.append({'vendor_id':vid,'value':value,'display':insights.display(value,spec['format']),
                          'qualification':rows[vid]['qualification']})
        scored=[c for c in cells if c['value'] is not None]
        leaders,runners=[],[]
        if scored:
            scored.sort(key=lambda c:c['value'],reverse=spec['better']=='higher')
            # Ties share a place, so equal values are never tagged differently — and a
            # row where everyone ties separates nobody, so it highlights no one.
            leaders=[] if len({c['value'] for c in scored})<2 else [c['vendor_id'] for c in scored if c['value']==scored[0]['value']]
            second=next((c['value'] for c in scored if c['vendor_id'] not in leaders),None)
            runners=[c['vendor_id'] for c in scored if c['value']==second] if second is not None else []
            for cell in cells:
                cell['rank']=next((i+1 for i,c in enumerate(scored) if c['vendor_id']==cell['vendor_id']),None)
        leader=leaders[0] if leaders else None
        if key=='most_compliant':
            for cell in cells:
                if cell['qualification']!='pass':
                    cell['blocked']=True
            eligible=[c for c in cells if c['value'] is not None and c['qualification']=='pass']
            best=min((c['value'] for c in eligible),default=None)
            leaders=[c['vendor_id'] for c in eligible if c['value']==best] if best is not None else []
            second=next((c['value'] for c in sorted(eligible,key=lambda c:c['value']) if c['vendor_id'] not in leaders),None)
            runners=[c['vendor_id'] for c in eligible if c['value']==second] if second is not None else []
            leader=leaders[0] if leaders else None
        board.append({'id':key,'label':label,'meaning':meaning,'metric':metric,
                      'unit':spec['unit'],'better':spec['better'],
                      'leader_id':leader,'leader_ids':leaders,'runner_up_ids':runners,'cells':cells})
    wins={}
    for row in board:
        for vid in row['leader_ids']:wins[vid]=wins.get(vid,0)+1
    return {'suppliers':[{'vendor_id':v['vendor_id'],'name':v['name'],'short_name':v['short_name'],
                          'qualification':v['qualification'],'relationship':v['relationship'],
                          'wins':wins.get(v['vendor_id'],0)} for v in vendors],
            'rows':board,'scenario_count':len(board)}

@app.get('/api/workflow')
def workflow_status():return graph.status()
@app.post('/api/workflow')
def workflow(req:WorkflowRequest):return graph.run(**req.model_dump())
@app.get('/api/responses')
def responses():
    return [{**{k:v.get(k) for k in ['id','name','format','quality','response_status','method','file','checksum']},'lead_days':v['lead'],'coverage':len(v['facts'])} for v in repo.read()['vendors'].values()]
@app.post('/api/demo/inbox')
def demo_inbox():
    return {'dataset_version':pipeline.receive_demo()['dataset_version']}
@app.post('/api/process')
def process():return jobs.start()
@app.get('/api/jobs/{jid}')
def job(jid:str):return jobs.read(jid)
@app.post('/api/responses/{vid}/receive')
def receive(vid:str,body:str=Form(''),subject:str=Form('Supplier response'),sender_email:str=Form(''),files:list[UploadFile]=File(default=[])):
    current=repo.read()
    if vid not in current['vendors']:raise KeyError('Unknown supplier')
    if current['rfx_status']!='approved':raise ValueError('Approve the RFx before receiving a response')
    if not body.strip() and not files:raise ValueError('Add an email body or at least one attachment')
    if len(body)>30000 or len(files)>5:raise ValueError('Use at most 30,000 message characters and five attachments')
    docs=[];total=0
    folder=repo.runtime_dir()/'uploads'/str(uuid4());folder.mkdir(parents=True)
    for file in files:
        name=Path(file.filename or 'response').name;suffix=Path(name).suffix.lower()
        if suffix not in {'.xlsx','.docx','.pdf','.eml','.txt','.jpg','.jpeg','.png','.webp'}:raise ValueError('Unsupported attachment format')
        content=file.file.read(12*1024*1024+1);total+=len(content)
        if len(content)>12*1024*1024 or total>24*1024*1024:raise ValueError('Use files below 12 MB and packets below 24 MB')
        path=folder/(str(uuid4())+suffix);path.write_bytes(content)
        docs.append({'path':str(path),'filename':name})
    if body.strip():
        path=folder/'email-body.txt';path.write_text(body)
        docs.insert(0,{'path':str(path),'filename':'email-body.txt','cover_note':bool(files)})
    d=pipeline.receive(vid,docs,body,subject,sender_email.strip() or None)
    return {'dataset_version':d['dataset_version'],'status':'received','vendor':d['vendors'][vid]}
@app.get('/api/responses/{vid}/documents/{index}')
def response_document(vid:str,index:int):
    docs=repo.read()['vendors'][vid].get('documents',[])
    if index<0 or index>=len(docs):raise KeyError('Document not found')
    return FileResponse(docs[index]['path'],filename=docs[index]['filename'],content_disposition_type='inline')
@app.post('/api/transcribe')
def transcribe(file:UploadFile=File(...)):
    mime=(file.content_type or '').split(';')[0]
    if mime not in {'audio/webm','audio/mp4','audio/wav','audio/mpeg','audio/ogg','audio/x-m4a'}:raise ValueError('Unsupported audio type')
    data=file.file.read(10*1024*1024+1)
    if len(data)>10*1024*1024:raise ValueError('Record a shorter request (maximum 10 MB)')
    return {'text':transcribe_audio(data,mime)}
@app.post('/api/responses/{vid}/ingest')
def ingest(vid:str):
    if vid not in repo.read()['vendors']:raise KeyError('Unknown supplier')
    d=pipeline.ingest(vid)
    return {'dataset_version':d['dataset_version'],'vendor':d['vendors'][vid]}
@app.post('/api/responses/{vid}/upload')
def upload(vid:str,file:UploadFile=File(...)):
    current=repo.read()
    if vid not in current['vendors']:raise KeyError('Unknown supplier')
    if current['rfx_status']!='approved':raise ValueError('Approve RFx before uploading a response')
    suffix=Path(file.filename or '').suffix.lower()
    if suffix not in {'.xlsx','.docx','.pdf','.eml','.txt','.jpg','.jpeg','.png','.webp'}:raise ValueError('Unsupported response format')
    content=file.file.read(12*1024*1024+1)
    if len(content)>12*1024*1024:raise ValueError('Response exceeds the 12 MB limit')
    path=repo.runtime_dir()/'uploads'/(str(uuid4())+suffix);path.parent.mkdir(exist_ok=True)
    path.write_bytes(content)
    d=pipeline.receive(vid,[{'path':str(path),'filename':Path(file.filename).name}])
    return {'dataset_version':d['dataset_version'],'vendor':d['vendors'][vid]}
@app.get('/api/comparison')
def comparison():return repo.read()['comparison']
@app.get('/api/exceptions')
def exceptions():return repo.read()['exceptions']
@app.post('/api/exceptions/{eid}/resolve')
def resolve(eid:str,req:Resolve):
    payload=req.model_dump()
    if req.clarification_id:
        c=next((c for c in repo.read()['clarifications'] if c['id']==req.clarification_id and c['exception_id']==eid),None)
        if not c or c['status']!='replied':raise ValueError('A linked supplier reply is required')
        payload['reply']={'id':c['id'],'text':c['reply'],'received_at':c['replied_at']}
    d=pipeline.resolve(eid,payload)
    return {'dataset_version':d['dataset_version']}
@app.post('/api/exceptions/{eid}/clarification')
def clarification(eid:str,req:Clarification):
    d=repo.read();e=next((e for e in d['exceptions'] if e['id']==eid),None)
    if not e:raise KeyError('Exception not found')
    cid=req.clarification_id or str(uuid4())
    proposal=None
    if req.action=='reply' and has_ai():
        proposal=ai_extract_text(req.text,pipeline.context(d['rfx']))
    def mutate(d):
        if req.action=='draft':
            text=req.text or f"Please clarify {e['title']} for {d['rfx']['event_id']}. {e['detail']} Please provide the exact rate, currency, unit/pack size, freight treatment and applicable source evidence."
            d['clarifications'].append({'id':cid,'exception_id':eid,'vendor_id':e['vendor_id'],'text':text,'status':'draft','created_at':repo.now(),'actor':req.actor})
        else:
            c=next((c for c in d['clarifications'] if c['id']==cid and c['exception_id']==eid),None)
            if not c:raise KeyError('Clarification not found')
            if req.action=='send':
                if c['status']!='draft':raise ValueError('Only a draft can be sent')
                c.update(status='sent_simulated',sent_at=repo.now(),approved_by=req.actor)
                if req.text:c['text']=req.text
            else:
                if c['status']!='sent_simulated' or not req.text.strip():raise ValueError('Send the approved draft before capturing a nonempty reply')
                c.update(status='replied',reply=req.text,replied_at=repo.now(),extraction=proposal)
    repo.change('clarification_'+req.action,req.actor,mutate)
    return next(c for c in repo.read()['clarifications'] if c['id']==cid)
@app.get('/api/evidence/{eid}')
def evidence(eid:str,version:int|None=None):
    e=repo.read(version)['evidence'].get(eid)
    if not e:raise KeyError('Evidence not found')
    return e
@app.get('/api/evidence/{eid}/source')
def source(eid:str):
    e=repo.read()['evidence'].get(eid)
    if not e or not e.get('source_path'):raise KeyError('Original source unavailable; see buyer or reply evidence')
    return FileResponse(e['source_path'],filename=e.get('file'),content_disposition_type='inline')
@app.get('/demo-files/{filename}')
def fixture(filename:str):
    allowed={x[1] for x in repo.VENDORS.values()}|{'buyer_rfx_reference.xlsx','manifest.json'}
    if filename not in allowed:raise KeyError('Fixture not found')
    return FileResponse(DATA_DIR/filename,content_disposition_type='inline')
@app.get('/api/extraction/{vid}')
def extraction(vid:str):
    v=repo.read()['vendors'].get(vid)
    if not v:raise KeyError('Unknown supplier')
    return v

def run_scenario(spec,question='',interpreter='structured_form'):
    d=repo.read()
    if d['rfx_status']!='approved' or not d['comparison']:raise ValueError('Approve RFx and ingest responses before analysis')
    result=solve_scenario(spec,d)
    result['dataset_version']=d['dataset_version']
    result['open_exceptions']=[{'id':e['id'],'title':e['title']} for e in d['exceptions'] if e['status']!='resolved_by_buyer']
    result['provisional']=bool(result['open_exceptions'])
    if result.get('solver_status')=='limit_or_error':result['status']='solver_limit'
    return repo.save_scenario(result,question,interpreter)
@app.post('/api/scenario')
def scenario(req:ValidatedSpec):return run_scenario(req.model_dump())
@app.post('/api/ask')
def ask(req:Ask):
    spec,mode=interpret_scenario(req.question,list(repo.read()['vendors']))
    return run_scenario(spec,req.question,mode)
@app.get('/api/scenarios')
def scenarios():return repo.scenarios()
@app.get('/api/scenarios/{sid}')
def saved(sid:str):return repo.scenario(sid)
@app.post('/api/scenarios/{sid}/recompute')
def recompute(sid:str):
    s=repo.scenario(sid)
    return run_scenario(s['spec'],s['question'],'recomputed_exact_constraints')
@app.get('/api/scenarios/{sid}/export')
def export(sid:str):
    s=repo.scenario(sid);out=io.StringIO()
    writer=csv.writer(out);writer.writerow(['scenario_id','dataset_version','stale','line','sku','supplier','quantity','landed_inr','extended_inr','evidence_id'])
    for a in s.get('allocation',[]):writer.writerow([sid,s['dataset_version'],s['stale'],a['line_no'],a['sku'],a['vendor_name'],a['qty'],a['landed_unit_cost'],a['total_cost'],a['evidence_id']])
    return Response(out.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="award-{sid}.csv"'})
@app.get('/api/audit')
def audit():return repo.audit()
@app.get('/api/datasets/{version}')
def version(version:int):return repo.read(version)
