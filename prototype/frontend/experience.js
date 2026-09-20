/* Guided experience layered onto the existing comparison and evidence components. */
let currentView='rfx',activeJob=null,jobTimer=null,recorder=null,recordStream=null,recordTarget=null,board=null,answer=null;
const originalGo=go;
go=function(view){currentView=view;document.body.dataset.view=view;originalGo(view)};
document.body.dataset.view='rfx';
const hero=(step,title,description,action='')=>`<div class="section-hero"><div><div class="step-label">${step}</div><h2>${title}</h2><p>${description}</p></div>${action}</div>`;
const next=(text,label,view)=>`<div class="next-step"><span>${text}</span>${button(label,'nextView',`data-to="${view}"`,'primary')}</div>`;
const mic=target=>`<button class="voice-button" data-action="voice" data-target="${target}" aria-label="Record voice request" title="Record a request; it is transcribed for your review">◉ <span>Voice</span></button>`;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const tableLines=()=>`<div class="table-wrap"><table><thead><tr><th>SKU</th><th>Annual quantity</th><th>Specification</th></tr></thead><tbody>${state.rfx.items.map(i=>`<tr><td>${esc(i.sku)}</td><td>${i.annual_quantity.toLocaleString('en-IN')}</td><td>${esc(i.description)}</td></tr>`).join('')}</tbody></table></div>`;

/* One fetch cycle now also carries the scenario board behind Review & Compare. */
refresh=async function(){
  [state,health,history,board]=await Promise.all([api('/api/state'),api('/health'),api('/api/scenarios'),
    api('/api/insights/scenarios').catch(()=>null)]);
  render();
};

/* ───────────────────────── 01 · RFx builder ───────────────────────── */

const STATUS_MARK={captured:'✓',partial:'◐',missing:'○'};
const SEED='We need to buy corrugated packaging for our Bengaluru and Hosur plants for FY27. Roughly 30 SKUs of boxes, dividers, pads, sheets and sleeves, about 2.1 million pieces a year, compared per piece.';

function checklistRail(){
  const list=state.rfx_checklist||[];
  const required=list.filter(x=>x.required);
  const done=required.filter(x=>x.status==='captured').length;
  const optionalDone=list.filter(x=>!x.required&&x.status==='captured').length;
  const optional=list.length-required.length;
  return `<aside class="checklist-rail">
    <div class="checklist-head">
      <h3>RFx readiness checklist</h3>
      <p>The facts any RFx needs before suppliers can quote it — whatever the category.</p>
      <div class="checklist-progress"><i style="width:${Math.round(100*done/Math.max(required.length,1))}%"></i></div>
      <b>${done} of ${required.length} required captured</b>
      <small>${optionalDone} of ${optional} recommended items also covered</small>
    </div>
    <ol class="checklist">${list.map(item=>`<li class="check ${item.status}">
      <button data-action="askItem" data-id="${item.id}" title="Ask me about this">
        <span class="check-mark">${STATUS_MARK[item.status]}</span>
        <span class="check-body">
          <b>${esc(item.label)}${item.required?'':' <em>recommended</em>'}</b>
          ${item.captured_value?`<span class="check-value">${esc(item.captured_value)}</span>`
            :`<span class="check-why">${esc(item.why)}</span>`}
          ${item.status!=='captured'?`<span class="check-ask">${esc(item.follow_up||item.ask)}</span>`:''}
        </span></button></li>`).join('')}</ol>
    ${state.rfx_status!=='approved'?button('Start over','resetChat','','small-button'):''}
  </aside>`;
}

function chatStream(){
  const chat=state.rfx_chat||[];
  if(!chat.length)return `<div class="welcome-card"><div class="welcome-symbol">✦</div>
    <h3>Describe what you need. I will make it quotable.</h3>
    <p>Tell me about the purchase in your own words. I will check it against the RFx checklist on the right,
       ask for whatever is missing, and confirm the whole thing with you before any supplier sees it.</p>
    <div class="suggestions">${button('Use the packaging example ↗','suggestRfx','','suggestion')}${button('View buyer reference','buyerReference','','suggestion')}</div></div>`;
  return chat.map(m=>m.role==='buyer'
    ?`<div class="user-message">${esc(m.text)}</div>`
    :`<div class="assistant-message"><div class="assistant-avatar">a.</div><div class="assistant-content">
        <div class="chat-label">RFx co-pilot</div><p>${esc(m.text)}</p>
        ${(m.questions||[]).length?`<div class="question-chips">${m.questions.map(q=>
          button(esc(q),'answerQuestion',`data-question="${esc(q)}"`,'suggestion')).join('')}</div>`:''}
      </div></div>`).join('');
}

