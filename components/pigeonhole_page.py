"""Pigeonhole page: why must some crew or band get several buildings?"""
from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from algorithms import pigeonhole_math as pm
from algorithms.validation import COL_DEMAND, COL_NAME, COL_SOLAR
from components.style import page_header

_HOLES = """
<style>
body{font-family:system-ui,sans-serif;margin:0;color:#1F2937}
#holes{display:flex;gap:10px;flex-wrap:wrap}
.hole{flex:1;min-width:120px;border:2px solid #D1D5DB;border-radius:14px;padding:8px;background:#fff;cursor:pointer}
.hole.full{border-color:#F59E0B;background:#FFFBEB}
.hole.sel{outline:3px solid #16A34A}
.hole h4{margin:0 0 6px;font-size:13px;color:#14532D}
.pigeon{display:inline-block;margin:2px;padding:3px 9px;border-radius:999px;background:#DCFCE7;border:1px solid #86EFAC;font-size:12px}
.count{float:right;font-weight:700}
#panel{margin-top:10px;padding:10px 12px;background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;font-size:14px}
</style>
<div id="holes"></div><div id="panel"></div>
<script>
const D = __DATA__;
const holes = document.getElementById('holes');
const panel = document.getElementById('panel');
panel.textContent = D.n + ' buildings in ' + D.m + ' holes: some hole must hold at least ' + D.min + '. Tap a hole to inspect it.';
D.holes.forEach((h, i) => {
  const box = document.createElement('div');
  box.className = 'hole' + (i === D.fullest ? ' full' : '');
  box.tabIndex = 0;
  const title = document.createElement('h4');
  title.textContent = h.name;
  const cnt = document.createElement('span');
  cnt.className = 'count';
  cnt.textContent = h.items.length;
  title.appendChild(cnt);
  box.appendChild(title);
  h.items.forEach(nm => {
    const p = document.createElement('span');
    p.className = 'pigeon';
    p.textContent = nm;
    box.appendChild(p);
  });
  const show = () => {
    document.querySelectorAll('.hole').forEach(x => x.classList.remove('sel'));
    box.classList.add('sel');
    let t = h.name + ' holds ' + h.items.length + ' building(s)';
    t += h.items.length ? ': ' + h.items.join(', ') + '.' : '.';
    if (i === D.fullest) t += ' This is the fullest hole, with at least the guaranteed ' + D.min + '.';
    else if (h.items.length < D.min) t += ' Fewer than ' + D.min + ' is fine here: the guarantee is only about the fullest hole.';
    panel.textContent = t;
  };
  box.onclick = show;
  box.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') show(); };
  holes.appendChild(box);
});
</script>
"""

_RING = """
<style>
body{font-family:system-ui,sans-serif;margin:0;color:#1F2937}
#panel{margin-top:6px;padding:10px 12px;background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;font-size:14px}
svg text{font-size:11px}
</style>
<svg id="svg" width="100%" viewBox="0 0 480 390"></svg>
<div id="panel"></div>
<script>
const D = __DATA__;
const NS = 'http://www.w3.org/2000/svg';
const svg = document.getElementById('svg');
const panel = document.getElementById('panel');
panel.textContent = D.intro;
function el(tag, attrs) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; }
const n = D.nodes.length, cx = 240, cy = 190, r = 135;
const pos = D.nodes.map((_, i) => {
  const ang = -Math.PI / 2 + 2 * Math.PI * i / n;
  return [cx + r * Math.cos(ang), cy + r * Math.sin(ang), Math.cos(ang)];
});
const hl = new Set(D.hl);
D.edges.forEach(e => {
  const hot = hl.has(e.a) && hl.has(e.b);
  const ln = el('line', {
    x1: pos[e.a][0], y1: pos[e.a][1], x2: pos[e.b][0], y2: pos[e.b][1],
    stroke: hot ? '#F59E0B' : (e.on ? '#16A34A' : '#DC2626'),
    'stroke-width': hot ? 5 : (e.on ? 2.5 : 1.5),
    'stroke-dasharray': e.on ? 'none' : '5 4',
    opacity: e.on ? 1 : 0.7
  });
  const say = () => { panel.textContent = D.nodes[e.a] + ' – ' + D.nodes[e.b] + ': ' + (e.on ? D.onText : D.offText) + '.'; };
  ln.onclick = say;
  ln.onmouseover = say;
  svg.appendChild(ln);
});
D.nodes.forEach((name, i) => {
  const c = el('circle', { cx: pos[i][0], cy: pos[i][1], r: 9, fill: hl.has(i) ? '#FDE68A' : '#fff', stroke: '#14532D', 'stroke-width': 2, tabindex: 0 });
  const side = pos[i][2];
  const t = el('text', {
    x: pos[i][0] + side * 16, y: pos[i][1] + 4,
    'text-anchor': side > 0.3 ? 'start' : (side < -0.3 ? 'end' : 'middle'),
    fill: '#14532D'
  });
  t.textContent = name;
  const say = () => {
    let deg = 0;
    D.edges.forEach(e => { if (e.on && (e.a === i || e.b === i)) deg++; });
    panel.textContent = name + ' has ' + deg + ' ' + D.noun + '.';
  };
  c.onclick = say;
  c.onmouseover = say;
  c.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') say(); };
  svg.appendChild(c);
  svg.appendChild(t);
});
</script>
"""

