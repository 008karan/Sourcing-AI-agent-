"""End-to-end evaluation; truth is read only by this evaluation program.

python evaluate.py --live --prompt-key
python evaluate.py                  # offline, photo explicitly untested
"""
from __future__ import annotations
import argparse
import csv
import getpass
import json
import os
import tempfile
import time
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--prompt-key',action='store_true')
    parser.add_argument('--out',default='evaluation')
    args=parser.parse_args()
    if args.prompt_key:os.environ['GOOGLE_API_KEY']=getpass.getpass('Runtime API secret (hidden): ')
    if not args.live:os.environ.pop('GOOGLE_API_KEY',None)
    if args.live and not os.getenv('GOOGLE_API_KEY'):raise SystemExit('Set GOOGLE_API_KEY or use --prompt-key for live evaluation.')
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app import repository as repo, pipeline
    from backend.app.ai import ai_extract_file, MODEL
    from backend.app.store import DATA_DIR
    from backend.app.scenario import solve_scenario
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    report={'model':MODEL if args.live else None,'mode':'live' if args.live else 'offline','started_at':repo.now(),'checks':[]}
    def check(name,passed,detail=None):
        report['checks'].append({'name':name,'passed':bool(passed),'detail':detail})
        print(('PASS' if passed else 'FAIL')+': '+name,flush=True)
    def post(client,path,body):
        r=client.post(path,json=body)
        if r.status_code!=200:raise RuntimeError(path+': '+r.text[:250])
        return r.json()
    start=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='aerchain-eval-') as tmp:
        os.environ['AERCHAIN_DATA_DIR']=tmp
        with TestClient(app) as client:
            draft=post(client,'/api/rfx/draft',{'prompt':'Prepare the FY27 corrugated packaging event. Retain all 30 supplied line items, mandatory ISO 9001, FSC/PEFC, burst factors and lead-time gates. Compare landed INR prices excluding GST with a 60 day validity. Preserve the baseline questionnaire wording and order.'})
            check('RFx structured draft',bool(draft['draft']['questionnaire']) and len(repo.read()['rfx']['items'])==30,draft['mode'])
            post(client,'/api/workflow',{'action':'start','use_ai':args.live})
            check('RFx approval interrupt',client.get('/api/workflow').json()['interrupts'][0]['type']=='rfx_approval')
            post(client,'/api/workflow',{'action':'resume','approved':True,'actor':'Evaluation buyer'})
            check('Response collection precedes extraction',client.get('/api/workflow').json()['interrupts'][0]['type']=='response_collection' and all(not v['facts'] for v in repo.read()['vendors'].values()))
            post(client,'/api/demo/inbox',{})
            job=post(client,'/api/process',{})
            while job['status']=='running':
                time.sleep(.2)
                job=client.get('/api/jobs/'+job['id']).json()
            if job['status']!='completed':raise RuntimeError(str(job.get('diagnostic',{}))+': '+job.get('error','Processing failed'))
            check('Real processing progress recorded',len(job['events'])>=15)
            d=repo.read()
            check('Five vendor ingestion branches',all(v['response_status']=='processed' for v in d['vendors'].values()))
            check('Human review interrupt',client.get('/api/workflow').json()['interrupts'][0]['type']=='exception_review')
            report['coverage']={vid:{'attempted':len(v['facts']),'method':v['method'],'qualification':v['quality']} for vid,v in d['vendors'].items()}
            check('Native fixture coverage',[len(d['vendors'][v]['facts']) for v in ['packright','corrpro','boxworks','greencarton']]==[30,30,27,30])
            check('Partial quote stays missing',all(d['comparison'][i-1]['vendors']['boxworks']['landed_unit_cost'] is None for i in [7,19,28]))
            check('Prior-year assumptions held for review',all(d['comparison'][i-1]['vendors']['greencarton']['landed_unit_cost'] is None for i in [6,13,21,29]))
            for e in list(d['exceptions']):
                if e['vendor_id']=='greencarton' and e['type']=='review_price':
                    post(client,'/api/exceptions/'+e['id']+'/resolve',{'action':'accept','actor':'Evaluation buyer','reason':'For this test, explicitly confirm the buyer FY26 baseline as the supplier reference.','expected_version':repo.read()['dataset_version']})
            d=repo.read()
            truth=list(csv.DictReader((DATA_DIR/'normalized_truth.csv').open()))
            scores={}
            for vid in repo.VENDORS:
                checked=[];withheld=[];errors=[]
                for t in truth:
                    if t['vendor']!=vid or t['status']!='quoted':continue
                    q=d['comparison'][int(t['line_no'])-1]['vendors'][vid]
                    if q['landed_unit_cost'] is None:
                        withheld.append(int(t['line_no']));continue
                    delta=abs(q['landed_unit_cost']-float(t['landed_unit_cost_inr']));checked.append(delta)
                    if delta>.020001:errors.append({'line':int(t['line_no']),'actual':q['landed_unit_cost'],'truth':float(t['landed_unit_cost_inr']),'error':delta})
                scores[vid]={'compared':len(checked),'within_tolerance':sum(x<=.020001 for x in checked),'mae_inr':sum(checked)/len(checked) if checked else None,'max_error_inr':max(checked) if checked else None,'withheld_lines':withheld,'mismatches':errors}
                check(vid+' normalization',not errors and (len(checked)==29 if vid=='alphapack' and args.live else len(checked)==0 if vid=='alphapack' else len(checked)==(27 if vid=='boxworks' else 30)),scores[vid])
            report['extraction']=scores
            if args.live:
                alpha=d['vendors']['alphapack']
                check('Photo obscured price abstention',d['comparison'][17]['vendors']['alphapack']['landed_unit_cost'] is None)
                check('Mandatory FSC failure detected',alpha['quality']=='fail')
                check('Bundle units extracted',any(f.get('raw_basis')=='bundle' for f in alpha['facts']))
                (out/'alphapack-live-extraction.json').write_text(json.dumps(alpha,indent=2))
                pdf=ai_extract_file(repo.VENDORS['corrpro'][1],pipeline.context(d['rfx']))
                (out/'corrpro-live-extraction.json').write_text(json.dumps(pdf,indent=2))
                rebates=[t for t in pdf['commercial_terms'] if 'rebate' in (t['value']+' '+t['source_text']).lower()]
                check('AI PDF conditional rebate',any('350,000' in t['value'] and '3' in t['value'] for t in rebates))
            questions=[('Cheapest qualified supplier per line',{}),('Qualified only, no supplier above 45% of award spend',{'max_supplier_spend_share':.45}),('Qualified only, no supplier above 55% of award spend',{'max_supplier_spend_share':.55}),('Qualified suppliers with delivery within 14 days',{'max_delivery_days':14}),('Qualified suppliers with delivery within 1 day',{'max_delivery_days':1})]
            results=[]
            for question,expected in questions:
                s=post(client,'/api/ask',{'question':question});results.append(s)
                check('Scenario intent: '+question,all(s['spec'][k]==v for k,v in expected.items()),s['spec'])
                check('Scenario outcome: '+question,s['status']==('infeasible' if expected.get('max_delivery_days')==1 else 'ok'))
                if s['status']=='ok':
                    check('Allocation integrity: '+question,len(s['allocation'])==30 and abs(sum(x['total_cost'] for x in s['allocation'])-s['award_total_inr'])<.01)
                    if expected.get('max_supplier_spend_share'):
                        check('Spend cap: '+question,max(m['spend']/s['award_total_inr'] for m in s['vendor_mix'])<=expected['max_supplier_spend_share']+1e-8)
            report['scenarios']=results
            base=results[0]
            oracle=sum(min(q['landed_unit_cost'] for q in r['vendors'].values() if q['qualification']=='pass' and q['landed_unit_cost'] is not None and not q['blocking_exception'])*r['qty'] for r in d['comparison'])
            check('Independent cheapest-line oracle',abs(base['award_total_inr']-oracle)<.01,oracle)
            eid='boxworks:7:missing_quote'
            c=post(client,'/api/exceptions/'+eid+'/clarification',{'action':'draft'})
            post(client,'/api/exceptions/'+eid+'/clarification',{'action':'send','clarification_id':c['id']})
            reply='L7 BX-5P-480-330-260: INR 24.00 per piece. Pack size 1. Delivery 10 days. Freight remains INR 0.32 per piece extra. This is a simulated supplier clarification for evaluation.'
            post(client,'/api/exceptions/'+eid+'/clarification',{'action':'reply','clarification_id':c['id'],'text':reply})
            post(client,'/api/exceptions/'+eid+'/resolve',{'action':'correct','changes':{'raw_price':24,'raw_currency':'INR','raw_basis':'piece'},'clarification_id':c['id'],'actor':'Evaluation buyer','reason':'Confirmed the simulated supplier reply.','expected_version':repo.read()['dataset_version']})
            check('Clarification changes only reviewed price',repo.read()['comparison'][6]['vendors']['boxworks']['landed_unit_cost']==24.32)
            check('Historical scenario marked stale',repo.scenario(base['id'])['stale'])
            rerun=solve_scenario(base['spec'],repo.read(base['dataset_version']))
            check('Historical award reproducible',rerun['award_total_inr']==base['award_total_inr'])
            check('CSV export includes all lines',len(client.get('/api/scenarios/'+base['id']+'/export').text.splitlines())==31)
    report['elapsed_seconds']=round(time.monotonic()-start,2)
    report['passed']=all(c['passed'] for c in report['checks'])
    report['limitations']=['SMTP and demo replies are simulated; extraction and analysis run at request time.','Qualification checks declarations, not certificate authenticity.','Conditional rebates are surfaced but excluded from optimization.','Whole-line allocation only.','Four prior-year references require explicit buyer approval.','Obscured photo line 18 is correctly withheld; full 147-price recall would be unsafe.','Scenario staleness is conservative: every persisted business change creates a version.','RFx retains baseline line specifications and qualification IDs; proposed questionnaire edits are advisory.']
    (out/'evaluation.json').write_text(json.dumps(report,indent=2))
    lines=['# Aerchain evaluation report','',f"Mode: {report['mode']}; model: {report['model'] or 'none'}; run: {report['started_at']}.",'',f"Checks: {sum(c['passed'] for c in report['checks'])}/{len(report['checks'])} passed. Runtime: {report['elapsed_seconds']} seconds.",'','## Extraction quality','','Rates compared to `demo-data/generated/normalized_truth.csv`, tolerance INR 0.02 per piece. Four buyer-approved prior-year references are included.','','| Supplier | Compared | Within tolerance | Withheld | Maximum error |','|---|---:|---:|---|---:|']
    for vid,s in scores.items():lines.append(f"| {vid} | {s['compared']} | {s['within_tolerance']} | {s['withheld_lines']} | {s['max_error_inr']} |")
    lines+=['','## Scenarios','','| Question | Result | Award INR | Dataset |','|---|---|---:|---:|']
    for s in report['scenarios']:lines.append(f"| {s['question']} | {s['status']} | {s.get('award_total_inr','—')} | {s['dataset_version']} |")
    lines+=['','## Checks','']+[f"- {'PASS' if c['passed'] else 'FAIL'}: {c['name']}" for c in report['checks']]+['','## Limits and interpretation','']+['- '+x for x in report['limitations']]
    (out/'EVALUATION_REPORT.md').write_text('\n'.join(lines)+'\n')
    os.environ.pop('GOOGLE_API_KEY',None)
    print('Evaluation report saved; '+('all checks passed.' if report['passed'] else 'review failed checks.'),flush=True)
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