function confirmCard(){
  if(state.rfx_status==='approved'){
    const m=state.supplier_match;
    return `<div class="assistant-message"><div class="assistant-avatar">a.</div><div class="assistant-content">
      <div class="chat-label">RFx co-pilot</div>
      <div class="success-note">✓ Shared with ${m?m.matched.length:'the matched'} suppliers by ${esc(state.approved_by||state.rfx.buyer)}.</div>
      ${m?`<div class="matched-strip">${m.matched.map(x=>`<span class="matched-chip"><i style="background:${seriesColor(x.vendor_id)}"></i>${esc(x.name)} <b>${x.score}</b></span>`).join('')}</div>`:''}
      ${next('Supplier replies land in the response inbox.','Open response inbox','responses')}</div></div>`;
  }
  if(!state.rfx_ready)return '';
  return `<div class="assistant-message"><div class="assistant-avatar">a.</div><div class="assistant-content">
    <div class="chat-label">RFx co-pilot</div>
    <h3>Here is the complete brief.</h3>
    <p>${esc(state.rfx_confirmation||'Confirm this and I will find the right suppliers for it.')}</p>
    <div class="confirm-grid">${(state.rfx_checklist||[]).filter(x=>x.captured_value).map(x=>
      `<div><small>${esc(x.label)}</small><span>${esc(x.captured_value)}</span></div>`).join('')}</div>
    <div class="approval-row"><span>Should I share this with the relevant suppliers?</span>
      ${button('Yes — find &amp; share →','shareRfx','','primary')}
      ${button('Not yet, let me add more','focusComposer')}</div>
    <p class="fine-print">Matching is deterministic and shown to you before anything is released. Delivery is simulated; no external email is sent.</p>
  </div></div>`;
}

renderRfx=function(){
  const released=state.rfx_status==='approved';
  $('#view-rfx').innerHTML=hero('01 / BUILD YOUR RFx','Start with a sentence. Leave with a complete RFx.',
    'Describe the requirement. I will run it against the universal RFx checklist, ask what is missing, then help you share it.')
    +`<div class="builder-layout"><div class="chat-workspace">
        <div class="chat-stream" id="chatStream">${chatStream()}${confirmCard()}</div>
        ${!released?`<div class="composer">
          <textarea id="rfxChat" aria-label="Describe your sourcing requirement" placeholder="Describe what you need to buy, or answer the question above…"></textarea>
          <div class="composer-toolbar">${mic('rfxChat')}<span>Guided intake · buyer approval required before release</span>
          ${button('Send ↑','composeRfx','','primary')}</div></div>`
        :`<div class="composer locked">This RFx is released and frozen for the sourcing event.</div>`}
      </div>${checklistRail()}</div>`;
  const stream=$('#chatStream');
  if(stream)stream.scrollTop=stream.scrollHeight;
};

/* The match runs server-side and deterministically; the overlay narrates it. */
async function playMatch(result){
  const overlay=document.createElement('div');
  overlay.className='match-overlay';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-label','Finding and mapping suppliers');
  overlay.innerHTML=`<div class="match-panel">
    <div class="match-head"><span class="working-orb">✦</span><div><h3>Finding the right suppliers</h3>
      <p>Matching your ${result.requirement_lines} requirement lines and ${result.qualification_gates} qualification gates against the supplier directory.</p></div></div>
    <ol class="match-stages">${result.stages.map(s=>`<li id="stage-${s.id}"><span class="stage-dot"></span>
      <b>${esc(s.label)}</b><small>${esc(s.detail)}</small></li>`).join('')}</ol>
    <div class="match-results" id="matchResults"></div>
    <div class="match-foot" id="matchFoot"></div></div>`;
  document.body.append(overlay);
  await sleep(120);overlay.classList.add('show');
  for(const stage of result.stages){
    const el=overlay.querySelector('#stage-'+stage.id);
    el.classList.add('active');
    if(stage.id==='capability'||stage.id==='mapping'){
      const box=overlay.querySelector('#matchResults');
      const slice=stage.id==='capability'?result.matched.slice(0,Math.ceil(result.matched.length/2)):result.matched.slice(Math.ceil(result.matched.length/2));
      for(const m of slice){
        box.insertAdjacentHTML('beforeend',`<div class="match-card ${m.fit}">
          <div class="match-card-top"><i style="background:${seriesColor(m.vendor_id)}"></i>
            <b>${esc(m.name)}</b><span class="match-score">${m.score}<small>/100</small></span></div>
          <div class="match-bar"><i style="width:${m.score}%;background:${seriesColor(m.vendor_id)}"></i></div>
          <p>${esc(m.reasons[0]||'Registered supplier in this category')}</p>
          <small>${esc(m.region)} · ${m.past_awards} previous award${m.past_awards===1?'':'s'}${m.on_time_pct?' · '+m.on_time_pct+'% on time':''}</small>
        </div>`);
        await sleep(260);
      }
    }else await sleep(850);
    el.classList.remove('active');el.classList.add('done');
  }
  overlay.querySelector('#matchFoot').innerHTML=`<b>✓ RFx shared with ${result.matched.length} of ${result.pool_size} suppliers.</b>
    <span>Each received your ${result.requirement_lines} line items, questionnaire and commercial terms.</span>
    ${button('Continue to responses →','closeMatch','','primary')}`;
  overlay.querySelector('.match-head').innerHTML=`<span class="done-orb">✓</span><div><h3>Shared.</h3>
    <p>The event is open and the response inbox is live.</p></div>`;
  overlay.querySelector('.match-foot').scrollIntoView({behavior:'smooth',block:'nearest'});
  return overlay;
}

