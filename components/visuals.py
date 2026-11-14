"""
visuals.py — self-contained interactive visuals.

Each function here takes the plain dict produced by
:mod:`algorithms.visual_data` and returns one complete HTML document — inline
SVG, inline CSS and vanilla JavaScript, with no external scripts, fonts or
images.  The document is meant to be rendered with
``st.components.v1.html``.

Division of labour:

  * Python decides every number, label and set membership (see
    ``algorithms/visual_data.py``);
  * JavaScript only draws what it is handed, animates it and handles
    hover, click and keyboard input.

All user text arrives already escaped (``label``), and every value is written
into the DOM with ``textContent`` or ``innerHTML`` using that escaped label.
"""

from __future__ import annotations

import json


# ===========================================================================
# Shared document shell
# ===========================================================================

_BASE_CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:transparent;color:#1F2937;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  font-size:14px;-webkit-text-size-adjust:100%;max-width:100%;overflow-x:hidden}
.wrap{padding:2px 2px 4px;max-width:100%;overflow-x:hidden}
svg{display:block;width:100%;height:auto}
.toolbar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 8px}
button{cursor:pointer;border:1px solid #16A34A;background:#fff;color:#14532D;
  border-radius:999px;padding:4px 12px;font-size:12.5px;font-weight:600;
  transition:background .15s ease}