_BARS = """
<style>
body{font-family:system-ui,sans-serif;margin:0;color:#1F2937}
#bars{display:flex;align-items:flex-end;gap:8px;height:220px;padding-bottom:4px}
.col{flex:1;min-width:46px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;cursor:pointer}
.bar{width:100%;border-radius:8px 8px 0 0;background:#D1D5DB}
.inc{background:#16A34A}
.dec{background:#F59E0B}
.both{background:linear-gradient(#16A34A 50%,#F59E0B 50%)}
.v{font-size:12px;font-weight:700}
.nm{font-size:11px;text-align:center;word-break:break-word}
#panel{margin-top:8px;padding:10px 12px;background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;font-size:14px}
</style>
<div id="bars"></div><div id="panel"></div>
<script>
const D = __DATA__;
const bars = document.getElementById('bars');
const panel = document.getElementById('panel');
panel.textContent = D.summary;
const mx = Math.max(1, ...D.values);
D.names.forEach((nm, i) => {
  const col = document.createElement('div');
  col.className = 'col';
  col.tabIndex = 0;
  const v = document.createElement('div');
  v.className = 'v';
  v.textContent = D.values[i];
  const b = document.createElement('div');
  const ii = D.inc.includes(i), dd = D.dec.includes(i);
  b.className = 'bar ' + (ii && dd ? 'both' : ii ? 'inc' : dd ? 'dec' : '');
  b.style.height = Math.max(6, 170 * D.values[i] / mx) + 'px';
  const label = document.createElement('div');
  label.className = 'nm';
  label.textContent = nm;
  col.appendChild(v);
  col.appendChild(b);
  col.appendChild(label);
  const say = () => {
    let t = nm + ': ' + D.values[i] + '.';
    if (ii) t += ' It is part of the longest rising run (green).';
    if (dd) t += ' It is part of the longest falling run (amber).';
    if (!ii && !dd) t += ' It is not in either longest run.';
    panel.textContent = t;
  };
  col.onclick = say;
  col.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') say(); };
  bars.appendChild(col);
});
</script>
"""


def _js(obj) -> str:
    return json.dumps(obj).replace("</", "<\\/")


@st.cache_data(show_spinner=False)
def _scan(n: int) -> dict:
    return pm.ramsey_scan(n)


def _pairs(names, edges):
    out = []
    for e in edges:
        u, v = str(e[0]), str(e[1])
        if u in names and v in names and u != v:
            key = (u, v) if u < v else (v, u)
            if key not in out:
                out.append(key)
    return sorted(out)


def _ring(nodes, edge_list, hl, intro, on_text, off_text, noun):
    return {"nodes": nodes,
            "edges": [{"a": a, "b": b, "on": on} for a, b, on in edge_list],
            "hl": list(hl), "intro": intro, "onText": on_text,
            "offText": off_text, "noun": noun}