/* ───────────────────────── 02 · Responses ───────────────────────── */

const FORMAT_LABEL={xlsx:'Excel workbook',pdf:'PDF proposal',docx:'Word offer',jpg:'Phone photo',jpeg:'Phone photo',png:'Image',eml:'Email reply',txt:'Text message',webp:'Image'};

renderResponses=function(){
  const vs=Object.values(state.vendors),received=vs.filter(v=>v.documents?.length).length,processed=vs.filter(v=>v.response_status==='processed').length;
  const locked=state.rfx_status!=='approved';
  $('#view-responses').innerHTML=hero('02 / COLLECT & UNDERSTAND','Their format. Your clarity.',
    'Load the bundled demo messages, or add your own supplier proposals — name, email, message body and attachments — and extract them the same way.',
    `<div class="hero-actions">${button('Load demo messages','demoMessages',locked?'disabled':'')}${button('+ Add supplier proposal','addSupplier',locked?'disabled':'','primary')}</div>`)
    +`${locked?next('First, build and share your RFx.','Back to RFx builder','rfx'):''}
      <div class="inbox-toolbar"><div><b>${received} of ${vs.length} responses received</b>
        <span>${processed} processed · Excel, PDF, Word, photo, email or anything you paste in</span></div>
        ${button('Extract &amp; normalize →','processAll',(!received||activeJob?.status==='running')?'disabled':'','primary')}</div>
      <div id="processingPanel">${processingHtml()}</div>
      <div class="supplier-grid">${vs.map(v=>{
        const open=state.exceptions.filter(e=>e.vendor_id===v.id&&e.status!=='resolved_by_buyer').length;
        const tint=seriesColor(v.id);
        return `<article class="supplier-card">
          <div class="supplier-top"><div class="supplier-avatar" style="background:${tint}1f;color:${tint}">${esc(v.name.slice(0,1).toUpperCase())}</div>
            ${pill(v.response_status==='processed'?'processed':v.documents?.length?'received':'waiting')}
            ${v.custom?'<span class="pill added">added by you</span>':''}</div>
          <h3>${esc(v.name)}</h3>
          <p class="supplier-format">${esc(FORMAT_LABEL[v.format]||v.format||'Format not yet known')}${v.email?' · '+esc(v.email):''}</p>
          ${v.documents?.length?`<div class="message-preview"><b>${esc(v.subject||'Supplier quote')}</b>
            <p>${esc(v.message?.slice(0,120)||'Supplier attachments received. Ready to read their original response.')}</p>
            <button class="attachment-link" data-action="packet" data-id="${v.id}">▧ ${v.documents.length} source ${v.documents.length===1?'document':'documents'} ↗</button></div>`
            :'<div class="waiting-note">No response yet. Add the supplier’s message to begin.</div>'}
          ${['ai_required','vision_required'].includes(v.method)?`<div class="waiting-note format-note">This format needs the AI extraction key to be read. Native parsing covered the message text only.</div>`:''}
          ${v.response_status==='processed'?`<div class="supplier-facts"><span><b>${v.facts.length}/${state.rfx.items.length}</b> line attempts</span><span>${pill(v.quality)}</span></div>
            <button class="review-link" data-action="vendorReview" data-id="${v.id}">${open?open+' points need attention →':'Review extracted details →'}</button>`:''}
          <div class="supplier-actions">${button(v.documents?.length?'Replace message':'Add response','receiveMessage',`data-id="${v.id}" ${locked?'disabled':''}`)}
            ${v.response_status==='processed'?button('Details','inspect',`data-id="${v.id}"`):''}
            ${v.custom?button('Remove','removeSupplier',`data-id="${v.id}"`,'link-button'):''}</div>
        </article>`}).join('')}</div>
      ${processed?next('Responses are ready. Review uncertainty before choosing an award.','Review &amp; compare →','compare'):''}`;
};

