"""Counting page: how many ways can the installation be planned?"""
from __future__ import annotations

import html
import json
from itertools import (combinations_with_replacement, islice, permutations,
                       product)

import streamlit as st
import streamlit.components.v1 as components

from algorithms import counting as cm
from algorithms.set_theory import build_sets, eligible_set
from algorithms.validation import COL_NAME
from components.style import page_header

LIMIT = 200

_CSS = """<style>
.chip{display:inline-block;padding:3px 10px;margin:2px;border-radius:999px;background:#DCFCE7;color:#14532D;border:1px solid #86EFAC;font-size:13px}
.combo{display:inline-block;padding:4px 6px;margin:3px;border-radius:10px;background:#fff;border:1px solid #D1D5DB}
.bar{color:#F59E0B;font-weight:700;margin:0 6px}
.stars{font-size:22px;letter-spacing:2px;color:#16A34A}
</style>"""

_PASCAL = """
<style>
body{font-family:system-ui,sans-serif;margin:0;color:#1F2937}
#tri{overflow-x:auto;padding-bottom:4px}
.row{display:flex;justify-content:center;gap:5px;margin:4px 0;min-width:max-content}
.cell{min-width:46px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:8px;background:#fff;border:1px solid #D1D5DB;cursor:pointer;font-size:13px}
.cell:hover{border-color:#16A34A}
.sel{background:#16A34A;color:#fff;border-color:#14532D}
.par{background:#FDE68A;border-color:#F59E0B}
.mir{border:2px dashed #14532D}
#panel{margin-top:8px;padding:10px 12px;background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;font-size:14px}
#track{height:10px;background:#E5E7EB;border-radius:6px;margin-top:8px}
#fill{height:10px;background:#16A34A;border-radius:6px;width:0}
</style>
<div id="tri"></div><div id="panel"></div><div id="track"><div id="fill"></div></div>
<script>
const ROWS = __ROWS__;
let sel = [5, 2];
function draw(){
  const tri = document.getElementById('tri');
  tri.innerHTML = '';
  ROWS.forEach((r, n) => {
    const row = document.createElement('div'); row.className = 'row';
    r.forEach((v, k) => {
      const c = document.createElement('div'); c.className = 'cell'; c.textContent = v;
      c.tabIndex = 0;
      if (n === sel[0] && k === sel[1]) c.classList.add('sel');
      else if (n === sel[0] - 1 && (k === sel[1] - 1 || k === sel[1])) c.classList.add('par');
      else if (n === sel[0] && k === sel[0] - sel[1]) c.classList.add('mir');
      const pick = () => { sel = [n, k]; draw(); };
      c.onclick = pick;
      c.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') pick(); };
      row.appendChild(c);
    });
    tri.appendChild(row);
  });
  const n = sel[0], k = sel[1], v = ROWS[n][k], total = Math.pow(2, n);
  let t = 'C(' + n + ',' + k + ') = ' + v + '. ';
  if (k === 0 || k === n) t += 'The edge of the triangle is always 1.';
  else t += 'C(' + n + ',' + k + ') = C(' + (n-1) + ',' + (k-1) + ') + C(' + (n-1) + ',' + k + ') = ' + ROWS[n-1][k-1] + ' + ' + ROWS[n-1][k] + '.';
  t += ' Mirror: C(' + n + ',' + (n-k) + ') = ' + ROWS[n][n-k] + '. Row ' + n + ' adds up to 2^' + n + ' = ' + total + '.';
  document.getElementById('panel').textContent = t;
  document.getElementById('fill').style.width = (total / Math.pow(2, ROWS.length - 1) * 100) + '%';
}
draw();
</script>
"""




def _js(obj) -> str:
    return json.dumps(obj).replace("</", "<\\/")


def _chips(items) -> str:
    return "".join(f"<span class='chip'>{html.escape(str(i))}</span>" for i in items)