def _holes_section(names, solars):
    st.subheader("1. Pigeons and holes")
    n = len(names)
    mode = st.radio("Sort the buildings into", ["Solar-potential bands", "Crews (I choose)"],
                    horizontal=True, key="pg_mode")
    m = int(st.number_input("Number of holes", 1, 12, 4, key="pg_m"))
    if mode == "Solar-potential bands":
        idx = pm.solar_bands(solars, m)
        width = 100 / m
        labels = [f"{round(i * width, 1):g}–{round((i + 1) * width, 1):g}%" for i in range(m)]
    else:
        idx = []
        cols = st.columns(3)
        for i, name in enumerate(names):
            choice = cols[i % 3].selectbox(name, list(range(1, m + 1)), index=i % m,
                                           key=f"pg_crew_{i}_{m}",
                                           format_func=lambda c: f"Crew {c}")
            idx.append(choice - 1)
        labels = [f"Crew {i + 1}" for i in range(m)]
    contents = pm.hole_contents(names, idx, m)
    g = pm.pigeonhole_min(n, m)
    data = {"holes": [{"name": labels[i], "items": contents[i]} for i in range(m)],
            "min": g, "n": n, "m": m, "fullest": pm.fullest(contents)}
    st.latex(rf"\left\lceil \frac{{{n}}}{{{m}}} \right\rceil = {g}")
    biggest = max(len(c) for c in contents)
    a, b = st.columns(2)
    a.metric("Guaranteed in the fullest hole (at least)", g)
    b.metric("Actually in the fullest hole", biggest)
    if n > m:
        st.caption(f"Because {n} buildings go into only {m} holes, some hole must hold at least {g}.")
    else:
        st.caption("With no more buildings than holes, every hole can hold at most one, so no repeat is forced.")
    components.html(_HOLES.replace("__DATA__", _js(data)), height=340, scrolling=True)


def _ramsey_section(names_sorted, pairs):
    st.subheader("2. Ramsey: among six buildings, a trio always stands out")
    st.caption("Colour every pair of buildings: connected, or not connected. "
               "With six buildings, some three are always all connected or all not connected.")
    mode = st.radio("Show", ["Five buildings", "Six buildings"], horizontal=True, key="pg_ramsey")
    if mode == "Five buildings":
        res = _scan(5)
        nodes = ["A", "B", "C", "D", "E"]
        colour = res["example"]
        tri = pm.mono_triple(5, colour)
        edge_list = [(a, b, bool(c)) for (a, b), c in colour.items()]
        data = _ring(nodes, edge_list, tri or [],
                     "One way to colour five buildings with no single-colour trio. Tap a line or a building.",
                     "green", "red", "green connection(s)")
        st.metric("Colourings with no single-colour trio", f"{res['free']:,} of {res['total']:,}")
        st.caption("Five buildings can avoid a single-colour trio.")
    else:
        if len(names_sorted) < 6:
            st.info("This needs at least six buildings on Campus Data.")
            return
        nodes = names_sorted[:6]
        colour = pm.campus_colouring(nodes, pairs)
        res = _scan(6)
        tri = pm.mono_triple(6, colour)
        edge_list = [(a, b, bool(c)) for (a, b), c in colour.items()]
        if tri:
            kind = "all connected" if colour[(tri[0], tri[1])] else "none connected"
            msg = f"Trio found: {', '.join(nodes[i] for i in tri)} ({kind})."
        else:
            msg = "No single-colour trio found."
        data = _ring(nodes, edge_list, tri or [], msg,
                     "can be connected", "cannot be connected", "possible connection(s)")
        st.metric("Colourings with no single-colour trio", f"{res['free']:,} of {res['total']:,}")
        st.caption(msg + " Every one of the colourings was checked, and none avoids a trio.")
        if len(names_sorted) > 6:
            st.caption("Using the first six buildings in alphabetical order.")
    components.html(_RING.replace("__DATA__", _js(data)), height=470, scrolling=True)