function processingHtml(){
  if(!activeJob)return '';
  const j=activeJob;
  return `<div class="processing-card"><div class="processing-title">
    <span class="${j.status==='running'?'working-orb':'done-orb'}">${j.status==='running'?'✦':'✓'}</span>
    <div><h3>${j.status==='running'?'Reading the supplier responses…':j.status==='completed'?'Your comparison is ready.':'Processing needs attention'}</h3>
    <p>${j.status==='running'?'Live progress from source parsing, extraction and normalization.':esc(j.error||'Prices, qualification and source references have been saved.')}</p></div></div>
    <div class="processing-vendors">${Object.values(state.vendors).map(v=>{const p=j.vendors[v.id];
      return `<div><span>${esc(v.name.split(' ')[0])}</span><b>${esc(p?.stage||'Queued')}</b><small>${esc(p?.message||'Waiting to start')}</small></div>`}).join('')}</div></div>`;
}

async function pollJob(){
  if(!activeJob)return;
  try{
    activeJob=await api('/api/jobs/'+activeJob.id);
    const panel=$('#processingPanel');if(panel)panel.innerHTML=processingHtml();
    if(activeJob.status==='running'){jobTimer=setTimeout(pollJob,900)}
    else{sessionStorage.removeItem('aerchain-job');await refresh();
      if(activeJob.status==='completed')toast('Extraction complete. Review the source-backed comparison.');else toast(activeJob.error,true)}
  }catch(e){toast(e.message,true);jobTimer=setTimeout(pollJob,2500)}
}

function addSupplierForm(){
  openDrawer(`<div class="eyebrow">ADD A SUPPLIER PROPOSAL</div>
    <h2>Test this with your own supplier response</h2>
    <p>Add the supplier, paste their email body and attach whatever they actually sent. Extraction runs the same
       pipeline the demo messages use — nothing is read until you ask for it.</p>
    <form id="addSupplierForm">
      <label class="field">Supplier name <input name="name" required maxlength="120" placeholder="e.g. Sunrise Packaging Pvt Ltd"></label>
      <label class="field">Email ID <input name="email" type="email" maxlength="200" placeholder="quotes@supplier.example"></label>
      <label class="field">Email subject <input name="subject" maxlength="200" value="${esc(state.rfx.title)} — supplier offer"></label>
      <label class="field">Message body <textarea name="body" rows="8" placeholder="Paste the supplier’s email exactly as it arrived — rates, units, freight, lead time, certifications…"></textarea></label>
      <label class="drop-zone">Attachments
        <input name="files" type="file" multiple accept=".xlsx,.docx,.pdf,.eml,.txt,.jpg,.jpeg,.png,.webp">
        <span>Excel, PDF, Word, photo, email or text · up to 12 MB each, five files</span></label>
      <p class="fine-print">Give at least a message body or one attachment.</p>
      <div class="actions">
        <button type="submit" class="primary" name="intent" value="extract">Add &amp; extract information →</button>
        <button type="submit" class="secondary" name="intent" value="add">Add supplier only</button>
      </div>
    </form>`);
}

function receiveForm(id){
  const v=state.vendors[id];
  openDrawer(`<div class="eyebrow">SUPPLIER RESPONSE</div><h2>${esc(v.name)}</h2>
    <p>Paste the message and attach the original quote. Nothing is extracted until you ask for it.</p>
    <form id="receiveForm" data-id="${id}">
      <label class="field">Email ID <input name="sender_email" type="email" maxlength="200" value="${esc(v.email||'')}"></label>
      <label class="field">Email subject <input name="subject" value="${esc(v.subject||state.rfx.title+' — supplier offer')}" required></label>
      <label class="field">Email body <textarea name="body" placeholder="Dear Priya, please find our quotation attached…" rows="6"></textarea></label>
      <label class="drop-zone">Attach quote files<input name="files" type="file" multiple accept=".xlsx,.docx,.pdf,.eml,.txt,.jpg,.jpeg,.png,.webp">
        <span>Excel, PDF, Word, photo or email · up to 12 MB each</span></label>
      <button type="submit" class="primary">Receive this response</button></form>`);
}

function packet(id){
  const v=state.vendors[id];
  openDrawer(`<div class="eyebrow">SUPPLIER MESSAGE</div><h2>${esc(v.name)}</h2>
    ${v.email?`<p>${esc(v.email)}</p>`:''}<h3>${esc(v.subject||'Supplier response')}</h3>
    <pre class="email-body">${esc(v.message||'See the attached supplier document below.')}</pre>
    ${(v.documents||[]).map((d,i)=>{const ext=d.filename.split('.').pop().toLowerCase();
      return `<div class="source-card"><b>${esc(d.filename)}</b>
        ${['jpg','jpeg','png','webp'].includes(ext)?`<img class="source-preview" src="/api/responses/${id}/documents/${i}" alt="Supplier attachment">`
          :ext==='pdf'?`<iframe class="document-frame" title="Supplier PDF" src="/api/responses/${id}/documents/${i}"></iframe>`:''}
        <a class="filelink" href="/api/responses/${id}/documents/${i}" target="_blank" rel="noopener">Open original file ↗</a></div>`}).join('')}`);
}