def _combo(items) -> str:
    return f"<div class='combo'>{_chips(items) or '∅'}</div>"


def _load():
    df = st.session_state.get("buildings")
    thresholds = st.session_state.get("thresholds")
    edges = st.session_state.get("edges") or []
    if df is None or len(df) == 0:
        return None
    sets = build_sets(df, thresholds)
    eligible = sorted(eligible_set(sets["A"], sets["B"], sets["C"]))
    names = sorted(str(n) for n in df[COL_NAME])
    pairs = []
    for e in edges:
        u, v = str(e[0]), str(e[1])
        if u in names and v in names and u != v:
            key = (u, v) if u < v else (v, u)
            if key not in pairs:
                pairs.append(key)
    return names, eligible, sorted(pairs)


def _selection(eligible):
    st.subheader("1. Choosing buildings")
    n = len(eligible)
    st.markdown("Eligible buildings: " + _chips(eligible), unsafe_allow_html=True)
    if n == 0:
        st.info("No building is eligible with the current thresholds, so there is nothing to choose from.")
        return
    c1, c2, c3 = st.columns(3)
    k = int(c1.number_input("How many to pick (k)", 0, 12, min(2, n), key="cnt_k"))
    order = c2.toggle("Order matters", key="cnt_order")
    repeat = c3.toggle("A building may repeat", key="cnt_repeat")
    if repeat:
        info = cm.permutations_with_repetition(n, k) if order else cm.combinations_with_repetition(n, k)
        source = product(eligible, repeat=k) if order else combinations_with_replacement(eligible, k)
        rows = list(islice(source, LIMIT))
    else:
        info = cm.permutations(n, k) if order else cm.combinations(n, k)
        if k > n:
            st.info("You cannot pick more buildings than there are without repeating one.")
            return
        listing = cm.list_selections(n, k, ordered=order, labels=eligible)
        if listing["errors"]:
            st.error(" ".join(listing["errors"]))
            return
        rows = listing["items"][:LIMIT]
    if info["errors"]:
        st.error(" ".join(info["errors"]))
        return
    st.metric("Number of ways", info["value"])
    st.code(info["formula"], language=None)
    st.markdown("".join(_combo(r) for r in rows), unsafe_allow_html=True)
    if info["value"] > len(rows):
        st.caption(f"Showing the first {len(rows)} of {info['value']}.")


def _balls(eligible):
    st.subheader("2. Sharing panel batches between buildings")
    c1, c2, c3 = st.columns(3)
    m = int(c1.number_input("Identical panel batches (m)", 0, 15, 5, key="cnt_m"))
    n = int(c2.number_input("Buildings (n)", 1, 6, min(max(len(eligible), 1), 6), key="cnt_nb"))
    least = c3.toggle("Every building gets at least one", key="cnt_least")
    bins = list(eligible) if n == len(eligible) else [f"Building {i + 1}" for i in range(n)]
    res = cm.stars_and_bars_distributions(m, n, 1 if least else 0, labels=bins)
    if res["errors"]:
        st.info(" ".join(res["errors"]))
        return
    distinct = cm.permutations_with_repetition(n, m)["value"]
    a, b = st.columns(2)
    a.metric("Identical batches", res["count"])
    b.metric("Different panels (each one unique)", distinct)
    remaining = m - (n if least else 0)
    st.latex(rf"\binom{{{remaining} + {n} - 1}}{{{n} - 1}} = {res['count']}")
    rows = res["distributions"]
    if rows:
        idx = int(st.number_input("Show distribution number", 1, len(rows), 1, key="cnt_idx"))
        d = rows[idx - 1]
        strip = '<span class="bar">|</span>'.join(
            '<span class="stars">' + ("★" * x if x else "·") + "</span>" for x in d)
        st.markdown(f"<div>{strip}</div>", unsafe_allow_html=True)
        st.caption(", ".join(f"{res['bins'][i]}: {x}" for i, x in enumerate(d)))


