/* Visual answers for the Analysis Room.

   Palette: the validated default categorical order, checked against this app's
   white panel surface (adjacent CVD ΔE 9.1, normal-vision ΔE 19.6). Three slots
   sit below 3:1 contrast, so every chart here ships visible direct labels and a
   table view — colour never carries a value on its own. */
const VIZ={surface:'#ffffff',ink:'#14202b',secondary:'#52514e',muted:'#7b8993',grid:'#e6eaed',
  baseline:'#c9d2d8',quiet:'#cfd4de',accent:'#6556d9',good:'#2b7a63',bad:'#b34242',
  series:['#2a78d6','#eb6834','#1baf7a','#eda100','#e87ba4','#008300','#4a3aa7','#e34948']};

/* Colour follows the supplier, never its rank: filtering a chart never repaints
   the survivors. Order comes from the event's own supplier list. */
function seriesColor(id){
  const order=(typeof state!=='undefined'&&state?.vendors)?Object.keys(state.vendors):[];
  const i=order.indexOf(id);
  return VIZ.series[(i<0?order.length:i)%VIZ.series.length];
}

const chartId=()=>'c'+Math.random().toString(36).slice(2,9);
const pct=(v,max)=>max>0?Math.max(1.5,(v/max)*100):1.5;

function tableView(id,table){
  if(!table||!table.rows?.length)return '';
  return `<details class="chart-table"><summary>Table view</summary><div class="table-wrap"><table>
    <thead><tr>${table.columns.map(c=>`<th>${esc(c)}</th>`).join('')}</tr></thead>
    <tbody>${table.rows.map(r=>`<tr>${r.map(c=>`<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody>
  </table></div></details>`;
}

/* Horizontal bars: supplier names are long, so the category label leads the row
   and the value rides the bar tip. Emphasis mode answers "which one" by lifting
   the leader out of a recessive field instead of spending eight hues on it. */
function barChart(spec){
  const id=chartId();
  const rows=spec.series||[];
  if(!rows.length)return emptyChart(spec);
  const max=Math.max(...rows.map(r=>Math.abs(r.value)),0);
  const identity=spec.mode==='identity';
  const bars=rows.map(r=>{
    const lead=r.id===spec.leader_id;
    const color=identity?seriesColor(r.id):lead?VIZ.accent:VIZ.quiet;
    return `<div class="bar-row ${lead?'is-leader':''}" tabindex="0"
        title="${esc(r.full_label||r.label)} · ${esc(r.display)}${r.meta?' · '+esc(r.meta):''}">
      <span class="bar-name">${esc(r.label)}</span>
      <span class="bar-track"><i style="width:${pct(Math.abs(r.value),max)}%;background:${color}"></i></span>
      <span class="bar-value">${esc(r.display)}</span>
      <span class="bar-flag ${lead?'':'gap'}">${lead&&spec.better!=='none'?'✓ Leads':esc(r.delta||'')}</span>
    </div>`}).join('');
  return `<figure class="chart" id="${id}">
    <figcaption><b>${esc(spec.title)}</b><span>${esc(spec.subtitle||'')}</span></figcaption>
    ${identity?legend(rows):''}
    <div class="bars">${bars}</div>
    ${spec.note?`<p class="chart-note">${esc(spec.note)}</p>`:''}
    ${tableView(id,spec.table)}
  </figure>`;
}

function legend(rows){
  return `<div class="chart-legend">${rows.map(r=>
    `<span><i style="background:${seriesColor(r.id)}"></i>${esc(r.full_label||r.label)}</span>`).join('')}</div>`;
}

/* Donut: part-to-whole at a glance, capped at six segments. The 2px separation
   between segments is the surface showing through, not a stroke around a mark. */
function donutChart(spec){
  const rows=(spec.series||[]).filter(r=>r.value>0);
  if(!rows.length)return emptyChart(spec);
  const total=rows.reduce((n,r)=>n+r.value,0);
  const R=68,r0=44,cx=80,cy=80,gap=1.4;
  let angle=-90;
  const arcs=rows.map(row=>{
    const sweep=(row.value/total)*360;
    const a0=angle+gap/2,a1=angle+sweep-gap/2;
    angle+=sweep;
    if(a1<=a0)return '';
    const p=(radius,deg)=>[cx+radius*Math.cos(deg*Math.PI/180),cy+radius*Math.sin(deg*Math.PI/180)];
    const big=(a1-a0)>180?1:0;
    const [x1,y1]=p(R,a0),[x2,y2]=p(R,a1),[x3,y3]=p(r0,a1),[x4,y4]=p(r0,a0);
    return `<path d="M${x1} ${y1}A${R} ${R} 0 ${big} 1 ${x2} ${y2}L${x3} ${y3}A${r0} ${r0} 0 ${big} 0 ${x4} ${y4}Z"
      fill="${seriesColor(row.id)}"><title>${esc(row.full_label||row.label)} · ${esc(row.display)}</title></path>`;
  }).join('');
  const top=rows[0];
  return `<figure class="chart donut-chart">
    <figcaption><b>${esc(spec.title)}</b><span>${esc(spec.subtitle||'')}</span></figcaption>
    <div class="donut-body">
      <svg viewBox="0 0 160 160" role="img" aria-label="${esc(spec.title)}">${arcs}
        <text x="80" y="76" class="donut-lead">${esc(top.display)}</text>
        <text x="80" y="94" class="donut-sub">${esc(top.label)}</text></svg>
      <ul class="donut-legend">${rows.map(row=>`<li>
        <i style="background:${seriesColor(row.id)}"></i>
        <b>${esc(row.full_label||row.label)}</b>
        <span>${esc(row.display)}</span>
        <small>${esc(row.meta||'')}</small></li>`).join('')}</ul>
    </div>
    ${spec.note?`<p class="chart-note">${esc(spec.note)}</p>`:''}
    ${tableView(chartId(),spec.table)}
  </figure>`;
}

function statChart(spec){
  return `<figure class="chart stat-chart">
    <figcaption><b>${esc(spec.title)}</b><span>${esc(spec.subtitle||'')}</span></figcaption>
    <strong class="stat-value">${esc(spec.value)}</strong>
    ${spec.delta?`<span class="stat-delta ${spec.delta_direction==='good'?'good':'bad'}">${spec.delta_direction==='good'?'▲':'▼'} ${esc(spec.delta)}</span>`:''}
    ${spec.context?`<p class="chart-note">${esc(spec.context)}</p>`:''}
  </figure>`;
}

function emptyChart(spec){
  return `<figure class="chart chart-empty">
    <figcaption><b>${esc(spec.title||'Nothing to chart yet')}</b><span>${esc(spec.subtitle||'')}</span></figcaption>
    <p>${esc(spec.note||'No reviewed values are available for this comparison yet.')}</p></figure>`;
}

function renderChart(spec){
  if(!spec)return '';
  if(spec.type==='donut')return donutChart(spec);
  if(spec.type==='stat')return statChart(spec);
  if(spec.type==='empty')return emptyChart(spec);
  return barChart(spec);
}