/* ───────────────────────── 03 · Review & compare ───────────────────────── */

function scenarioBoard(){
  if(!board||!board.rows.length||!board.suppliers.length)
    return `<div class="panel"><div class="panel-head"><div><h2>Scenario-wise supplier standings</h2>
      <p>Appears once supplier responses are processed.</p></div></div>
      <div class="empty">Process the supplier responses to rank them scenario by scenario.</div></div>`;
  const sup=board.suppliers;
  const cell=(row,c)=>{
    const lead=(row.leader_ids||[]).includes(c.vendor_id),runner=(row.runner_up_ids||[]).includes(c.vendor_id);
    const cls=c.value==null?'na':lead?'lead':c.blocked?'blocked':runner?'runner':'';
    return `<td class="board-cell ${cls}"><b>${esc(c.display)}</b>
      ${lead?'<span class="cell-tag lead-tag">✓ Leads</span>':runner?'<span class="cell-tag">2nd</span>'
        :c.blocked?'<span class="cell-tag block-tag">⚠ Not qualified</span>':''}</td>`;
  };
  return `<div class="panel board-panel"><div class="panel-head">
      <div><h2>Scenario-wise supplier standings</h2>
      <p>One row per buying priority. The supplier leading each row is highlighted — read down the column to see who fits your priorities.</p></div>
      <div class="board-key"><span><i class="k-lead"></i>Leads this row</span><span><i class="k-runner"></i>Runner-up</span>
        <span><i class="k-block"></i>Blocked by qualification</span><span><i class="k-na"></i>No reviewed value</span></div></div>
    <div class="table-wrap"><table class="board-table">
      <thead><tr><th class="board-scenario">If you optimise for…</th>
        ${sup.map(s=>`<th><span class="board-supplier"><i style="background:${seriesColor(s.vendor_id)}"></i>${esc(s.short_name)}</span>
          ${pill(s.qualification)}</th>`).join('')}</tr></thead>
      <tbody>${board.rows.map(row=>`<tr>
        <th class="board-scenario"><b>${esc(row.label)}</b><span>${esc(row.meaning)}</span><small>${esc(row.unit)}</small></th>
        ${sup.map(s=>cell(row,row.cells.find(c=>c.vendor_id===s.vendor_id)||{vendor_id:s.vendor_id,value:null,display:'—'})).join('')}</tr>`).join('')}
        <tr class="board-total"><th class="board-scenario"><b>Scenarios led</b><span>How often this supplier comes first</span></th>
        ${sup.map(s=>`<td class="board-cell ${s.wins?'wins':''}"><b>${s.wins}</b><span class="cell-tag">of ${board.scenario_count}</span></td>`).join('')}</tr>
      </tbody></table></div>
    <p class="chart-note">Leaders are computed from reviewed source data only. A supplier with no usable price for a factor is shown as “Not available”, never as zero.</p></div>`;
}

const originalRenderCompare=renderCompare;
renderCompare=function(){
  originalRenderCompare();
  $('#view-compare').insertAdjacentHTML('afterbegin',
    hero('03 / REVIEW WITH CONFIDENCE','Know who leads, and why.',
      'Start with the scenario standings, then open the line-by-line normalized view. Click any price for its source and calculation.',
      button('Analyze this event →','nextView','data-to="analysis"','primary'))+scenarioBoard());
};

/* ───────────────────────── 04 · Analysis room ───────────────────────── */

const SUGGESTIONS=[
  ['Cheapest qualified supplier per line','Lowest-cost qualified award'],
  ['Qualified only, no supplier above 45% of award spend','Balance cost against concentration risk'],
  ['Compare the average landed cost of each supplier','Chart the price comparison'],
  ['Show me previous deals with each supplier','Chart the relationship history'],
  ['Which supplier has the best on-time delivery record?','Chart delivery performance'],
  ['Qualified suppliers with delivery within 1 day','Test an infeasible constraint'],
];