def _arrangements():
    st.subheader("3. Crew shifts with repeated types")
    c1, c2, c3 = st.columns(3)
    day = int(c1.number_input("Day shifts", 0, 6, 2, key="cnt_day"))
    night = int(c2.number_input("Night shifts", 0, 6, 2, key="cnt_night"))
    standby = int(c3.number_input("Standby shifts", 0, 6, 1, key="cnt_standby"))
    counts = {"Day": day, "Night": night, "Standby": standby}
    if day + night + standby == 0:
        st.info("Add at least one shift.")
        return
    res = cm.multinomial(list(counts.values()))
    if res["errors"]:
        st.error(" ".join(res["errors"]))
        return
    st.metric("Different sequences", res["value"])
    st.code(res["formula"], language=None)
    tokens = []
    for name, c in counts.items():
        tokens += [name] * c
    if len(tokens) > 8:
        st.caption("Sequences are listed only for 8 shifts or fewer.")
        return
    arrangements = sorted(set(permutations(tokens)))
    idx = int(st.number_input("Show sequence number", 1, len(arrangements), 1, key="cnt_arr"))
    st.markdown(_chips(arrangements[idx - 1]), unsafe_allow_html=True)


def _pascal():
    st.subheader("4. Pascal's triangle")
    st.caption("Click a cell: the amber cells add up to it, the dashed cell is its mirror.")
    tri = cm.pascal_triangle(13)
    if tri["errors"]:
        st.error(" ".join(tri["errors"]))
        return
    page = _PASCAL.replace("__ROWS__", _js(tri["triangle"]))
    components.html(page, height=600, scrolling=True)



def _proof_strip(eligible):
    st.subheader("5. Two ways to count the same choices")
    n = len(eligible)
    if n < 2:
        st.info("This needs at least two eligible buildings.")
        return
    chosen = st.multiselect("Buildings to install first", eligible,
                            default=eligible[:max(1, n // 2)], key="cnt_proof")
    skipped = [b for b in eligible if b not in chosen]
    k = len(chosen)
    st.markdown("Install: " + (_chips(chosen) or "∅") + "<br>Skip: " + (_chips(skipped) or "∅"),
                unsafe_allow_html=True)
    value = cm.combinations(n, k)["value"]
    st.latex(rf"\binom{{{n}}}{{{k}}} = \binom{{{n}}}{{{n - k}}} = {value}")
    st.caption("Naming the k buildings to install automatically names the n − k to skip, "
               "so both counts list exactly the same selections.")


def _how_it_works():
    with st.expander("How it works"):
        st.markdown(
            "**Combination:** choose k buildings when order does not matter, C(n,k) = n! / (k!(n−k)!).\n\n"
            "**Permutation:** choose k buildings in an installation order, P(n,k) = n! / (n−k)!.\n\n"
            "**With repetition:** a building can be used again: n^k ordered, C(n+k−1, k) unordered.\n\n"
            "**Stars and bars:** m identical batches between n buildings can be shared in C(m+n−1, n−1) ways.\n\n"
            "**Repeated types:** a sequence with counts a, b, c of three shift types can be arranged in "
            "(a+b+c)! / (a! b! c!) ways.\n\n"
            "**Pascal's rule:** C(n,k) = C(n−1,k−1) + C(n−1,k), and row n adds up to 2^n.\n\n"
            "**Double counting:** counting (building, connection) pairs per building or per connection "
            "gives the same total."
        )


def render_counting_page() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    page_header(
       "How many ways can the installation be planned?",
       "Counting rules turn the list of eligible buildings into the number of possible "
       "selections, installation orders and crew schedules.",
   )
    data = _load()
    if data is None:
        st.info("Add buildings on Campus Data to start counting.")
        return
    names, eligible, pairs = data
    _selection(eligible)
    _balls(eligible)
    _arrangements()
    _pascal()
    _proof_strip(eligible)
    _how_it_works()