def _mantel_section(names_sorted, pairs):
    st.subheader("3. Mantel: how many connections can avoid a triangle?")
    n = len(names_sorted)
    if not pairs:
        st.info("Add possible connections on Campus Data to see this.")
        return
    labels = [f"{u} – {v}" for u, v in pairs]
    chosen = st.multiselect("Connections kept", labels, default=labels, key="pg_mantel")
    kept = [pairs[labels.index(label)] for label in chosen]
    tris = pm.find_triangles(names_sorted, kept)
    bound = pm.mantel_bound(n)
    c1, c2, c3 = st.columns(3)
    c1.metric("Connections kept", len(kept))
    c2.metric(f"Mantel bound for {n} buildings", bound)
    c3.metric("Triangles", len(tris))
    st.latex(rf"\left\lfloor \frac{{{n}^2}}{{4}} \right\rfloor = {bound}")
    if tris:
        st.warning("Triangle: " + ", ".join(tris[0]) + ". Remove one of its connections to break it.")
    else:
        st.success(f"Triangle-free with {len(kept)} connection(s), within the bound of {bound}.")
    if len(kept) > bound:
        st.info(f"More than {bound} connections among {n} buildings forces a triangle.")
    left, right, ext = pm.complete_bipartite(names_sorted)
    st.caption(f"Most connections without a triangle: split the buildings into {len(left)} and "
               f"{len(right)} and join every left building to every right building: {len(ext)} connections.")
    idx = {name: i for i, name in enumerate(names_sorted)}
    edge_list = [(idx[u], idx[v], True) for u, v in kept]
    hl = [idx[x] for x in tris[0]] if tris else []
    intro = ("Triangle highlighted in amber." if tris else "No triangle among the kept connections.")
    data = _ring(names_sorted, edge_list, hl, intro, "kept", "removed", "kept connection(s)")
    components.html(_RING.replace("__DATA__", _js(data)), height=470, scrolling=True)


def _es_section(df):
    st.subheader("4. Erdős–Szekeres: a long run always appears")
    names = [str(x) for x in df[COL_NAME]]
    demands = [float(x) for x in df[COL_DEMAND]]
    max_n = min(len(names), 12)
    n = int(st.number_input("Buildings taken in data order", 1, max_n, min(5, max_n), key="pg_es_n"))
    seq, nm = demands[:n], names[:n]
    runs = pm.longest_monotone(seq)
    inc, dec = runs["increasing"], runs["decreasing"]
    longest = max(len(inc), len(dec))
    k = pm.es_k(n)
    g = pm.es_guarantee(n)
    a, b = st.columns(2)
    a.metric("Longest rising or falling run", longest)
    b.metric("Guaranteed at least", g)
    st.latex(rf"{n} \ge {k}^2 + 1 \;\Rightarrow\; \text{{a run of at least }} {k} + 1 = {g}")
    if len(set(seq)) != len(seq):
        st.warning("Two buildings share the same demand. The guarantee is stated for different numbers, so a run can be shorter here.")
    summary = ("Rising run (green): " + ", ".join(nm[i] for i in inc)
               + ". Falling run (amber): " + ", ".join(nm[i] for i in dec) + ".")
    data = {"names": nm, "values": [int(v) if v == int(v) else v for v in seq],
            "inc": inc, "dec": dec, "summary": summary}
    components.html(_BARS.replace("__DATA__", _js(data)), height=330, scrolling=True)
    st.caption("Turán's theorem (statement only): a graph on n vertices with no group of r + 1 mutually "
               "connected vertices has at most (1 − 1/r)·n²/2 connections. Mantel is the case r = 2.")


def _how_it_works():
    with st.expander("How it works"):
        st.markdown(
            "**Pigeonhole principle:** n buildings in m holes with n > m means some hole holds at least 2.\n\n"
            "**Generalized form:** some hole holds at least ⌈n/m⌉ buildings.\n\n"
            "**Ramsey R(3,3) = 6:** colour every pair of six buildings with one of two colours and a "
            "single-colour trio always appears; five buildings can avoid it.\n\n"
            "**Mantel:** a graph with no triangle on n vertices has at most ⌊n²/4⌋ edges.\n\n"
            "**Erdős–Szekeres:** any k² + 1 different numbers contain a rising or falling run of at least k + 1."
        )


def render_pigeonhole_page() -> None:
    page_header(
        "Why must some crew or band get several buildings?",
        "When more buildings than groups must be sorted, something has to double up. "
        "The same idea shows up in connections and in demand patterns.",
    )
    df = st.session_state.get("buildings")
    edges = st.session_state.get("edges") or []
    if df is None or len(df) == 0:
        st.info("Add buildings on Campus Data to start.")
        return
    names = [str(x) for x in df[COL_NAME]]
    solars = [float(x) for x in df[COL_SOLAR]]
    names_sorted = sorted(names)
    pairs = _pairs(names_sorted, edges)
    try:
        _holes_section(names, solars)
        _ramsey_section(names_sorted, pairs)
        _mantel_section(names_sorted, pairs)
        _es_section(df)
    except ValueError as err:
        st.error(str(err))
        return
    _how_it_works()