const awardCharts=s=>{
  if(!s||s.status!=='ok')return [];
  const money2=v=>v==null?'—':Math.abs(v)>=1e7?`₹${(v/1e7).toFixed(2)} Cr`:Math.abs(v)>=1e5?`₹${(v/1e5).toFixed(2)} L`:`₹${Math.round(v).toLocaleString('en-IN')}`;
  const mix=s.vendor_mix||[];
  // The scenario KPI row already carries the headline numbers, so the charts
  // answer the two questions it cannot: how the award splits, and who won what.
  return [
    {type:'donut',title:'Share of award spend',subtitle:`${mix.length} supplier${mix.length===1?'':'s'} · ${(s.allocation||[]).length} lines allocated`,
     better:'none',leader_id:mix[0]?.vendor_id,note:'Whole line items only; no line is split between suppliers.',
     series:mix.map(m=>({id:m.vendor_id,label:m.vendor_name.split(' ')[0],full_label:m.vendor_name,
       value:+(m.share*100).toFixed(2),display:(m.share*100).toFixed(1)+'%',meta:`${m.lines} lines · ${money2(m.spend)}`})),
     table:{columns:['Supplier','Share of award','Lines','Award spend'],
       rows:mix.map(m=>[m.vendor_name,(m.share*100).toFixed(1)+'%',String(m.lines),money2(m.spend)])}},
    {type:'bar',mode:'identity',title:'Lines won by supplier',subtitle:'requirement lines · higher is better',better:'higher',
     leader_id:[...mix].sort((a,b)=>b.lines-a.lines)[0]?.vendor_id,
     series:[...mix].sort((a,b)=>b.lines-a.lines).map(m=>({id:m.vendor_id,label:m.vendor_name.split(' ')[0],
       full_label:m.vendor_name,value:m.lines,display:String(m.lines),meta:money2(m.spend)})),
     table:{columns:['Supplier','Lines won'],rows:[...mix].sort((a,b)=>b.lines-a.lines).map(m=>[m.vendor_name,String(m.lines)])}},
  ];
};

renderAnalysis=function(){
  const question=$('#question')?.value||'';
  $('#view-analysis').innerHTML=hero('04 / FIND YOUR AWARD','Ask the next “what if”.',
    'Ask for an award scenario or a comparison on any factor. Answers come back as a chart wherever a chart reads faster than a sentence.')
    +`<div class="analysis-layout"><div class="analysis-conversation">
      <div id="scenarioResult" class="scenario-result ${selected||answer?'show':''}">
        ${!selected&&!answer?`<div class="welcome-card analysis-welcome"><div class="welcome-symbol">✦</div>
          <h3>What would you like to understand?</h3><p>Ask for an award, or for a comparison on price, delivery, compliance or past deals.</p>
          <div class="scenario-suggestions">${SUGGESTIONS.map(([q,label])=>
            button(label+' ↗','askSuggestion',`data-question="${esc(q)}"`,'suggestion')).join('')}</div></div>`:''}
      </div>
      <div class="composer analyst-composer">
        <textarea id="question" aria-label="Analysis question" placeholder="Ask for an award scenario, or a chart of any factor…">${esc(question)}</textarea>
        <div class="composer-toolbar">${mic('question')}<span>Charts and awards are calculated from your reviewed data</span>
        ${button('Analyze ↑','askNew','','primary')}</div></div></div>
      <aside class="scenario-sidebar"><h3>Scenario history</h3><p>Saved with their source-data version.</p>
        ${history.map(s=>`<button class="scenario-history-item ${selected===s.id?'selected':''}" data-action="scenario" data-id="${s.id}">
          <span>${esc(s.question||'Structured scenario')}</span>
          <b>${s.award_total_inr!=null?cr(s.award_total_inr):'No feasible award'}</b>
          <small>v${s.dataset_version} · ${s.stale?'Needs recomputing':'Current'}</small></button>
          ${s.stale?button('Recompute','recompute',`data-id="${s.id}"`,'small-button'):''}`).join('')||'<div class="empty-history">Your first question will appear here.</div>'}
      </aside></div>`;
  if(answer)renderAnswer(answer);
  else if(selected){const s=history.find(x=>x.id===selected);if(s)renderScenario(s)}
  else $('#scenarioResult').classList.add('show');
};

function renderAnswer(result){
  const box=$('#scenarioResult');
  if(!box)return;
  box.classList.add('show');
  if(result.mode==='scenario'){
    selected=result.scenario.id;answer=null;
    renderScenario(result.scenario);
    return;
  }
  box.innerHTML=`<div class="user-message">${esc(result.question)}</div>
    <div class="assistant-message"><div class="assistant-avatar">a.</div><div class="assistant-content">
      <div class="chat-label">✦ Decision analyst · source data v${state.dataset_version}</div>
      ${result.narrative?`<p class="answer-lead">${esc(result.narrative)}</p>`:''}
      <div class="chart-stack">${(result.charts||[]).map(renderChart).join('')||'<p>No chartable data for that question yet.</p>'}</div>
    </div></div>`;
}