button:hover{background:#F0FDF4}
button:focus-visible{outline:3px solid rgba(22,163,74,.45);outline-offset:2px}
button[aria-pressed="true"]{background:#16A34A;color:#fff}
button:disabled{opacity:.45;cursor:not-allowed}
input[type=range]{accent-color:#16A34A;max-width:100%}
input[type=text]{border:1px solid #E5E7EB;border-radius:8px;padding:4px 8px;font-size:13px}
.panel{border:1px solid #E5E7EB;border-radius:12px;background:#fff;
  padding:6px 10px;margin-top:6px;min-height:36px}
.panel h4{margin:0 0 4px;font-size:13px;color:#14532D}
.panel p{margin:2px 0;font-size:12.5px;color:#6B7280}
.panel .row{margin:3px 0;font-size:12.5px}
.chip{display:inline-block;border-radius:999px;padding:2px 9px;font-size:11.5px;
  font-weight:600;margin:2px 4px 2px 0;border:1px solid transparent;white-space:nowrap}
.chip.ok{background:#DCFCE7;color:#15803D}
.chip.no{background:#FEE2E2;color:#DC2626}
.chip.grey{background:#F3F4F6;color:#6B7280}
.chip.amber{background:#FEF3C7;color:#B45309}
.badge{display:inline-flex;align-items:center;gap:5px;border-radius:999px;
  padding:3px 10px;font-size:11.5px;font-weight:700;border:1px solid;
  margin:0 6px 6px 0;background:#fff}
.badge.ok{border-color:#86EFAC;color:#15803D}
.badge.no{border-color:#FECACA;color:#B91C1C}
.badge button{border:none;background:none;padding:0;font:inherit;color:inherit}
.title{font-size:13px;font-weight:700;color:#14532D;margin:0 0 6px}
.sub{font-size:12px;color:#6B7280;margin:0 0 8px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.three{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
table.tt{border-collapse:collapse;font-size:12.5px;width:100%}
table.tt th,table.tt td{border:1px solid #E5E7EB;padding:3px 6px;text-align:center}
table.tt th{background:#F0FDF4;color:#14532D;font-weight:600}
table.tt tr.sel td{background:#FEF3C7!important;outline:2px solid #F59E0B;outline-offset:-1px}
.tile{cursor:pointer;position:relative;border-radius:12px;border:1px solid #E5E7EB;
  background:#fff;display:flex;flex-direction:column;justify-content:space-between;
  padding:8px;transition:box-shadow .15s ease,transform .15s ease}
.tile:hover{box-shadow:0 4px 14px rgba(16,24,40,.12)}
.tile.ok{background:linear-gradient(180deg,#F0FDF4 0%,#DCFCE7 100%);border-color:#86EFAC}
.tile.no{background:#F9FAFB;border-color:#E5E7EB}
.tile b{font-size:12.5px;color:#14532D;display:block;line-height:1.2}
.bar{height:7px;border-radius:999px;background:#E5E7EB;overflow:hidden;margin-top:5px}
.bar>span{display:block;height:100%;background:#F59E0B;border-radius:999px}
.small{font-size:11px;color:#6B7280}
.empty{border:1px dashed #D1D5DB;border-radius:12px;padding:18px;text-align:center;
  color:#6B7280;font-size:13px;background:#fff}
@media (max-width:540px){
  .two{grid-template-columns:1fr!important}
  .three{grid-template-columns:1fr!important}
  .hide-sm{display:none!important}
  button{padding:5px 11px}
}
@media (prefers-reduced-motion: reduce){
  *{transition:none!important;animation:none!important}
}
"""

_BASE_JS = """
const NS='http://www.w3.org/2000/svg';
const REDUCED=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function E(tag,attrs,html){const e=document.createElement(tag);
  for(const k in (attrs||{}))e.setAttribute(k,attrs[k]);
  if(html!=null)e.innerHTML=html;return e;}
function S(tag,attrs,text){const e=document.createElementNS(NS,tag);
  for(const k in (attrs||{}))e.setAttribute(k,attrs[k]);
  if(text!=null)e.textContent=String(text);return e;}
function MS(ms){return REDUCED?0:ms;}
function clear(node){while(node.firstChild)node.removeChild(node.firstChild);}
function fitFrame(){
  const frame=window.frameElement, wrap=document.querySelector('.wrap');
  if(!frame||!wrap)return;
  const height=Math.ceil(wrap.getBoundingClientRect().height);
  if(height>0&&Math.abs(frame.getBoundingClientRect().height-height)>1)
    frame.style.height=height+'px';
  const container=frame.parentElement;
  if(height>0&&container){
    container.style.height=height+'px';
    container.style.flexBasis=height+'px';
  }
}
const visualWrap=document.querySelector('.wrap');
if(visualWrap){
  if(window.ResizeObserver)new ResizeObserver(fitFrame).observe(visualWrap);
  window.addEventListener('resize',fitFrame);
  window.addEventListener('load',fitFrame,{once:true});
  requestAnimationFrame(fitFrame);
}
"""


def _json(obj) -> str:
    """Serialise *obj* so it can never close the surrounding script element."""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def _doc(body_html: str, script: str, css: str = "") -> str:
    """Wrap *body_html* and *script* in one self-contained document."""
    return (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<style>{_BASE_CSS}{css}</style></head><body>"
        f"<div class=\"wrap\">{body_html}</div>"
        f"<script>{_BASE_JS}\n{script}</script></body></html>"
    )


_EMPTY = (
    '<div class="empty"><b>No buildings yet.</b><br>'
    'Add at least one building on the Campus Data page to see this view.</div>'
)


# ===========================================================================
# 1 — Campus map
# ===========================================================================

def campus_map(data: dict) -> str:
    """Tiles for the six buildings: size by area, sun for solar, demand bar."""
    if not data.get("buildings"):
        return _doc(_EMPTY, "")

    body = (
        '<p class="sub">Tile size follows rooftop area. A glowing green tile is '
        'ready for panels; a grey tile shows the criterion it misses. Click or '
        'press Enter on a tile for the full breakdown.</p>'
        '<div id="map" class="grid" style="display:flex;flex-wrap:wrap;gap:10px;'
        'align-items:flex-start"></div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
    )
    script = f"""
const D={_json(data)};
const map=document.getElementById('map'), panel=document.getElementById('panel');
function sun(size, active){{
  const svg=S('svg',{{viewBox:'0 0 24 24',width:size,height:size,
    'aria-hidden':'true',style:'flex:0 0 auto'}});
  const col=active?'#F59E0B':'#9CA3AF';
  svg.appendChild(S('circle',{{cx:12,cy:12,r:4.4,fill:col}}));
  for(let i=0;i<8;i++){{
    const a=i*Math.PI/4;
    svg.appendChild(S('line',{{x1:12+6.2*Math.cos(a),y1:12+6.2*Math.sin(a),
      x2:12+8.8*Math.cos(a),y2:12+8.8*Math.sin(a),
      stroke:col,'stroke-width':1.7,'stroke-linecap':'round'}}));
  }}
  return svg;
}}
function show(b){{
  const checks=D.buildings.find(x=>x.key===b.key).criteria;
  const names={{A:'demand',B:'area',C:'solar'}};
  let rows='';
  for(const k of ['A','B','C']){{
    rows+='<div class="row"><span class="chip '+(checks[k]?'ok':'no')+'">'
      +(checks[k]?'passes':'fails')+'</span> '+names[k]+'</div>';
  }}
  panel.innerHTML='<h4>'+b.label+'</h4>'
    +'<p>Demand '+b.demand+' kWh/day &nbsp;·&nbsp; rooftop '+b.area+' m²'
    +' &nbsp;·&nbsp; solar '+b.solar+'%</p>'+rows
    +'<p>'+(b.eligible?'Eligible — meets all three criteria.'
      :'Not eligible — '+b.failed_text+' below the threshold.')+'</p>';
}}
D.buildings.forEach(b=>{{
  const t=E('div',{{class:'tile '+(b.eligible?'ok':'no'),tabindex:'0',role:'button',
    'aria-label':b.label,'data-key':b.key,
    style:'width:'+b.tile+'px;min-height:'+b.tile+'px'}});
  const top=E('div',{{}});
  top.appendChild(E('b',{{}},b.label));
  const meta=E('div',{{class:'small',style:'margin:4px 0 2px'}},
    b.area+' m² · '+b.solar+'%');
  top.appendChild(meta);
  const bar=E('div',{{class:'bar','aria-hidden':'true'}});
  bar.appendChild(E('span',{{style:'width:'+Math.round(100*b.demand/D.max_demand)+'%'}}));
  top.appendChild(bar);
  t.appendChild(top);
  const foot=E('div',{{style:'display:flex;align-items:center;gap:6px;margin-top:6px'}});
  foot.appendChild(sun(18,b.solar>=D.thresholds.min_solar));
  foot.appendChild(E('span',{{class:'chip '+(b.eligible?'ok':'grey')}},
    b.eligible?'panel ready':b.failed_text));
  t.appendChild(foot);
  t.addEventListener('mouseenter',()=>show(b));
  t.addEventListener('focus',()=>show(b));
  t.addEventListener('click',()=>show(b));
  t.addEventListener('keydown',e=>{{if(e.key==='Enter'||e.key===' '){{
    e.preventDefault();show(b);}}}});
  map.appendChild(t);
}});
show(D.buildings[0]);
"""
    return _doc(body, script)


# ===========================================================================
# 2 — Filter funnel
# ===========================================================================

def filter_funnel(data: dict) -> str:
    """The three criteria applied in turn, with Play and Step controls."""
    if not data.get("start"):
        return _doc(_EMPTY, "")

    body = (
        '<div class="toolbar">'
        '<button id="play" aria-label="Play the funnel">▶ Play</button>'
        '<button id="step" aria-label="Advance one stage">Step ▸</button>'
        '<button id="reset" aria-label="Restart the funnel">↺ Reset</button>'
        '<label class="small" for="slider">Stage</label>'
        '<input id="slider" type="range" min="0" max="3" value="0" step="1" '
        'style="flex:1 1 120px" aria-label="Funnel stage">'
        '</div>'
        '<div id="stages" class="grid" style="grid-template-columns:repeat(4,1fr)"></div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
    )
    script = f"""
const D={_json(data)};
const stagesEl=document.getElementById('stages'), panel=document.getElementById('panel');
const slider=document.getElementById('slider');
let at=0, timer=null;
const columns=[
  {{label:'All buildings', reason:'start'}},
  ...D.stages.map(s=>({{label:'Keep '+s.label, reason:s.criterion}}))
];
function building(b,cls){{return '<span class="chip '+cls+'" data-key="'+b.key+'">'+b.label+'</span>';}}
function render(){{
  clear(stagesEl);
  columns.forEach((c,i)=>{{
    const box=E('div',{{}});
    box.appendChild(E('div',{{class:'title'}},c.label));
    let html='';
    if(i===0){{
      const kept=D.start;
      html=kept.map(b=>building(b,'grey')).join('');
      box.appendChild(E('div',{{}},html));
      box.appendChild(E('div',{{class:'small'}},'6 buildings'));
    }} else {{
      const st=D.stages[i-1];
      html=st.kept.map(b=>building(b,'ok')).join('');
      box.appendChild(E('div',{{}},html||'<span class="small">none left</span>'));
      if(i<=at && st.removed.length){{
        const gone=E('div',{{style:'margin-top:6px'}});
        st.removed.forEach(r=>gone.appendChild(E('span',{{class:'chip no',
          title:r.reason}},'✕ '+r.label)));
        box.appendChild(gone);
      }}
      box.appendChild(E('div',{{class:'small',style:'margin-top:4px'}},
        st.count_in+' → '+st.count_out));
    }}
    if(i>at)box.style.opacity='0.45';
    stagesEl.appendChild(box);
  }});
  const final=E('div',{{style:'grid-column:1/-1;border-top:1px solid #E5E7EB;padding-top:8px;margin-top:2px'}});
  final.appendChild(E('div',{{class:'title'}},D.final_label+' — '
    +D.final.map(b=>b.label).join(', ')));
  final.appendChild(E('div',{{class:'small'}},'Sizes at each stage: '
    +D.counts.join(' → ')+'.  The funnel ends at stage '+at+'.'));
  stagesEl.appendChild(final);
  slider.value=String(at);
  document.getElementById('step').disabled = at>=3;
  panel.innerHTML = at===0
    ? '<h4>All six buildings enter.</h4><p>Press Step or Play to apply the '
      +'criteria one at a time.</p>'
    : '<h4>After stage '+at+': '+D.stages[at-1].label+'</h4>'
      +'<p>Removed here: '+(D.stages[at-1].removed.map(r=>r.label+' ('+r.reason+')')
        .join('; ')||'none')+'</p>';
}}
function stop(){{if(timer){{clearInterval(timer);timer=null;
  document.getElementById('play').textContent='▶ Play';}}}}
function setAt(v){{at=Math.max(0,Math.min(3,v));render();}}
document.getElementById('step').addEventListener('click',()=>{{stop();setAt(at+1);}});
document.getElementById('reset').addEventListener('click',()=>{{stop();setAt(0);}});
slider.addEventListener('input',()=>{{stop();setAt(parseInt(slider.value,10));}});
document.getElementById('play').addEventListener('click',e=>{{
  if(timer){{stop();return;}}
  e.currentTarget.textContent='❚❚ Pause';
  if(at>=3)setAt(0);
  timer=setInterval(()=>{{ if(at>=3){{stop();return;}} setAt(at+1); }},900);
}});
render();
"""
    return _doc(body, script)


# ===========================================================================
# 3 — Three-set Venn
# ===========================================================================

def venn_diagram(data: dict) -> str:
    """Hover a region, click to list it, buttons to apply set operations."""
    if not data.get("counts") or data["counts"]["U"] == 0:
        return _doc(_EMPTY, "")

    body = (
        '<div class="toolbar" id="ops"></div>'
        '<div class="two" style="align-items:start">'
        '<svg id="venn" viewBox="0 0 420 380" role="img" '
        'aria-label="Three overlapping sets of campus buildings"></svg>'
        '<div><div id="panel" class="panel" style="margin-top:0"></div>'
        '<div class="panel"><h4>Region</h4><div id="region" class="row">'
        'Hover a dot to see the region.</div></div></div>'
        '</div>'
    )
    script = f"""
const D={_json(data)};
const svg=document.getElementById('venn'), panel=document.getElementById('panel');
const regionEl=document.getElementById('region');
const circles={{A:{{cx:160,cy:150,r:100}},B:{{cx:260,cy:150,r:100}},C:{{cx:210,cy:235,r:100}}}};
const HOT={{
  A_only:[95,120], B_only:[325,120], C_only:[210,300],
  A_B:[210,118], A_C:[150,216], B_C:[270,216],
  A_B_C:[210,170], none:[30,345]
}};
const REGION_LABEL={{
  A_only:'A only', B_only:'B only', C_only:'C only',
  A_B:'A ∩ B (not C)', A_C:'A ∩ C (not B)', B_C:'B ∩ C (not A)',
  A_B_C:'A ∩ B ∩ C', none:'outside A, B and C'
}};
const FILL={{A:'#86EFAC',B:'#BFDBFE',C:'#FDE68A'}};
let selected=null, hovered=null;
function draw(){{
  clear(svg);
  Object.keys(circles).forEach(k=>{{
    const c=circles[k];
    svg.appendChild(S('circle',{{cx:c.cx,cy:c.cy,r:c.r,fill:FILL[k],
      'fill-opacity':selected?0.42:0.55,stroke:'#14532D','stroke-width':1.4}}));
  }});
  svg.appendChild(S('text',{{x:72,y:58,'font-size':14,'font-weight':700,
    fill:'#14532D'}},'A · demand'));
  svg.appendChild(S('text',{{x:286,y:58,'font-size':14,'font-weight':700,
    fill:'#14532D'}},'B · area'));
  svg.appendChild(S('text',{{x:186,y:352,'font-size':14,'font-weight':700,
    fill:'#14532D'}},'C · solar'));
  Object.keys(HOT).forEach(key=>{{
    const [x,y]=HOT[key];
    const count=D.region_counts[key];
    const active=selected&&selected.includes(key);
    const r=14+Math.min(16,count*4);
    const g=S('g',{{tabindex:'0',role:'button','aria-label':REGION_LABEL[key]
      +', '+count+' buildings','data-region':key,style:'cursor:pointer'}});
    g.appendChild(S('circle',{{cx:x,cy:y,r:r,
      fill:active?'#F59E0B':(hovered===key?'#16A34A':'#FFFFFF'),
      'fill-opacity':active||hovered===key?1:0.88,
      stroke:active?'#B45309':'#14532D','stroke-width':active?2.4:1.3}}));
    g.appendChild(S('text',{{x:x,y:y+4,'text-anchor':'middle','font-size':12,
      'font-weight':700,fill:active?'#FFFFFF':'#14532D'}},count));
    g.addEventListener('mouseenter',()=>{{hovered=key;draw();showRegion(key);}});
    g.addEventListener('mouseleave',()=>{{hovered=null;draw();}});
    g.addEventListener('focus',()=>showRegion(key));
    g.addEventListener('click',()=>showRegion(key));
    g.addEventListener('keydown',e=>{{if(e.key==='Enter'||e.key===' '){{
      e.preventDefault();showRegion(key);}}}});
    svg.appendChild(g);
  }});
}}
function showRegion(key){{
  const members=D.regions[key]||[];
  regionEl.innerHTML='<b>'+REGION_LABEL[key]+'</b> — size '+members.length
    +'<br>'+(members.map(m=>'<span class="chip grey">'+m.label+'</span>')
      .join('')||'<span class="small">no buildings</span>');
}}
function apply(op){{
  selected=op.regions;
  draw();
  panel.innerHTML='<h4>'+op.label+'</h4><p class="mono">'+op.notation+'</p>'
    +'<p>Size: '+op.size+' building(s)</p>'
    +'<div>'+(op.members.map(m=>'<span class="chip ok">'+m.label+'</span>')
      .join('')||'<span class="small">the empty set</span>')+'</div>';
}}
const ops=document.getElementById('ops');
D.operations.forEach(op=>{{
  const b=E('button',{{'aria-pressed':'false'}},op.label);
  b.addEventListener('click',()=>{{
    ops.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed','false'));
    b.setAttribute('aria-pressed','true');
    apply(op);
  }});
  ops.appendChild(b);
}});
panel.innerHTML='<h4>Universal set U</h4><p>'+D.counts.U+' buildings in total. '
  +'A has '+D.counts.A+', B has '+D.counts.B+', C has '+D.counts.C+', and '
  +'E = A ∩ B ∩ C has '+D.counts.E+'.</p>';
draw();
"""
    return _doc(body, script)


# ===========================================================================
# 4 — Relation diagram
# ===========================================================================

def relation_diagram(data: dict) -> str:
    """Node ring, property badges and the relation grid."""
    if not data.get("nodes"):
        return _doc(_EMPTY, "")

    body = (
        '<p class="sub">Buildings sit on a ring; a line joins two buildings that '
        'can be connected. Pick a badge to see why the property holds or fails.</p>'
        '<div id="badges" class="toolbar"></div>'
        '<div class="two" style="align-items:start">'
        '<svg id="ring" viewBox="0 0 380 340" role="img" '
        'aria-label="Buildings on a ring, linked where a connection exists"></svg>'
        '<div id="matrix"></div></div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
    )
    script = f"""
const D={_json(data)};
const svg=document.getElementById('ring'), panel=document.getElementById('panel');
const CX=190, CY=165, R=118;
function pos(i){{const a=(2*Math.PI*i/D.nodes.length)-Math.PI/2;
  return [CX+R*Math.cos(a),CY+R*Math.sin(a)];}}
let highlight=null;
function draw(){{
  clear(svg);
  D.links.forEach(l=>{{
    const [x1,y1]=pos(l.a),[x2,y2]=pos(l.b);
    const on=highlight&&highlight.links.some(p=>(p[0]===l.a&&p[1]===l.b)||(p[0]===l.b&&p[1]===l.a));
    svg.appendChild(S('line',{{x1:x1,y1:y1,x2:x2,y2:y2,
      stroke:on?'#F59E0B':(highlight?'#E5E7EB':'#16A34A'),
      'stroke-width':on?4:1.6,'stroke-linecap':'round'}}));
  }});
  D.nodes.forEach(n=>{{
    const [x,y]=pos(n.id);
    const on=!highlight||highlight.nodes.includes(n.id);
    const g=S('g',{{tabindex:'0',role:'button','aria-label':n.label}});
    g.appendChild(S('circle',{{cx:x,cy:y,r:22,fill:on?'#DCFCE7':'#F3F4F6',
      stroke:on?'#14532D':'#9CA3AF','stroke-width':1.6}}));
    g.appendChild(S('text',{{x:x,y:y+4,'text-anchor':'middle','font-size':10.5,
      'font-weight':700,fill:'#14532D'}},
      n.label.length>9?n.label.slice(0,8)+'…':n.label));
    g.addEventListener('click',()=>{{panel.innerHTML='<h4>'+n.label+'</h4>'
      +'<p>Connections: '+(D.links.filter(l=>l.a===n.id||l.b===n.id).length)
      +'</p>';}});
    svg.appendChild(g);
  }});
}}
function badge(b){{
  const el=E('span',{{class:'badge '+(b.passed?'ok':'no')}});
  const btn=E('button',{{'aria-pressed':'false','data-key':b.key}},
    (b.passed?'✔ ':'✖ ')+b.label);
  btn.addEventListener('click',()=>{{
    document.querySelectorAll('#badges button').forEach(x=>{{
      if(x!==btn)x.setAttribute('aria-pressed','false');}});
    const on=btn.getAttribute('aria-pressed')==='true';
    btn.setAttribute('aria-pressed',on?'false':'true');
    highlight=on?null:D.highlights[b.key];
    draw();
    panel.innerHTML='<h4>'+b.label+' — '+(b.passed?'holds':'fails')+'</h4>'
      +'<p>'+b.reason+'.</p><p>'
      +((D.highlights[b.key]&&D.highlights[b.key].text)||'')+'</p>';
  }});
  el.appendChild(btn);
  return el;
}}
const badges=document.getElementById('badges');
D.badges.forEach(b=>badges.appendChild(badge(b)));
const m=D.matrix, box=document.getElementById('matrix');
let html='<div class="title">Relation grid</div><table class="tt"><tr><th></th>';
m.labels.forEach(l=>html+='<th>'+l.slice(0,3)+'</th>');
html+='</tr>';
m.grid.forEach((row,i)=>{{
  html+='<tr><th>'+m.labels[i].slice(0,3)+'</th>';
  row.forEach(c=>{{html+='<td style="background:'+(c?'#DCFCE7':'#FFFFFF')+'">'
    +(c?'1':'·')+'</td>';}});
  html+='</tr>';
}});
html+='</table><p class="small">1 marks a pair that is in the relation.</p>';
box.innerHTML=html;
panel.innerHTML='<h4>The relation</h4><p>'+D.pair_count+' ordered pairs on '
  +D.domain_size+' buildings. Symmetric, but not reflexive and not transitive — '
  +'try the badges.</p>';
draw();
"""
    return _doc(body, script)


# ===========================================================================
# 5 — Ranking ladder
# ===========================================================================

def ranking_ladder(data: dict) -> str:
    """The demand ladder, reordered with a short animation."""
    if not data.get("order"):
        return _doc(_EMPTY, "")

    body = (
        '<p class="sub">Buildings ordered by daily demand, largest first.</p>'
        '<div id="ladder"></div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
    )
    script = f"""
const D={_json(data)};
const ladder=document.getElementById('ladder');
const panel=document.getElementById('panel');
function draw(){{
  clear(ladder);
  const max=D.order[0]?D.order[0].demand:1;
  D.order.forEach(o=>{{
    const row=E('div',{{style:'display:flex;align-items:center;gap:8px;margin:5px 0'}});
    row.appendChild(E('span',{{class:'chip ok'}},'#'+o.rank));
    const name=E('div',{{style:'flex:0 0 110px;font-size:12.5px;font-weight:600;'
      +'color:#14532D;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'}},
      o.label);
    row.appendChild(name);
    const bar=E('div',{{class:'bar',style:'flex:1 1 auto'}});
    bar.appendChild(E('span',{{style:'width:'+Math.round(100*o.demand/(max||1))
      +'%;background:#16A34A'}}));
    row.appendChild(bar);
    row.appendChild(E('span',{{class:'small',style:'flex:0 0 auto'}},
      o.demand+' kWh/day'));
    row.addEventListener('mouseenter',()=>{{panel.innerHTML='<h4>'+o.label
      +'</h4><p>Rank '+o.rank+' with '+o.demand+' kWh/day.</p>';}});
    ladder.appendChild(row);
  }});
  const tie = D.total_order
    ? '<p class="row"><span class="chip ok">total order</span> every pair is '
      +'comparable and no two demands are equal.</p>'
    : '<p class="row"><span class="chip amber">tie</span> '
      +D.ties.map(g=>g.map(x=>x.label).join(' = ')).join(', ')
      +' share a demand, so the ranking is no longer a strict order.</p>';
  panel.innerHTML='<h4>Has at least as much demand as</h4>'+tie
    +'<p>'+D.pair_count+' pairs in the relation.</p>'
    +(D.note?'<p>'+D.note+'</p>':'');
}}
draw();
"""
    return _doc(body, script)


# ===========================================================================
# 6 — Function maps
# ===========================================================================

def function_maps(data: dict) -> str:
    """Domain and codomain with arrows, plus the property badges."""
    if not any(data.get(k, {}).get("domain") for k in ("demand", "eligible", "rank")):
        return _doc(_EMPTY, "")

    body = (
        '<div class="toolbar" id="tabs"></div>'
        '<svg id="map" viewBox="0 0 460 340" role="img" '
        'aria-label="Function map with arrows from the domain to the codomain"></svg>'
        '<div id="badges" class="toolbar"></div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
    )
    script = f"""
const D={_json(data)};
const svg=document.getElementById('map');
const LABEL={{demand:'demand', eligible:'eligible', rank:'rank'}};
let which='demand';
function fn(){{return D[which];}}
function draw(){{
  const f=fn(); clear(svg);
  const H=320, top=24, n=Math.max(f.domain.length,f.codomain.length,1);
  const y=i=>top+(H-top-30)*(n===1?0.5:i/(n-1));
  const dx=96, cx=300;
  svg.appendChild(S('text',{{x:dx,y:12,'text-anchor':'middle','font-size':12,
    'font-weight':700,fill:'#14532D'}},'domain'));
  svg.appendChild(S('text',{{x:cx,y:12,'text-anchor':'middle','font-size':12,
    'font-weight':700,fill:'#14532D'}},'codomain'));
  const ys={{}};
  f.domain.forEach((d,i)=>{{ ys['d'+i]=y(i); }});
  const cy={{}};
  f.codomain.forEach((c,i)=>{{ cy['c'+i]=y(i); }});
  f.arrows.forEach(a=>{{
    const di=f.domain.findIndex(d=>d.key===a[0]);
    const ci=f.codomain.findIndex(c=>c.key===String(a[1]));
    if(di<0||ci<0)return;
    const on=!selected||(selected[0]===a[0]);
    svg.appendChild(S('path',{{d:'M '+(dx+8)+' '+ys['d'+di]+' C '+(dx+60)+' '
      +ys['d'+di]+', '+(cx-60)+' '+cy['c'+ci]+', '+(cx-8)+' '+cy['c'+ci],
      fill:'none',stroke:on?'#16A34A':'#D1D5DB','stroke-width':on?2:1.2}}));
    svg.appendChild(S('circle',{{cx:cx-8,cy:cy['c'+ci],r:3,fill:on?'#16A34A':'#D1D5DB'}}));
  }});
  f.domain.forEach((d,i)=>{{
    const g=S('g',{{tabindex:'0',role:'button','aria-label':d.label,
      'data-key':d.key,style:'cursor:pointer'}});
    g.appendChild(S('circle',{{cx:dx,cy:ys['d'+i],r:7,fill:'#DCFCE7',
      stroke:'#14532D','stroke-width':1.4}}));
    g.appendChild(S('text',{{x:dx-12,y:ys['d'+i]+4,'text-anchor':'end',
      'font-size':11,fill:'#1F2937'}},d.label));
    g.addEventListener('mouseenter',()=>show(d.key));
    g.addEventListener('click',()=>show(d.key));
    g.addEventListener('focus',()=>show(d.key));
    svg.appendChild(g);
  }});
  f.codomain.forEach((c,i)=>{{
    const miss=f.missing.includes(c.key);
    svg.appendChild(S('circle',{{cx:cx,cy:cy['c'+i],r:7,
      fill:miss?'#FEE2E2':'#DCFCE7',stroke:miss?'#DC2626':'#14532D',
      'stroke-width':1.4}}));
    svg.appendChild(S('text',{{x:cx+12,y:cy['c'+i]+4,'font-size':11,
      fill:miss?'#B91C1C':'#1F2937'}},c.label+(miss?'  ← no preimage':'')));
  }});
}}
let selected=null;
function show(key){{
  const f=fn();
  const img=(f.arrows.find(a=>a[0]===key)||[])[1];
  selected=[key];
  draw();
  panel.innerHTML='<h4>'+key+' ↦ '+img+'</h4><p>'+f.details+'</p>';
}}
function badges(){{
  const f=fn(), box=document.getElementById('badges'); clear(box);
  [['injective','one-to-one'],['surjective','onto'],['bijective','bijective']]
    .forEach(([k,label])=>{{
      box.appendChild(E('span',{{class:'badge '+(f[k]?'ok':'no')}},
        (f[k]?'✔ ':'✖ ')+label));
    }});
}}
const tabs=document.getElementById('tabs');
Object.keys(LABEL).forEach(k=>{{
  const b=E('button',{{'aria-pressed':k===which?'true':'false'}},LABEL[k]);
  b.addEventListener('click',()=>{{
    which=k; selected=null;
    tabs.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed','false'));
    b.setAttribute('aria-pressed','true');
    draw(); badges();
    const f=fn();
    panel.innerHTML='<h4>'+LABEL[k]+' : '+f.domain.length+' → '
      +f.codomain.length+'</h4><p>'+f.details+'</p>';
  }});
  tabs.appendChild(b);
}});
draw(); badges();
const f0=fn();
panel.innerHTML='<h4>'+LABEL[which]+'</h4><p>'+f0.details+'</p>';
"""
    return _doc(body, script)


# ===========================================================================
# 7 — Logic gate
# ===========================================================================

def logic_gate(data: dict) -> str:
    """Three switches into an AND gate, with the truth-table row it selects."""
    if not data.get("buildings"):
        return _doc(_EMPTY, "")

    body = (
        '<div class="toolbar">'
        '<label class="small" for="pick">Building</label>'
        '<select id="pick" style="border:1px solid #E5E7EB;border-radius:8px;'
        'padding:3px 6px"></select>'
        '<span class="small">or flip a switch:</span>'
        '<button id="sp" aria-pressed="false">p</button>'
        '<button id="sq" aria-pressed="false">q</button>'
        '<button id="sr" aria-pressed="false">r</button>'
        '</div>'
        '<svg id="gate" viewBox="0 0 440 190" style="max-height:220px" role="img" '
        'aria-label="Three switches feeding an AND gate and a lamp"></svg>'
        '<div class="two" style="margin-top:6px;align-items:start">'
        '<div id="panel" class="panel" style="margin-top:0"></div>'
        '<div class="panel" style="margin-top:0;overflow:auto">'
        '<div class="title" style="margin-bottom:4px">Truth table</div>'
        '<div id="tt"></div></div></div>'
    )
    script = f"""
const D={_json(data)};
const svg=document.getElementById('gate');
const pick=document.getElementById('pick');
let p=false,q=false,r=false;
function draw(){{
  clear(svg);
  const sw=(x,y,v,label)=>{{
    svg.appendChild(S('rect',{{x:x,y:y-11,width:64,height:22,rx:8,
      fill:v?'#16A34A':'#E5E7EB',stroke:'#14532D','stroke-width':1.3}}));
    svg.appendChild(S('text',{{x:x+32,y:y+4,'text-anchor':'middle','font-size':12,
      'font-weight':700,fill:v?'#FFFFFF':'#14532D'}},label+' '+(v?'1':'0')));
    svg.appendChild(S('line',{{x1:x+64,y1:y,x2:196,y2:y,stroke:'#14532D',
      'stroke-width':1.4}}));
  }};
  sw(8,40,p,'p'); sw(8,100,q,'q'); sw(8,160,r,'r');
  svg.appendChild(S('path',{{d:'M196 24 L246 24 L246 176 L196 176 Z',
    fill:'#F0FDF4',stroke:'#14532D','stroke-width':1.5}}));
  svg.appendChild(S('path',{{d:'M246 46 A70 70 0 0 1 246 154',
    fill:'none',stroke:'#14532D','stroke-width':1.5}}));
  svg.appendChild(S('text',{{x:186,y:104,'font-size':12,'font-weight':700,
    fill:'#14532D'}},'AND'));
  const on=p&&q&&r;
  svg.appendChild(S('line',{{x1:250,y1:100,x2:330,y2:100,stroke:'#14532D',
    'stroke-width':1.5}}));
  svg.appendChild(S('circle',{{cx:352,cy:100,r:22,
    fill:on?'#F59E0B':'#F3F4F6',stroke:'#14532D','stroke-width':1.5}}));
  for(let i=0;i<8;i++){{const a=i*Math.PI/4;
    svg.appendChild(S('line',{{x1:352+24*Math.cos(a),y1:100+24*Math.sin(a),
      x2:352+30*Math.cos(a),y2:100+30*Math.sin(a),
      stroke:on?'#F59E0B':'#D1D5DB','stroke-width':1.6,
      'stroke-linecap':'round'}}));}}
  svg.appendChild(S('text',{{x:352,y:150,'text-anchor':'middle','font-size':12,
    'font-weight':700,fill:on?'#15803D':'#6B7280'}},
    on?'eligible':'not eligible'));
}}
function rowIndex(){{return (p?1:0)*4+(q?1:0)*2+(r?1:0);}}
function table(){{
  const box=document.getElementById('tt');
  const idx=rowIndex();
  let html='<table class="tt"><tr><th>p</th><th>q</th><th>r</th><th>eligible</th>'
    +'<th>buildings</th></tr>';
  D.rows.forEach(row=>{{
    const el=row.eligible;
    html+='<tr class="'+(row.index===idx?'sel':'')+'"><td style="background:'
      +(row.p?'#DCFCE7':'#FEE2E2')+'">'+(row.p?'1':'0')+'</td>'
      +'<td style="background:'+(row.q?'#DCFCE7':'#FEE2E2')+'">'+(row.q?'1':'0')+'</td>'
      +'<td style="background:'+(row.r?'#DCFCE7':'#FEE2E2')+'">'+(row.r?'1':'0')+'</td>'
      +'<td style="background:'+(el?'#16A34A':'#F3F4F6')+';color:'+(el?'#fff':'#6B7280')+'">'
      +(el?'1':'0')+'</td>'
      +'<td>'+(row.buildings.map(b=>b.label).join(', ')||'—')+'</td></tr>';
  }});
  html+='</table>';
  box.innerHTML=html;
  const b=D.rows[idx];
  const eligible=(p&&q&&r);
  document.getElementById('panel').innerHTML='<h4>Current combination</h4>'
    +'<p>p='+(p?1:0)+', q='+(q?1:0)+', r='+(r?1:0)
    +' → <b>eligible = '+(eligible?'1 ✔':'0 ✖')+'</b></p>'
    +'<p>Buildings in this row: '
    +(b.buildings.map(x=>'<span class="chip '+(eligible?'ok':'grey')+'">'+x.label+'</span>').join('')
      ||'<span class="small">no building falls here</span>')+'</p>';
}}
function syncButtons(){{
  document.getElementById('sp').setAttribute('aria-pressed',p?'true':'false');
  document.getElementById('sq').setAttribute('aria-pressed',q?'true':'false');
  document.getElementById('sr').setAttribute('aria-pressed',r?'true':'false');
}}
D.buildings.forEach((b,i)=>{{
  const o=E('option',{{value:String(i)}},b.label+' ('+[b.p?1:0,b.q?1:0,b.r?1:0].join('')
    +')');
  pick.appendChild(o);
}});
pick.addEventListener('change',()=>{{
  const b=D.buildings[parseInt(pick.value,10)];
  p=b.p; q=b.q; r=b.r; syncButtons(); draw(); table();
}});
['sp','sq','sr'].forEach(id=>{{
  document.getElementById(id).addEventListener('click',e=>{{
    if(id==='sp')p=!p; if(id==='sq')q=!q; if(id==='sr')r=!r;
    syncButtons(); draw(); table();
  }});
}});
{{const b=D.buildings[0]; p=b.p;q=b.q;r=b.r; pick.value='0'; syncButtons();}}
draw(); table();
"""
    return _doc(body, script)


# ===========================================================================
# 8 — Truth table grid
# ===========================================================================

def truth_table_grid(data: dict) -> str:
    """Eight coloured rows; click one to filter the buildings."""
    rows = data.get("rows") or []
    if not rows:
        return _doc(_EMPTY, "")

    body = (
        '<div class="toolbar"><span id="cls" class="badge ok"></span>'
        '<button id="all" aria-pressed="true">Show all rows</button></div>'
        '<div id="grid"></div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
    )
    script = f"""
const D={_json(data)};
const grid=document.getElementById('grid'), panel=document.getElementById('panel');
document.getElementById('cls').textContent=D.formula+' is a '+D.classification;
let only=null;
function draw(){{
  let html='<table class="tt"><tr><th>p</th><th>q</th><th>r</th><th>eligible</th>'
    +'<th>buildings</th></tr>';
  D.rows.forEach(row=>{{
    const el=row.eligible;
    const show=only===null||only===row.index;
    html+='<tr data-index="'+row.index+'" tabindex="0" class="'
      +(only===row.index?'sel':'')+'" style="'
      +(show?'':'opacity:.32;')+'cursor:pointer">'
      +'<td style="background:'+(row.p?'#DCFCE7':'#FEE2E2')+'">'+(row.p?'1':'0')+'</td>'
      +'<td style="background:'+(row.q?'#DCFCE7':'#FEE2E2')+'">'+(row.q?'1':'0')+'</td>'
      +'<td style="background:'+(row.r?'#DCFCE7':'#FEE2E2')+'">'+(row.r?'1':'0')+'</td>'
      +'<td style="background:'+(el?'#16A34A':'#F3F4F6')+';color:'
      +(el?'#fff':'#6B7280')+'">'+(el?'1':'0')+'</td>'
      +'<td>'+(row.buildings.map(b=>b.label).join(', ')||'—')+'</td></tr>';
  }});
  html+='</table>';
  grid.innerHTML=html;
  grid.querySelectorAll('tr[data-index]').forEach(tr=>{{
    const idx=parseInt(tr.getAttribute('data-index'),10);
    const act=()=>{{only=(only===idx?null:idx); draw(); detail();}};
    tr.addEventListener('click',act);
    tr.addEventListener('keydown',e=>{{if(e.key==='Enter'||e.key===' '){{
      e.preventDefault();act();}}}});
  }});
}}
function detail(){{
  if(only===null){{
    panel.innerHTML='<h4>All eight rows</h4><p>'
      +D.rows.filter(r=>r.buildings.length).length+' rows carry at least one '
      +'building. Click a row to isolate it.</p>';
    return;
  }}
  const row=D.rows[only];
  panel.innerHTML='<h4>Row '+only+' — p='+(row.p?1:0)+', q='+(row.q?1:0)
    +', r='+(row.r?1:0)+'</h4><p>eligible = '+(row.eligible?1:0)+'</p>'
    +'<p>'+(row.buildings.map(b=>'<span class="chip '
      +(row.eligible?'ok':'grey')+'">'+b.label+'</span>').join('')
      ||'<span class="small">no building is in this row</span>')+'</p>';
}}
document.getElementById('all').addEventListener('click',()=>{{only=null;draw();detail();}});
draw(); detail();
"""
    return _doc(body, script)


# ===========================================================================
# 9 — De Morgan
# ===========================================================================

def de_morgan(data: dict) -> str:
    """Two circuits stepped through the same eight rows."""
    rows = data.get("rows") or []
    if not rows:
        return _doc(_EMPTY, "")

    body = (
        '<div class="toolbar">'
        '<button id="play" aria-label="Play through the rows">▶ Play</button>'
        '<button id="next" aria-label="Next row">Next ▸</button>'
        '<label class="small" for="row">Row</label>'
        '<input id="row" type="range" min="0" max="7" value="0" step="1" '
        'style="flex:1 1 120px">'
        '<span id="verdict" class="badge ok"></span></div>'
        '<div class="two">'
        '<svg id="left" viewBox="0 0 300 120" role="img" '
        'aria-label="Circuit for not (p and q and r)"></svg>'
        '<svg id="right" viewBox="0 0 300 120" role="img" '
        'aria-label="Circuit for (not p) or (not q) or (not r)"></svg></div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
    )
    script = f"""
const D={_json(data)};
let i=0, timer=null;
function gate(svg,x,y,label,active){{
  svg.appendChild(S('rect',{{x:x,y:y,width:56,height:34,rx:8,
    fill:active?'#16A34A':'#F3F4F6',stroke:'#14532D','stroke-width':1.4}}));
  svg.appendChild(S('text',{{x:x+28,y:y+22,'text-anchor':'middle','font-size':11.5,
    'font-weight':700,fill:active?'#fff':'#14532D'}},label));
}}
function render(){{
  const row=D.rows[i];
  const L=document.getElementById('left'), R=document.getElementById('right');
  clear(L); clear(R);
  L.appendChild(S('text',{{x:6,y:16,'font-size':11,'font-weight':700,
    fill:'#14532D'}},D.left_pretty));
  gate(L,14,40,'AND',row.p&&row.q&&row.r);
  gate(L,150,40,'NOT',!row.left);
  L.appendChild(S('line',{{x1:70,y1:57,x2:150,y2:57,stroke:'#14532D','stroke-width':1.4}}));
  L.appendChild(S('text',{{x:150,y:100,'font-size':11.5,fill:'#1F2937'}},
    'p='+(row.p?1:0)+' q='+(row.q?1:0)+' r='+(row.r?1:0)+' → '+(row.left?1:0)));
  R.appendChild(S('text',{{x:6,y:16,'font-size':11,'font-weight':700,
    fill:'#14532D'}},D.right_pretty));
  gate(R,14,40,'OR',row.right);
  gate(R,150,40,'OUT',row.right);
  R.appendChild(S('line',{{x1:70,y1:57,x2:150,y2:57,stroke:'#14532D','stroke-width':1.4}}));
  R.appendChild(S('text',{{x:150,y:100,'font-size':11.5,fill:'#1F2937'}},
    '¬p='+((!row.p)?1:0)+' ¬q='+((!row.q)?1:0)+' ¬r='+((!row.r)?1:0)
    +' → '+(row.right?1:0)));
  document.getElementById('row').value=String(i);
  document.getElementById('verdict').textContent=row.equal
    ? 'same output ✔' : 'different ✖';
  document.getElementById('verdict').className='badge '+(row.equal?'ok':'no');
  document.getElementById('panel').innerHTML='<h4>Row '+i+'</h4>'
    +'<p>'+D.left_pretty+' = '+(row.left?1:0)+' and '+D.right_pretty+' = '
    +(row.right?1:0)+' — the two sides agree on all eight rows, so they are '
    +'equivalent.</p>';
}}
function stop(){{if(timer){{clearInterval(timer);timer=null;
  document.getElementById('play').textContent='▶ Play';}}}}
document.getElementById('next').addEventListener('click',()=>{{
  stop(); i=(i+1)%8; render();}});
document.getElementById('row').addEventListener('input',e=>{{
  stop(); i=parseInt(e.target.value,10); render();}});
document.getElementById('play').addEventListener('click',e=>{{
  if(timer){{stop();return;}}
  e.currentTarget.textContent='❚❚ Pause'; i=0; render();
  timer=setInterval(()=>{{i=(i+1)%8; render();
    if(i===0)stop();}},900);
}});
render();
"""
    return _doc(body, script)


# ===========================================================================
# 10 — Formula tester
# ===========================================================================

def formula_tester(data: dict) -> str:
    """Truth table, classification and implication for a typed formula."""
    if data.get("errors"):
        msg = " ".join(str(e) for e in data["errors"])
        return _doc(f'<div class="empty"><b>That formula could not be read.</b>'
                    f'<br>{msg}</div>', "")

    body = (
        '<div class="two" style="align-items:start">'
        '<div><div id="cls" class="badge ok" style="margin-bottom:8px"></div>'
        '<div id="table"></div></div>'
        '<div id="panel" class="panel" style="margin-top:0"></div></div>'
    )
    script = f"""
const D={_json(data)};
const cls=document.getElementById('cls');
cls.textContent=D.formula+' is a '+D.classification
  +(D.equivalent_to_eligible?' and is equivalent to eligible':'');
cls.className='badge '+(D.classification==='tautology'?'ok':'no');
const vars=D.variables;
let html='<table class="tt"><tr>'+vars.map(v=>'<th>'+v+'</th>').join('')
  +'<th>result</th></tr>';
D.rows.forEach(row=>{{
  html+='<tr>'+vars.map(v=>'<td style="background:'
    +(row.values[v]?'#DCFCE7':'#FEE2E2')+'">'+(row.values[v]?1:0)+'</td>').join('')
    +'<td style="background:'+(row.result?'#16A34A':'#F3F4F6')+';color:'
    +(row.result?'#fff':'#6B7280')+'">'+(row.result?1:0)+'</td></tr>';
}});
html+='</table>';
document.getElementById('table').innerHTML=html;
const imp=D.implication;
document.getElementById('panel').innerHTML='<h4>Classification</h4>'
  +'<p>'+(D.classification==='tautology'?'True on every row.'
    :D.classification==='contradiction'?'False on every row.'
    :'True on some rows and false on others.')+'</p>'
  +'<h4>Equivalent to eligible?</h4><p>'
  +(D.equivalent_to_eligible?'Yes — the two formulas agree on every row.'
    :'No — they differ on at least one row.')+'</p>'
  +'<h4>Implication eligible → high demand</h4>'
  +'<p class="mono">'+imp.statement+'</p>'
  +'<p>Contrapositive <span class="mono">'+imp.contrapositive+'</span> — '
  +(imp.statement_vs_contrapositive?'equivalent ✔':'not equivalent ✖')+'</p>'
  +'<p>Converse <span class="mono">'+imp.converse+'</span> — '
  +(imp.statement_vs_converse?'equivalent ✔':'not equivalent ✖')+'</p>';
"""
    return _doc(body, script)


# ===========================================================================
# 11 — Proof stepper
# ===========================================================================

def proof_stepper(data: dict) -> str:
    """Numbered step cards revealed one at a time, with a live check."""
    steps = data.get("steps") or []
    if not steps:
        return _doc(_EMPTY, "")

    body = (
        f'<div class="title">{data.get("title","")}</div>'
        f'<p class="sub"><b>Claim.</b> {data.get("claim","")}</p>'
        '<div class="toolbar">'
        '<button id="next" aria-label="Reveal the next step">Next step ▸</button>'
        '<button id="all" aria-label="Reveal every step">Show all</button>'
        '<button id="reset" aria-label="Hide the steps">↺ Reset</button>'
        '<span class="small" id="count"></span></div>'
        '<div id="steps"></div>'
        '<div id="check" class="panel" role="status" aria-live="polite"></div>'
    )
    script = f"""
const D={_json(data)};
let shown=1;
const STATUS={{assumption:'amber',derived:'grey',conclusion:'ok',
  initialization:'ok',maintenance:'amber',termination:'ok'}};
function draw(){{
  const box=document.getElementById('steps');
  box.innerHTML='';
  D.steps.forEach((s,idx)=>{{
    const card=E('div',{{class:'panel',style:'opacity:'+(idx<shown?'1':'0.28')}});
    card.appendChild(E('div',{{class:'row'}},'<b>Step '+(idx+1)+'</b> '
      +'<span class="chip '+(STATUS[s.status]||'grey')+'">'+s.status+'</span>'));
    card.appendChild(E('div',{{class:'row'}},s.claim));
    card.appendChild(E('div',{{class:'small'}},'Why: '+s.why));
    box.appendChild(card);
  }});
  document.getElementById('count').textContent=shown+' of '+D.steps.length
    +' steps shown';
  const c=D.check;
  document.getElementById('check').innerHTML='<h4>Live check on the campus '
    +'data — '+c.headline+'</h4><p><span class="chip '
    +(c.passed?'ok':'no')+'">'+(c.passed?'passes':'fails')+'</span> '
    +c.message+'</p><p class="small">'+c.evidence+'</p>';
}}
document.getElementById('next').addEventListener('click',()=>{{
  shown=Math.min(D.steps.length,shown+1); draw();}});
document.getElementById('all').addEventListener('click',()=>{{
  shown=D.steps.length; draw();}});
document.getElementById('reset').addEventListener('click',()=>{{
  shown=1; draw();}});
draw();
"""
    return _doc(body, script)


# ===========================================================================
# 12 — Induction dominoes
# ===========================================================================

def induction_dominoes(data: dict) -> str:
    """A row of dominoes illustrating the induction argument."""
    n = int(data.get("n") or 1)
    if n < 1:
        return _doc(_EMPTY, "")

    body = (
        f'<div class="title">Claim</div><p class="sub">{data.get("claim","")}</p>'
        '<div class="toolbar">'
        '<button id="tip" aria-label="Tip the first domino">Tip the first domino</button>'
        '<button id="reset" aria-label="Stand the dominoes up">↺ Reset</button>'
        '<span class="small">n = ' + str(n) + '</span></div>'
        '<svg id="dom" viewBox="0 0 420 150" role="img" '
        'aria-label="A row of dominoes"></svg>'
        '<div class="two" style="margin-top:8px">'
        '<div class="panel" style="margin-top:0"><h4>Base case</h4><p>'
        + str(data.get("base_case", {}).get("text", "")) + '</p></div>'
        '<div class="panel" style="margin-top:0"><h4>Inductive step</h4><p>'
        + str(data.get("step", {}).get("show", "")) + '</p></div></div>'
        '<div class="panel"><h4>Note</h4><p>' + str(data.get("note", "")) + '</p>'
        '<p class="small">Cases listed: ' + str(len(data.get("cases", [])))
        + '.</p></div>'
    )
    script = """
const N=""" + str(n) + """;
const svg=document.getElementById('dom');
const W=420, gap=W/(N+1);
function draw(fallen){
  clear(svg);
  for(let i=0;i<N;i++){
    const x=gap*(i+1);
    const down=i<fallen;
    const g=S('g',{style:down?'transform:rotate(78deg);transform-origin:'+x+'px 118px;'
      +'transition:transform '+MS(260)+'ms ease':''});
    g.appendChild(S('rect',{x:x-5,y:34,width:10,height:84,rx:3,
      fill:down?'#F59E0B':(i===0?'#16A34A':'#DCFCE7'),stroke:'#14532D',
      'stroke-width':1.3}));
    svg.appendChild(g);
    svg.appendChild(S('line',{x1:0,y1:118,x2:W,y2:118,stroke:'#E5E7EB',
      'stroke-width':1.5}));
  }
  svg.appendChild(S('text',{x:6,y:16,'font-size':11,fill:'#6B7280'},
    'base case tips #1, each domino tips the next — up to n = '+N));
  if(fallen>=N){
    svg.appendChild(S('text',{x:W-6,y:16,'text-anchor':'end','font-size':11,
      'font-weight':700,fill:'#15803D'},'all n fallen'));
  }
}
let fallen=0, timer=null;
document.getElementById('tip').addEventListener('click',()=>{
  fallen=1; draw(fallen);
  if(timer)clearInterval(timer);
  timer=setInterval(()=>{fallen++; draw(fallen);
    if(fallen>=N)clearInterval(timer);},MS(300)||0);
});
document.getElementById('reset').addEventListener('click',()=>{
  if(timer)clearInterval(timer); fallen=0; draw(0);});
draw(0);
"""
    return _doc(body, script)


# ===========================================================================
# 13 — Strong induction tiles
# ===========================================================================

_PHASE_FILL = {2: "#DCFCE7", 3: "#FDE68A"}


def strong_induction_tiles(data: dict) -> str:
    """Phase tiles showing how n splits into groups of 2 and 3."""
    n = int(data.get("n") or 2)
    if n < 2:
        return _doc(_EMPTY, "")

    body = (
        f'<p class="sub">{data.get("claim","")}</p>'
        '<div class="toolbar">'
        '<button id="play" aria-label="Play through the groups">▶ Play</button>'
        '<button id="step" aria-label="Next group">Step ▸</button>'
        '<button id="reset" aria-label="Clear the selection">↺ Reset</button>'
        '<input id="slider" type="range" min="0" max="'
        + str(len(data.get("phases") or [2]))
        + '" value="0" step="1" style="flex:1 1 100px" aria-label="Group">'
        '</div>'
        '<div class="title">Grouping for n = ' + str(n) + '</div>'
        '<div id="tiles" style="display:flex;flex-wrap:wrap;gap:8px"></div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
        '<div class="two" style="margin-top:10px">'
        '<div class="panel" style="margin-top:0"><h4>Base cases</h4>'
        + "".join(f'<p><span class="chip amber">n = {b["n"]}</span> {b["text"]}</p>'
                  for b in data.get("base_cases", [])) +
        '</div>'
        '<div class="panel" style="margin-top:0"><h4>Strong step</h4><p>'
        + str(data.get("step", {}).get("show", ""))
        + '</p><p class="small">' + str(data.get("note", "")) + '</p></div></div>'
    )
    script = f"""
const D={_json(data)};
const box=document.getElementById('tiles');
const panel=document.getElementById('panel');
const slider=document.getElementById('slider');
const FILL={{'2':'#DCFCE7','3':'#FDE68A'}};
const tiles=[];
let at=0, timer=null;
D.phases.forEach((size,i)=>{{
  const t=E('div',{{class:'tile',tabindex:'0',role:'button',
    'aria-label':'group of '+size+' buildings',
    style:'width:'+(40+size*22)+'px;min-height:'+(40+size*22)+'px;'
      +'background:'+FILL[String(size)]+';align-items:center;'
      +'justify-content:center'}});
  t.appendChild(E('b',{{style:'font-size:15px;text-align:center'}},size+' buildings'));
  t.appendChild(E('div',{{class:'small',style:'text-align:center'}},
    'needs '+(size-1)+' connections'));
  const pick=()=>{{stop(); setAt(i+1);}};
  t.addEventListener('click',pick);
  t.addEventListener('keydown',e=>{{
    if(e.key==='Enter'||e.key===' '){{e.preventDefault();pick();}}}});
  box.appendChild(t); tiles.push(t);
}});
const summary=E('div',{{class:'tile',tabindex:'0',role:'button',
  'aria-label':'all '+D.n+' buildings',
  style:'background:#F3F4F6;width:auto;min-height:auto;padding:8px 12px'}});
summary.innerHTML='<b style="font-size:12.5px">'+D.n+' buildings</b>'
  +'<div class="small">'+(D.phases.length)+' group(s) of 2s and 3s</div>';
summary.addEventListener('click',()=>{{stop(); setAt(0);}});
summary.addEventListener('keydown',e=>{{
  if(e.key==='Enter'||e.key===' '){{e.preventDefault();stop();setAt(0);}}}});
box.appendChild(summary);
function stop(){{if(timer){{clearInterval(timer);timer=null;
  document.getElementById('play').textContent='▶ Play';}}}}
function setAt(v){{
  at=Math.max(0,Math.min(D.phases.length,v));
  tiles.forEach((t,i)=>{{
    t.style.outline=i===at-1?'3px solid #F59E0B':'none';
  }});
  slider.value=String(at);
  if(at===0){{
    panel.innerHTML='<h4>All '+D.n+' buildings</h4><p>'+D.phases.length
      +' group(s) of two and three. Click a tile or press Enter to read why '
      +'that group is allowed.</p>';
    return;
  }}
  const size=D.phases[at-1];
  const bases=(D.base_cases||[]).map(b=>b.n).join(' and ');
  panel.innerHTML='<h4>Group '+at+' of '+D.phases.length
    +' — '+size+' buildings</h4>'
    +'<p>This group needs '+(size-1)+' connections. The argument leans on the '
    +'base cases n = '+bases+' and on every smaller grouping already shown.</p>'
    +'<p class="small">'+(D.step&&D.step.show?D.step.show:'')+'</p>';
}}
document.getElementById('step').addEventListener('click',()=>{{
  stop(); setAt(at>=D.phases.length?0:at+1);}});
document.getElementById('reset').addEventListener('click',()=>{{stop();setAt(0);}});
slider.addEventListener('input',()=>{{stop();setAt(parseInt(slider.value,10));}});
document.getElementById('play').addEventListener('click',e=>{{
  if(timer){{stop();return;}}
  e.currentTarget.textContent='❚❚ Pause';
  if(at>=D.phases.length)setAt(0);
  timer=setInterval(()=>{{ if(at>=D.phases.length){{stop();return;}} setAt(at+1); }},800);
}});
setAt(0);
"""
    return _doc(body, script)


# ===========================================================================
# 14 — Loop-invariant conveyor
# ===========================================================================

def loop_invariant_conveyor(data: dict) -> str:
    """Buildings move through the filter one at a time; the tray grows."""
    steps = data.get("steps") or []
    if not steps:
        return _doc(_EMPTY, "")

    body = (
        '<div class="toolbar">'
        '<button id="play" aria-label="Play the loop">▶ Play</button>'
        '<button id="step" aria-label="Run one iteration">Step ▸</button>'
        '<button id="reset" aria-label="Restart">↺ Reset</button>'
        '<label class="small" for="slider">Iteration</label>'
        '<input id="slider" type="range" min="0" max="' + str(len(steps)) + '" '
        'value="0" step="1" style="flex:1 1 120px"></div>'
        '<div id="belt" style="display:flex;flex-wrap:wrap;gap:6px;'
        'min-height:34px"></div>'
        '<div class="title" style="margin-top:10px">Eligible so far</div>'
        '<div id="tray" style="display:flex;flex-wrap:wrap;gap:6px;'
        'min-height:34px"></div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
    )
    script = f"""
const D={_json(data)};
const belt=document.getElementById('belt'), tray=document.getElementById('tray');
const slider=document.getElementById('slider');
let at=0, timer=null;
function draw(){{
  clear(belt); clear(tray);
  const upto=at;
  D.steps.forEach(s=>{{
    const done=s.index<=upto;
    const c=E('span',{{class:'chip '+(done?(s.accepted?'ok':'no'):'grey')}},
      s.label+(done?(s.accepted?' → kept':' → dropped'):''));
    belt.appendChild(c);
  }});
  const current=upto>0?D.steps[upto-1]:null;
  const names=current?current.tray:[];
  if(!names.length){{tray.appendChild(E('span',{{class:'small'}},'empty'));}}
  names.forEach(n=>tray.appendChild(E('span',{{class:'chip ok'}},n.label)));
  slider.value=String(upto);
  document.getElementById('step').disabled=upto>=D.steps.length;
  if(current){{
    document.getElementById('panel').innerHTML='<h4>Iteration '+current.index
      +' — '+current.label+'</h4><p>'+(current.accepted
        ?'Meets all three criteria, so it is placed in the tray.'
        :'Fails a criterion, so it is skipped.')+'</p>'
      +'<p class="small">'+D.invariant+'</p>'
      +'<p><span class="chip '+(current.invariant_holds?'ok':'no')+'">'
      +(current.invariant_holds?'invariant holds':'invariant broken')
      +'</span> tray size '+names.length+'</p>';
  }} else {{
    document.getElementById('panel').innerHTML='<h4>Before the loop</h4>'
      +'<p>k = 0 and the tray is empty, which is the invariant at k = 0.</p>'
      +'<p class="small">Overall: '+(D.holds?'every step preserved the invariant'
        :'the invariant failed')+'.</p>';
  }}
}}
function stop(){{if(timer){{clearInterval(timer);timer=null;
  document.getElementById('play').textContent='▶ Play';}}}}
function setAt(v){{at=Math.max(0,Math.min(D.steps.length,v));draw();}}
document.getElementById('step').addEventListener('click',()=>{{stop();setAt(at+1);}});
document.getElementById('reset').addEventListener('click',()=>{{stop();setAt(0);}});
slider.addEventListener('input',()=>{{stop();setAt(parseInt(slider.value,10));}});
document.getElementById('play').addEventListener('click',e=>{{
  if(timer){{stop();return;}}
  e.currentTarget.textContent='❚❚ Pause';
  if(at>=D.steps.length)setAt(0);
  timer=setInterval(()=>{{ if(at>=D.steps.length){{stop();return;}} setAt(at+1); }},800);
}});
draw();
"""
    return _doc(body, script)


# ===========================================================================
# 15 — Selection explorer (Counting)
# ===========================================================================

def selection_explorer(data: dict) -> str:
    """Choose k of the eligible buildings: combinations, orders, repetition."""
    if not data.get("buildings"):
        return _doc(_EMPTY, "")

    body = (
        '<p class="sub">The eligible buildings can be chosen a few at a time. '
        'Move the slider to change how many are chosen, then switch order and '
        'repetition on or off. Hover or click a row for its details.</p>'
        '<div class="toolbar">'
        '<button id="play" aria-label="Play through the selections">▶ Play</button>'
        '<button id="step" aria-label="Next selection">Step ▸</button>'
        '<button id="reset" aria-label="Reset the list">↺ Reset</button>'
        '<span class="small">chosen at a time: <b id="kval">' + str(data["k"])
        + '</b> of ' + str(data["n"]) + '</span>'
        '<input id="krange" type="range" min="0" max="' + str(data["max_k"])
        + '" value="' + str(data["k"]) + '" step="1" style="flex:1 1 120px" '
        'aria-label="Buildings chosen at a time">'
        '</div>'
        '<div class="toolbar">'
        '<button id="order" aria-pressed="false">order matters</button>'
        '<button id="repeat" aria-pressed="false">a building may repeat</button>'
        '</div>'
        '<div id="pool" style="display:flex;flex-wrap:wrap;gap:4px;margin:2px 0 8px"></div>'
        '<div class="two" style="align-items:start">'
        '<div><div class="title" id="lhead">Every way to choose</div>'
        '<div id="list"></div></div>'
        '<div><div id="counts" class="panel" style="margin-top:0"></div>'
        '<div id="panel" class="panel"></div></div>'
        '</div>'
    )
    script = "const D=" + _json(data) + r"""
const pool=document.getElementById('pool');
const list=document.getElementById('list');
const counts=document.getElementById('counts');
const panel=document.getElementById('panel');
const lhead=document.getElementById('lhead');
const krange=document.getElementById('krange');
const kval=document.getElementById('kval');
const bOrder=document.getElementById('order');
const bRepeat=document.getElementById('repeat');
let ordered=false, repeats=false, at=0, timer=null;
D.buildings.forEach(function(b){pool.appendChild(E('span',{class:'chip ok'},b.label));});
function chips(names,sep){
  return names.map(function(n){return '<span class="chip ok">'+n+'</span>';}).join(sep||' ');
}
function detail(title,html){panel.innerHTML='<h4>'+title+'</h4>'+html;}
function render(){
  const k=parseInt(krange.value,10);
  kval.textContent=String(k);
  bOrder.setAttribute('aria-pressed',ordered?'true':'false');
  bRepeat.setAttribute('aria-pressed',repeats?'true':'false');
  const st=D.by_k[k];
  clear(list);
  let title;
  if(repeats){
    const side=ordered? st.repeat.ordered : st.repeat.unordered;
    title=ordered? 'Orders, repeats allowed' : 'Batches, repeats allowed';
    list.appendChild(E('p',{class:'small'},'With repetition there are '
      +side.count+' '+(ordered?'installation orders':'batches')+' — '+side.formula
      +'. The list is not written out here.'));
  }else{
    const s=ordered? st.ordered : st.unordered;
    title=ordered? 'Every installation order' : 'Every way to choose';
    if(!s.items.length){
      list.appendChild(E('p',{class:'small'},
        'Only the empty choice: no building is picked.'));
    }
    s.items.forEach(function(it,i){
      const row=E('div',{class:'row',tabindex:'0',role:'button',
        style:'border:1px solid '+(i===at?'#F59E0B':'#E5E7EB')+';border-radius:10px;padding:5px 7px;'
          +'margin:3px 0;cursor:pointer;background:'+(i===at?'#FEF3C7':'#fff')});
      row.innerHTML=chips(it);
      const pick=function(){at=i; detail(
        (ordered?'Installation order ':'Selection ')+(i+1)+' of '+s.count,
        '<p>'+it.join(ordered?' → ':', ')+'</p>'
        +'<p class="small">'+(ordered
          ? 'The same buildings in another sequence are a different order.'
          : 'Rearranging these buildings does not make a new selection.')+'</p>');
        Array.prototype.forEach.call(list.children,function(el,j){
          el.style.background=j===i?'#FEF3C7':'#fff';
          el.style.borderColor=j===i?'#F59E0B':'#E5E7EB';
        });};
      row.addEventListener('mouseenter',pick);
      row.addEventListener('click',pick);
      row.addEventListener('focus',pick);
      row.addEventListener('keydown',function(e){
        if(e.key==='Enter'||e.key===' '){e.preventDefault();pick();}});
      list.appendChild(row);
    });
    if(s.items.length){
      at=Math.max(0,Math.min(at,s.items.length-1));
      const it=s.items[at];
      detail((ordered?'Installation order ':'Selection ')+(at+1)+' of '+s.count,
        '<p>'+it.join(ordered?' → ':', ')+'</p>');
    }
    if(s.truncated){
      list.appendChild(E('p',{class:'small'},
        'Showing the first '+s.items.length+' of '+s.count+'.'));
    }
  }
  lhead.textContent=title;
  counts.innerHTML='<h4>Counts for k = '+k+'</h4>'
    +'<p>choose, order ignored: <b>'+st.unordered.count+'</b><br>'
    +'<span class="small">'+st.unordered.formula+'</span></p>'
    +'<p>install in order: <b>'+st.ordered.count+'</b><br>'
    +'<span class="small">'+st.ordered.formula+'</span></p>'
    +'<p>with repetition, in order: <b>'+st.repeat.ordered.count+'</b><br>'
    +'<span class="small">'+st.repeat.ordered.formula+'</span></p>'
    +'<p>with repetition, unordered: <b>'+st.repeat.unordered.count+'</b><br>'
    +'<span class="small">'+st.repeat.unordered.formula+'</span></p>';
}
function stop(){if(timer){clearInterval(timer);timer=null;
  document.getElementById('play').textContent='▶ Play';}}
krange.addEventListener('input',function(){at=0;stop();render();});
bOrder.addEventListener('click',function(){ordered=!ordered;at=0;stop();render();});
bRepeat.addEventListener('click',function(){repeats=!repeats;at=0;stop();render();});
document.getElementById('reset').addEventListener('click',function(){stop();at=0;render();});
document.getElementById('step').addEventListener('click',function(){
  stop();
  const st=D.by_k[parseInt(krange.value,10)];
  const items=repeats?[]:(ordered?st.ordered.items:st.unordered.items);
  if(!items.length)return;
  at=(at+1)%items.length; render();
});
document.getElementById('play').addEventListener('click',function(e){
  if(timer){stop();return;}
  e.currentTarget.textContent='❚❚ Pause';
  timer=setInterval(function(){
    const st=D.by_k[parseInt(krange.value,10)];
    const items=repeats?[]:(ordered?st.ordered.items:st.unordered.items);
    if(!items.length){stop();return;}
    at=(at+1)%items.length; render();
  },800);
});
render();
"""
    return _doc(body, script)


# ===========================================================================
# 16 — Balls and bins (Counting)
# ===========================================================================

def balls_and_bins(data: dict) -> str:
    """Identical batches shared out, with the star-and-bar picture."""
    if not data.get("bins"):
        return _doc(_EMPTY, "")

    body = (
        '<p class="sub">The panel batches are identical, so only how many each '
        'building gets matters. Move the slider for the number of batches, then '
        'step through the star-and-bar pictures.</p>'
        '<div class="toolbar">'
        '<span class="small">batches: <b id="mval">' + str(data["m"])
        + '</b> of ' + str(data["max_m"]) + '</span>'
        '<input id="mrange" type="range" min="0" max="' + str(data["max_m"])
        + '" value="' + str(data["m"]) + '" step="1" style="flex:1 1 120px" '
        'aria-label="Number of panel batches">'
        '</div>'
        '<div class="toolbar">'
        '<button id="each" aria-pressed="false">every building gets at least one</button>'
        '</div>'
        '<div id="strip" class="mono" style="font-size:19px;letter-spacing:1px;'
        'background:#F0FDF4;border:1px solid #E5E7EB;border-radius:12px;'
        'padding:9px 10px;overflow-x:auto;white-space:nowrap" '
        'aria-label="Star and bar picture"></div>'
        '<div class="toolbar" style="margin-top:8px">'
        '<button id="prev" aria-label="Previous distribution">◀</button>'
        '<button id="play" aria-label="Play through the distributions">▶ Play</button>'
        '<button id="step" aria-label="Next distribution">Step ▸</button>'
        '<button id="reset" aria-label="Back to the first distribution">↺</button>'
        '<input id="irange" type="range" min="0" max="0" value="0" step="1" '
        'style="flex:1 1 100px" aria-label="Distribution">'
        '</div>'
        '<div class="two" style="align-items:start">'
        '<div class="panel" style="margin-top:0"><h4>This distribution</h4>'
        '<div id="dist" class="row">—</div></div>'
        '<div class="panel" style="margin-top:0"><h4>Counts</h4>'
        '<div id="counts"></div></div>'
        '</div>'
        '<div class="panel"><h4>Every distribution</h4>'
        '<div id="all" style="max-height:150px;overflow:auto"></div></div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
    )
    script = "const D=" + _json(data) + r"""
const mrange=document.getElementById('mrange');
const irange=document.getElementById('irange');
const strip=document.getElementById('strip');
const dist=document.getElementById('dist');
const counts=document.getElementById('counts');
const all=document.getElementById('all');
const eachBtn=document.getElementById('each');
let onlyEach=false, at=0, timer=null;
function state(){return D.by_m[parseInt(mrange.value,10)];}
function rowsOf(st){
  if(onlyEach) return st.at_least_one? st.at_least_one.distributions : null;
  return st.distributions;
}
function starBar(row){
  let out='';
  row.forEach(function(c,i){ if(i>0)out+='|'; out+='★'.repeat(c); });
  return out;
}
function countHtml(st){
  let h='<p>identical batches: <b>'+st.identical.count+'</b><br>'
    +'<span class="small">'+st.identical.formula+'</span></p>'
    +'<p>batches told apart: <b>'+st.distinguishable.count+'</b><br>'
    +'<span class="small">'+st.distinguishable.formula+'</span></p>';
  if(st.at_least_one){
    h+='<p>every building at least one: <b>'+st.at_least_one.count+'</b><br>'
      +'<span class="small">'+st.at_least_one.formula+'</span></p>';
  }else{
    h+='<p class="small">With fewer batches than buildings, at least one '
      +'building has to stay empty.</p>';
  }
  return h;
}
function stop(){if(timer){clearInterval(timer);timer=null;
  document.getElementById('play').textContent='▶ Play';}}
function render(){
  const m=parseInt(mrange.value,10);
  document.getElementById('mval').textContent=String(m);
  eachBtn.setAttribute('aria-pressed',onlyEach?'true':'false');
  const st=state();
  const rs=rowsOf(st);
  counts.innerHTML=countHtml(st);
  clear(all);
  if(rs===null){
    strip.textContent='';
    dist.innerHTML='<span class="chip amber">needs at least as many batches '
      +'as buildings</span>';
    irange.max='0'; irange.value='0';
    document.getElementById('play').disabled=true;
    document.getElementById('step').disabled=true;
    document.getElementById('prev').disabled=true;
    return;
  }
  if(!rs.length){
    strip.textContent='';
    dist.textContent='No distribution is listed for this many buildings.';
    irange.max='0'; irange.value='0';
    document.getElementById('play').disabled=true;
    document.getElementById('step').disabled=true;
    document.getElementById('prev').disabled=true;
    return;
  }
  at=Math.max(0,Math.min(at,rs.length-1));
  irange.max=String(rs.length-1);
  irange.value=String(at);
  strip.textContent=starBar(rs[at]);
  dist.innerHTML=rs[at].map(function(c,i){
    return D.bins[i].label+' gets '+c;}).join('<br>');
  document.getElementById('panel').innerHTML='<h4>Distribution '+(at+1)+' of '+rs.length
    +'</h4><p>'+starBar(rs[at])+'</p><p class="small">Identical batches: '
    +st.identical.count+' ways. Distinguishable panels: '
    +st.distinguishable.count+' ways.</p>';
  const cap=60;
  rs.slice(0,cap).forEach(function(row,i){
    const el=E('div',{class:'row',tabindex:'0',role:'button',
      style:'border:1px solid '+(i===at?'#F59E0B':'#E5E7EB')+';border-radius:9px;'
        +'padding:3px 7px;margin:2px 0;cursor:pointer;overflow-x:auto;'
        +'white-space:nowrap;background:'+(i===at?'#FEF3C7':'#fff')});
    el.textContent=starBar(row)+'   →  '+row.join(', ');
    el.addEventListener('click',function(){stop();at=i;render();});
    el.addEventListener('keydown',function(e){
      if(e.key==='Enter'||e.key===' '){e.preventDefault();stop();at=i;render();}});
    all.appendChild(el);
  });
  if(rs.length>cap){
    all.appendChild(E('p',{class:'small'},
      'Showing the first '+cap+' of '+rs.length+'.'));
  }
  document.getElementById('play').disabled=false;
  document.getElementById('step').disabled=at>=rs.length-1;
  document.getElementById('prev').disabled=at<=0;
}
mrange.addEventListener('input',function(){at=0;stop();render();});
irange.addEventListener('input',function(){stop();
  at=parseInt(irange.value,10);render();});
eachBtn.addEventListener('click',function(){onlyEach=!onlyEach;at=0;stop();render();});
document.getElementById('prev').addEventListener('click',function(){stop();at=Math.max(0,at-1);render();});
document.getElementById('step').addEventListener('click',function(){
  stop();at=Math.min(rowsOf(state()).length-1,at+1);render();});
document.getElementById('reset').addEventListener('click',function(){stop();at=0;render();});
document.getElementById('play').addEventListener('click',function(e){
  if(timer){stop();return;}
  const n=rowsOf(state()).length;
  if(at>=n-1)at=0;
  e.currentTarget.textContent='❚❚ Pause';
  timer=setInterval(function(){ if(at>=rowsOf(state()).length-1){stop();return;}
    at=at+1;render(); },900);
});
render();
"""
    return _doc(body, script)


# ===========================================================================
# 17 — Multinomial shift arrangements (Counting)
# ===========================================================================

def multinomial_arranger(data: dict) -> str:
    """Rearrangeable shift tiles plus the multinomial working."""
    if not data.get("sequence"):
        return _doc(_EMPTY, "")

    body = (
        '<p class="sub">A crew shift sequence is built from the same shifts over '
        'and over. Click a tile, then click another to swap them; move the shift '
        'slider to rotate the whole sequence.</p>'
        '<div class="toolbar">'
        '<button id="play" aria-label="Play the rotation">▶ Play</button>'
        '<button id="step" aria-label="Rotate once">Step ▸</button>'
        '<button id="reset" aria-label="Put the sequence back">↺ Reset</button>'
        '<label class="small" for="shift">shift</label>'
        '<input id="shift" type="range" min="0" max="' + str(max(1, data["total"] - 1))
        + '" value="0" step="1" style="flex:1 1 100px" aria-label="Rotation">'
        '</div>'
        '<div id="tiles" style="display:flex;flex-wrap:wrap;gap:6px"></div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
        '<div class="panel"><h4>Shifts in the sequence</h4><div id="types"></div></div>'
    )
    script = "const D=" + _json(data) + r"""
const tiles=document.getElementById('tiles');
const panel=document.getElementById('panel');
const shift=document.getElementById('shift');
const COLOURS=['#DCFCE7','#DBEAFE','#FEF3C7','#FDE68A','#FCE7F3','#E0E7FF'];
let base=D.sequence.slice(), picked=-1, timer=null;
function colourOf(label){
  for(let i=0;i<D.types.length;i++){ if(D.types[i].label===label)return COLOURS[i%COLOURS.length]; }
  return '#F3F4F6';
}
function rotate(arr,r){
  if(!arr.length)return arr.slice();
  const s=((r%arr.length)+arr.length)%arr.length;
  return arr.slice(s).concat(arr.slice(0,s));
}
function stop(){if(timer){clearInterval(timer);timer=null;
  document.getElementById('play').textContent='▶ Play';}}
function render(){
  const r=parseInt(shift.value,10);
  const shown=rotate(base,r);
  clear(tiles);
  shown.forEach(function(label,i){
    const t=E('div',{class:'tile',tabindex:'0',role:'button',
      'aria-label':'position '+(i+1)+', '+label,
      style:'width:auto;min-height:auto;padding:7px 12px;background:'
        +colourOf(label)+';border-color:'+(i===picked?'#F59E0B':'#E5E7EB')});
    t.appendChild(E('b',{},label));
    t.appendChild(E('div',{class:'small'},'position '+(i+1)));
    const pick=function(){
      if(picked<0){picked=i;
        panel.innerHTML='<h4>Tile '+(i+1)+' picked</h4><p>'+label
          +' — now click another tile to swap places with it.</p>';}
      else if(picked===i){picked=-1;
        panel.innerHTML='<h4>Tile '+(i+1)+' unpicked</h4>'
          +'<p>Click a tile and then another to swap them.</p>';}
      else{
        const a=Math.min(picked,i), b=Math.max(picked,i);
        const t0=base[a]; base[a]=base[b]; base[b]=t0;
        panel.innerHTML='<h4>Swapped positions '+(a+1)+' and '+(b+1)+'</h4>'
          +'<p>Every distinct sequence is counted once, so swapping two shifts '
          +'that are the same does not change the picture.</p>';
        picked=-1;
      }
      render();
    };
    t.addEventListener('click',pick);
    t.addEventListener('focus',function(){
      panel.innerHTML='<h4>Position '+(i+1)+'</h4><p>'+label+'</p>';});
    t.addEventListener('keydown',function(e){
      if(e.key==='Enter'||e.key===' '){e.preventDefault();pick();}});
    tiles.appendChild(t);
  });
}
document.getElementById('types').innerHTML=D.types.map(function(t){
  return '<p>'+t.label+' × <b>'+t.count+'</b></p>';}).join('')
  +'<p class="small">Distinct sequences: '+D.formula+'</p>';
shift.addEventListener('input',function(){picked=-1;render();});
document.getElementById('step').addEventListener('click',function(){
  stop();shift.value=String((parseInt(shift.value,10)+1)%(D.total||1));render();});
document.getElementById('reset').addEventListener('click',function(){
  stop();base=D.sequence.slice();picked=-1;shift.value='0';render();});
document.getElementById('play').addEventListener('click',function(e){
  if(timer){stop();return;}
  e.currentTarget.textContent='❚❚ Pause';
  timer=setInterval(function(){
    shift.value=String((parseInt(shift.value,10)+1)%(D.total||1));render();},800);
});
panel.innerHTML='<h4>Shift sequence</h4><p>Click a tile, then another, to '
  +'swap the two shifts; use the slider or Play to rotate the whole sequence.</p>';
render();
"""
    return _doc(body, script)


# ===========================================================================
# 18 — Pascal's triangle explorer (Counting)
# ===========================================================================

def pascal_explorer(data: dict) -> str:
    """Click any cell: its two parents light up and the mirror can be shown."""
    if not data.get("triangle"):
        return _doc(_EMPTY, "")

    checks = data.get("identity_checks") or {}
    check_html = ""
    for key in ("symmetry", "pascal_rule", "row_sum"):
        item = checks.get(key)
        if not item:
            continue
        holds = bool(item.get("holds"))
        check_html += (
            '<div class="row"><span class="chip ' + ("ok" if holds else "no") + '">'
            + ("holds" if holds else "fails") + "</span> "
            + str(item.get("statement", "")) + "</div>"
        )

    body = (
        '<p class="sub">Each number is built from the two numbers above it. Click '
        'or press Enter on any cell to see the two it came from; switch the mirror '
        'on to read C(n,k) as C(n,n−k).</p>'
        '<div class="toolbar">'
        '<button id="play" aria-label="Play through the cells">▶ Play</button>'
        '<button id="step" aria-label="Next cell">Step ▸</button>'
        '<button id="sym" aria-pressed="false">show the mirror pair</button>'
        '<button id="reset" aria-label="Back to the default cell">↺ Reset</button>'
        '<input id="cslider" type="range" min="0" max="'
        + str(sum(len(r) for r in data.get("triangle") or [[1]]) - 1)
        + '" value="0" step="1" style="flex:1 1 100px" aria-label="Cell">'
        '<span class="small">rows 0–' + str(data["rows"] - 1) + '</span>'
        '</div>'
        '<div id="tri" style="overflow-x:auto;padding:4px 0"></div>'
        '<div class="two" style="align-items:start">'
        '<div class="panel" style="margin-top:0"><h4 id="cellhead">Cell</h4>'
        '<div id="cell" class="row">—</div></div>'
        '<div class="panel" style="margin-top:0"><h4>Row sum</h4>'
        '<div id="rowsum"></div></div>'
        '</div>'
        '<div class="panel"><h4>Checked over the whole triangle</h4>'
        + (check_html or '<p class="small">No check reported.</p>') + '</div>'
    )
    script = "const D=" + _json(data) + r"""
const tri=document.getElementById('tri');
const refs=[];
let selN=D.selected.n, selK=D.selected.k, sym=false, timer=null;
function cellIndex(r,k){return r*(r+1)/2 + k;}
function fromIndex(idx){
  let r=0, left=idx;
  while(left>r){left-=(r+1); r+=1;}
  return [r, left];
}
D.triangle.forEach(function(row,r){
  const line=E('div',{style:'display:flex;justify-content:center;gap:4px;margin:2px 0'});
  const rowRefs=[];
  row.forEach(function(v,k){
    const cell=E('div',{class:'row',tabindex:'0',role:'button',
      'aria-label':'row '+r+', position '+k+', value '+v,
      style:'min-width:32px;text-align:center;border:1px solid #E5E7EB;'
        +'border-radius:9px;padding:4px 5px;cursor:pointer;font-size:12.5px;'
        +'background:#fff'});
    cell.textContent=String(v);
    cell.addEventListener('click',function(){select(r,k);});
    cell.addEventListener('focus',function(){select(r,k);});
    cell.addEventListener('keydown',function(e){
      if(e.key==='Enter'||e.key===' '){e.preventDefault();select(r,k);}});
    line.appendChild(cell); rowRefs.push(cell);
  });
  refs.push(rowRefs); tri.appendChild(line);
});
function select(r,k){selN=r; selK=k;
  document.getElementById('cslider').value=String(cellIndex(r,k));
  paint();}
function paint(){
  D.cells.forEach(function(row,r){ row.forEach(function(c,k){
    const el=refs[r][k];
    el.style.background='#fff'; el.style.borderColor='#E5E7EB';
    el.style.fontWeight='400';
  });});
  const c=D.cells[selN][selK];
  const me=refs[selN][selK];
  me.style.background='#FEF3C7'; me.style.borderColor='#F59E0B';
  me.style.fontWeight='700';
  if(c.has_parents){
    [[c.left_n,c.left_k],[c.right_n,c.right_k]].forEach(function(p){
      refs[p[0]][p[1]].style.background='#DCFCE7';
      refs[p[0]][p[1]].style.borderColor='#16A34A';
    });
  }
  if(sym){
    refs[c.n][c.mirror_k].style.background='#DBEAFE';
    refs[c.n][c.mirror_k].style.borderColor='#2563EB';
  }
  document.getElementById('cellhead').textContent='Row '+c.n+', position '+c.k;
  let h='<p><b>C('+c.n+','+c.k+') = '+c.value+'</b></p>';
  if(c.has_parents){
    h+='<p>C('+c.n+','+c.k+') = C('+c.left_n+','+c.left_k+') + C('
      +c.right_n+','+c.right_k+') = '+c.left_value+' + '+c.right_value+' = '
      +c.value+' <span class="chip '+(c.rule_holds?'ok':'no')+'">'
      +(c.rule_holds?'rule holds':'rule fails')+'</span></p>';
  }else{
    h+='<p class="small">An edge cell of the row: every row starts and ends '
      +'with 1.</p>';
  }
  if(sym){
    h+='<p>C('+c.n+','+c.k+') = C('+c.n+','+c.mirror_k+') = '+c.mirror_value+' '
      +'<span class="chip '+(c.symmetric_holds?'ok':'no')+'">'
      +(c.symmetric_holds?'mirror holds':'mirror fails')+'</span></p>';
  }
  document.getElementById('cell').innerHTML=h;
  const total=D.row_sums[c.n];
  let maxsum=0;
  D.row_sums.forEach(function(s){ if(s>maxsum)maxsum=s; });
  document.getElementById('rowsum').innerHTML='<p>Row '+c.n+' sums to <b>'
    +total+'</b></p><div class="bar" aria-hidden="true"><span style="width:'
    +Math.round(100*total/(maxsum||1))+'%"></span></div>'
    +'<p class="small">Row '+c.n+' has '+(c.n+1)+' cell(s) and sums to 2^'
    +c.n+' = '+total+'.</p>';
}
function stop(){if(timer){clearInterval(timer);timer=null;
  document.getElementById('play').textContent='▶ Play';}}
document.getElementById('sym').addEventListener('click',function(e){
  sym=!sym; e.currentTarget.setAttribute('aria-pressed',sym?'true':'false');
  paint();});
document.getElementById('reset').addEventListener('click',function(){
  stop(); sym=false;
  document.getElementById('sym').setAttribute('aria-pressed','false');
  select(D.selected.n,D.selected.k);});
document.getElementById('cslider').addEventListener('input',function(){
  stop(); const p=fromIndex(parseInt(this.value,10)); select(p[0],p[1]);});
document.getElementById('step').addEventListener('click',function(){
  stop(); const max=parseInt(document.getElementById('cslider').max,10);
  const next=(cellIndex(selN,selK)+1)%(max+1);
  const p=fromIndex(next); select(p[0],p[1]);});
document.getElementById('play').addEventListener('click',function(e){
  if(timer){stop();return;}
  e.currentTarget.textContent='❚❚ Pause';
  timer=setInterval(function(){
    const max=parseInt(document.getElementById('cslider').max,10);
    const next=(cellIndex(selN,selK)+1)%(max+1);
    const p=fromIndex(next); select(p[0],p[1]);
  },700);
});
paint();
"""
    return _doc(body, script)


# ===========================================================================
# 19 — Double counting board (Counting)
# ===========================================================================

def double_counting_board(data: dict) -> str:
    """Every building-to-connection line, counted from both sides."""
    if not data.get("lines"):
        return _doc(_EMPTY, "")

    body = (
        '<p class="sub">Every line joins one building to one connection. Play or '
        'step the lines through and watch the two totals grow together.</p>'
        '<div class="toolbar">'
        '<button id="play" aria-label="Play the lines">▶ Play</button>'
        '<button id="step" aria-label="Add one line">Step ▸</button>'
        '<button id="reset" aria-label="Clear the lines">↺ Reset</button>'
        '<input id="slider" type="range" min="0" max="' + str(len(data["lines"]))
        + '" value="0" step="1" style="flex:1 1 100px" aria-label="Lines shown">'
        '</div>'
        '<div class="two" style="align-items:start">'
        '<div><div class="title">Counted per building</div><div id="left"></div>'
        '<div class="panel" style="margin-top:8px"><h4>Total this side</h4>'
        '<div class="row"><b id="tb">0</b> of ' + str(data["tally_buildings"])
        + '</div></div></div>'
        '<div><div class="title">Counted per connection</div><div id="right"></div>'
        '<div class="panel" style="margin-top:8px"><h4>Total this side</h4>'
        '<div class="row"><b id="tc">0</b> of ' + str(data["tally_connections"])
        + '</div></div></div>'
        '</div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
    )
    script = "const D=" + _json(data) + r"""
const left=document.getElementById('left'), right=document.getElementById('right');
const slider=document.getElementById('slider');
const panel=document.getElementById('panel');
const lb={}, rb={};
let at=0, timer=null;
function row(label,counter){
  const el=E('div',{class:'row',style:'display:flex;justify-content:space-between;'
    +'gap:6px;padding:3px 0;border-bottom:1px solid #F3F4F6'});
  el.appendChild(E('span',{},label));
  el.appendChild(counter);
  return el;
}
D.buildings.forEach(function(b){
  const c=E('span',{class:'chip grey'},'0 of '+b.degree);
  lb[b.key]=c; left.appendChild(row(b.label,c));
});
D.connections.forEach(function(c){
  const s=E('span',{class:'chip grey'},'0 of '+c.endpoints);
  rb[c.key]=s; right.appendChild(row(c.label,s));
});
function stop(){if(timer){clearInterval(timer);timer=null;
  document.getElementById('play').textContent='▶ Play';}}
function render(){
  const count={}, ccount={};
  D.buildings.forEach(function(b){count[b.key]=0;});
  D.connections.forEach(function(c){ccount[c.key]=0;});
  D.lines.slice(0,at).forEach(function(l){
    count[l.building_key]+=1; ccount[l.connection_key]+=1;});
  let sumL=0;
  D.buildings.forEach(function(b){
    sumL+=count[b.key];
    lb[b.key].textContent=count[b.key]+' of '+b.degree;
    lb[b.key].className='chip '+(count[b.key]?'ok':'grey');
  });
  let sumR=0;
  D.connections.forEach(function(c){
    sumR+=ccount[c.key];
    rb[c.key].textContent=ccount[c.key]+' of '+c.endpoints;
    rb[c.key].className='chip '+(ccount[c.key]?'ok':'grey');
  });
  document.getElementById('tb').textContent=String(sumL);
  document.getElementById('tc').textContent=String(sumR);
  slider.value=String(at);
  const last=at>0? D.lines[at-1] : null;
  let h;
  if(!last){
    h='<h4>Nothing counted yet</h4><p>Press Step or Play to walk the lines.</p>';
  }else{
    h='<h4>'+last.building_label+' — '+last.connection_label+'</h4>'
      +'<p>This line adds one to the building count and one to the connection '
      +'count.</p>';
  }
  if(at>=D.lines.length){
    h+='<p><span class="chip '+(D.check?'ok':'no')+'">'
      +(D.check?'the two totals agree':'the totals differ')+'</span> '
      +'Each side reaches '+D.tally_buildings+' from '+D.vertex_count
      +' building(s) and '+D.edge_count+' connection(s).</p>';
  }
  panel.innerHTML=h;
  document.getElementById('step').disabled=at>=D.lines.length;
}
function setAt(v){at=Math.max(0,Math.min(D.lines.length,v));render();}
document.getElementById('step').addEventListener('click',function(){stop();setAt(at+1);});
document.getElementById('reset').addEventListener('click',function(){stop();setAt(0);});
slider.addEventListener('input',function(){stop();setAt(parseInt(slider.value,10));});
document.getElementById('play').addEventListener('click',function(e){
  if(timer){stop();return;}
  e.currentTarget.textContent='❚❚ Pause';
  if(at>=D.lines.length)setAt(0);
  timer=setInterval(function(){ if(at>=D.lines.length){stop();return;}
    setAt(at+1); },700);
});
render();
"""
    return _doc(body, script)


# ===========================================================================
# 20 — Combinatorial proof strip (Counting)
# ===========================================================================

def combinatorial_proof_strip(data: dict) -> str:
    """Install-or-skip tiles behind C(n,k) = C(n,n−k)."""
    if not data.get("buildings"):
        return _doc(_EMPTY, "")
    if not data.get("states_ready"):
        return _doc(
            '<div class="empty"><b>Too many buildings to toggle here.</b><br>'
            'This view shows every install-or-skip pattern, which needs at most '
            'ten eligible buildings.</div>', "")

    total = len(data["states"])
    start = (1 << data["k"]) - 1
    body = (
        '<p class="sub">Each building either gets panels or is left out. Toggle a '
        'building, or move the slider, and the same choice is read from both sides '
        'of the identity.</p>'
        '<div class="toolbar">'
        '<button id="play" aria-label="Play through the patterns">▶ Play</button>'
        '<button id="step" aria-label="Next pattern">Step ▸</button>'
        '<button id="reset" aria-label="Back to the first pattern">↺ Reset</button>'
        '<input id="mrange" type="range" min="0" max="' + str(total - 1)
        + '" value="' + str(start) + '" step="1" style="flex:1 1 100px" '
        'aria-label="Install or skip pattern">'
        '</div>'
        '<div id="tiles" style="display:flex;flex-wrap:wrap;gap:6px"></div>'
        '<div class="two" style="align-items:start">'
        '<div class="panel" style="margin-top:0"><h4>Get panels</h4>'
        '<div id="install" class="row">—</div></div>'
        '<div class="panel" style="margin-top:0"><h4>Left out</h4>'
        '<div id="skip" class="row">—</div></div>'
        '</div>'
        '<div id="panel" class="panel" role="status" aria-live="polite"></div>'
        '<div class="panel"><h4>The row of counts</h4><div id="row"></div></div>'
    )
    script = "const D=" + _json(data) + r"""
const tiles=document.getElementById('tiles');
const mrange=document.getElementById('mrange');
const install=document.getElementById('install');
const skip=document.getElementById('skip');
const panel=document.getElementById('panel');
const rowBox=document.getElementById('row');
let timer=null;
function chips(list,cls){
  if(!list.length)return '<span class="small">none</span>';
  return list.map(function(x){return '<span class="chip '+cls+'">'+x+'</span>';}).join(' ');
}
function stop(){if(timer){clearInterval(timer);timer=null;
  document.getElementById('play').textContent='▶ Play';}}
function render(){
  const m=parseInt(mrange.value,10);
  const st=D.states[m];
  if(!st)return;
  clear(tiles);
  D.buildings.forEach(function(b,i){
    const on=(m>>i)&1;
    const t=E('div',{class:'tile '+(on?'ok':'no'),tabindex:'0',role:'button',
      'aria-label':b.label+(on?' gets panels':' is left out'),
      style:'width:auto;min-height:auto;padding:7px 10px'});
    t.appendChild(E('b',{},b.label));
    t.appendChild(E('div',{class:'small'},on?'gets panels':'left out'));
    const flip=function(){
      stop(); mrange.value=String(m ^ (1<<i)); render();};
    t.addEventListener('click',flip);
    t.addEventListener('keydown',function(e){
      if(e.key==='Enter'||e.key===' '){e.preventDefault();flip();}});
    tiles.appendChild(t);
  });
  install.innerHTML=chips(st.install,'ok');
  skip.innerHTML=chips(st.skip,'grey');
  panel.innerHTML='<h4>k = '+st.k+'</h4>'
    +'<p>Choosing which '+st.k+' buildings get panels is the same as choosing '
    +'which '+(D.n-st.k)+' are left out.</p>'
    +'<p>C('+D.n+','+st.k+') = <b>'+st.left_count+'</b> and C('+D.n+','
    +(D.n-st.k)+') = <b>'+st.right_count+'</b> <span class="chip '
    +(st.equal?'ok':'no')+'">'+(st.equal?'the two sides agree':'the two sides differ')
    +'</span></p>'
    +'<p class="small">This pattern is selection '+st.position+' of '
    +st.left_count+'.</p>';
  rowBox.innerHTML=D.row.map(function(v,j){
    return '<span class="chip '+(j===st.k?'amber':'grey')+'">C('+D.n+','+j+') = '
      +v+'</span>';}).join(' ');
}
mrange.addEventListener('input',function(){stop();render();});
document.getElementById('step').addEventListener('click',function(){
  stop(); mrange.value=String((parseInt(mrange.value,10)+1)%D.states.length);
  render();});
document.getElementById('reset').addEventListener('click',function(){
  stop(); mrange.value=String((1<<D.k)-1); render();});
document.getElementById('play').addEventListener('click',function(e){
  if(timer){stop();return;}
  e.currentTarget.textContent='❚❚ Pause';
  timer=setInterval(function(){
    mrange.value=String((parseInt(mrange.value,10)+1)%D.states.length);
    render();},700);
});
render();
"""
    return _doc(body, script)