const originalRenderScenario=renderScenario;
renderScenario=function(s){
  answer=null;
  originalRenderScenario(s);
  const box=$('#scenarioResult');
  box.insertAdjacentHTML('afterbegin',`<div class="user-message">${esc(s.question||'Run an award scenario')}</div>`);
  if(s.status==='ok'){
    const panelEl=box.querySelector('.panel');
    panelEl.insertAdjacentHTML('afterbegin',`<div class="chat-label">✦ Decision analyst · source data v${s.dataset_version}</div>`);
    const kpis=panelEl.querySelector('.scenario-kpis');
    if(kpis)kpis.insertAdjacentHTML('afterend',`<div class="chart-stack">${awardCharts(s).map(renderChart).join('')}</div>`);
    const tableWrap=panelEl.querySelector('.table-wrap');
    if(tableWrap){
      const details=document.createElement('details');
      details.className='allocation-details';
      details.innerHTML=`<summary>Line-by-line allocation (${(s.allocation||[]).length} lines)</summary>`;
      tableWrap.replaceWith(details);details.append(tableWrap);
    }
  }
  $$('.scenario-history-item').forEach(el=>el.classList.toggle('selected',el.dataset.id===s.id));
};

const originalShowEvidence=showEvidence;
showEvidence=async function(id,version){
  await originalShowEvidence(id,version);
  const e=await api('/api/evidence/'+id+(version?'?version='+version:''));
  if(e.source_path)$('#drawerBody').insertAdjacentHTML('beforeend',`<div class="inline-source"><h3>Original document</h3>
    ${e.type==='pdf'?`<iframe title="Original PDF source" src="/api/evidence/${id}/source#page=${e.page||1}"></iframe>`
      :['jpg','jpeg','png','webp'].includes(e.type)?''
      :'<p>Native source excerpt is shown above with its location. Download the original to inspect the full workbook or document.</p>'}</div>`);
};

async function recordVoice(target,b){
  if(recorder?.state==='recording'){recorder.stop();b.textContent='Transcribing…';return}
  if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder)throw Error('Voice recording is unavailable in this browser. Use text, or open the app in Chrome.');
  recordStream=await navigator.mediaDevices.getUserMedia({audio:true});recordTarget=target;
  const mimeType=MediaRecorder.isTypeSupported('audio/webm')?'audio/webm':'audio/mp4';
  recorder=new MediaRecorder(recordStream,{mimeType});const chunks=[];
  recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
  recorder.onstop=async()=>{recordStream.getTracks().forEach(t=>t.stop());
    try{const f=new FormData();f.append('file',new Blob(chunks,{type:mimeType}),'request.'+(mimeType==='audio/webm'?'webm':'mp4'));
      const r=await fetch('/api/transcribe',{method:'POST',body:f});const result=await r.json();
      if(!r.ok)throw Error(result.detail);$('#'+recordTarget).value=result.text;
      toast('Transcript ready. Review it, then send your request.')}
    catch(e){toast(e.message,true)}finally{b.innerHTML='◉ <span>Voice</span>';recorder=null}};
  recorder.start();b.textContent='■ Stop recording';toast('Recording your request. Click Stop when finished.');
  setTimeout(()=>{if(recorder?.state==='recording')recorder.stop()},60000);
}

const EXPERIENCE_ACTIONS=['nextView','suggestRfx','buyerReference','composeRfx','shareRfx','closeMatch','resetChat','askItem',
  'answerQuestion','focusComposer','demoMessages','processAll','receiveMessage','addSupplier','removeSupplier','packet',
  'vendorReview','askNew','askSuggestion','voice'];

document.addEventListener('click',async e=>{
  const b=e.target.closest('[data-action]');
  if(!b)return;
  const a=b.dataset.action;
  if(!EXPERIENCE_ACTIONS.includes(a))return;
  if(a==='voice'){try{await recordVoice(b.dataset.target,b)}catch(err){toast(err.message,true)}return}
  await busy(b,async()=>{
    if(a==='nextView')return go(b.dataset.to);
    if(a==='closeMatch'){document.querySelector('.match-overlay')?.remove();return go('responses')}
    if(a==='suggestRfx'){const el=$('#rfxChat');el.value=SEED;el.focus();return}
    if(a==='focusComposer'){$('#rfxChat')?.focus();return}
    if(a==='askItem'){const item=(state.rfx_checklist||[]).find(x=>x.id===b.dataset.id);
      const el=$('#rfxChat');if(!el||!item)return;
      el.placeholder='Answer: '+item.ask;el.focus();
      toast(item.status==='captured'?'Already captured — '+(item.captured_value||item.label):item.ask);return}
    if(a==='answerQuestion'){const el=$('#rfxChat');
      el.placeholder='Answer: '+b.dataset.question;el.focus();
      el.scrollIntoView({behavior:'smooth',block:'nearest'});return}
    if(a==='buyerReference')return openDrawer(`<h2>Buyer requirement baseline</h2>
      <p>${state.rfx.items.length} line items · baseline annual spend ${cr(state.rfx.expected_annual_spend_inr)}. Imported from the handoff buyer reference.</p>
      ${tableLines()}<a class="filelink" href="/demo-files/buyer_rfx_reference.xlsx">Download original buyer workbook</a>`);
    if(a==='composeRfx'){
      const el=$('#rfxChat');const message=el.value.trim();
      if(!message)throw Error('Describe your requirement, or answer the question above, first.');
      el.value='';
      await api('/api/rfx/chat',{message});
      await refresh();return}
    if(a==='resetChat'){await api('/api/rfx/chat/reset',{});await refresh();toast('Intake restarted.');return}
    if(a==='shareRfx'){
      const result=await api('/api/rfx/share',{action:'resume',actor:state.rfx.buyer});
      const overlay=await playMatch(result);
      await refresh();
      if(!document.body.contains(overlay))go('responses');
      return}
    if(a==='demoMessages'){await api('/api/demo/inbox',{});await refresh();
      toast('Demo supplier messages received. Click Extract & normalize to process them.');return}
    if(a==='addSupplier')return addSupplierForm();
    if(a==='removeSupplier'){await api('/api/suppliers/'+encodeURIComponent(b.dataset.id),null,'DELETE');
      await refresh();toast('Supplier removed from this event.');return}
    if(a==='receiveMessage')return receiveForm(b.dataset.id);
    if(a==='packet')return packet(b.dataset.id);
    if(a==='vendorReview'){go('compare');
      const review=state.exceptions.find(e=>e.vendor_id===b.dataset.id&&e.status!=='resolved_by_buyer');
      return review?showReview(review.id):showInspect(b.dataset.id)}
    if(a==='processAll'){activeJob=await api('/api/process',{});sessionStorage.setItem('aerchain-job',activeJob.id);
      renderResponses();pollJob();return}
    if(a==='askSuggestion')$('#question').value=b.dataset.question;
    if(a==='askNew'||a==='askSuggestion'){
      const question=$('#question').value;
      if(!question.trim())throw Error('Enter a question first.');
      const box=$('#scenarioResult');box.classList.add('show');
      box.innerHTML=`<div class="user-message">${esc(question)}</div><div class="thinking-panel"><span class="working-orb">✦</span>
        <div><h3>Working through your question…</h3><p>Choosing the clearest form, then calculating it from your reviewed data.</p></div></div>`;
      const result=await api('/api/analyze',{question});
      if(result.mode==='scenario'){selected=result.scenario.id;answer=null}else{answer=result;selected=null}
      await refresh();}
  })});

document.addEventListener('submit',async e=>{
  const form=e.target;
  if(form.id==='receiveForm'){
    e.preventDefault();
    await busy(form.querySelector('[type=submit]'),async()=>{
      const data=new FormData(form);
      if(!form.querySelector('[type=file]').files.length)data.delete('files');
      const r=await fetch('/api/responses/'+form.dataset.id+'/receive',{method:'POST',body:data});
      const d=await r.json();
      if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'Check the message and attachments.');
      closeDrawer();await refresh();toast('Response received. Start extraction when you are ready.')});
    return;
  }
  if(form.id!=='addSupplierForm')return;
  e.preventDefault();
  const intent=e.submitter?.value||'extract';
  await busy(e.submitter,async()=>{
    const data=new FormData(form);
    const name=(data.get('name')||'').trim();
    const files=form.querySelector('[type=file]').files;
    if(!name)throw Error('Give the supplier a name.');
    if(!(data.get('body')||'').trim()&&!files.length)throw Error('Add a message body or at least one attachment.');
    const created=await api('/api/suppliers',{name,email:(data.get('email')||'').trim()});
    const vid=created.vendor.id;
    const packet=new FormData();
    packet.append('body',data.get('body')||'');
    packet.append('subject',data.get('subject')||'Supplier response');
    packet.append('sender_email',data.get('email')||'');
    for(const file of files)packet.append('files',file);
    const r=await fetch('/api/responses/'+vid+'/receive',{method:'POST',body:packet});
    const d=await r.json();
    if(!r.ok){await api('/api/suppliers/'+vid,null,'DELETE').catch(()=>{});
      throw Error(typeof d.detail==='string'?d.detail:'Check the message and attachments.')}
    closeDrawer();
    if(intent==='extract'&&activeJob?.status!=='running'){
      await refresh();
      activeJob=await api('/api/process',{});
      sessionStorage.setItem('aerchain-job',activeJob.id);
      renderResponses();pollJob();
      toast(`${name} added. Extracting their response now.`);
    }else{await refresh();toast(`${name} added. Use Extract & normalize when your suppliers are all in.`)}
  })});

refresh().catch(e=>toast(e.message,true));

const pendingJob=sessionStorage.getItem('aerchain-job');
if(pendingJob)api('/api/jobs/'+pendingJob).then(j=>{activeJob=j;if(state)renderResponses();pollJob()})
  .catch(()=>sessionStorage.removeItem('aerchain-job'));
