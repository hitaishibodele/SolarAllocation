"""Tabs for the Graph Theory page. All logic comes from algorithms/."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from algorithms import graph_extra as gx
from algorithms.graph_algorithms import (
    adjacency_list, bipartite_check, euler_check, graph_colouring, incidence_matrix,
    max_matching, planarity_bound_check, tree_check,
)
from algorithms.network import connected_components, has_cycle
from components.graph_draw import COLOUR_NAMES, draw_graph, two_column_positions
from components.style import AMBER, DANGER, GREEN, callout, kpi_row, math_box, section_card, section_title

_PRESETS = {
    "Triangle (K₃)": (["A", "B", "C"], [("A", "B"), ("B", "C"), ("A", "C")]),
    "Triangle with a tail": (["A", "B", "C", "D"], [("A", "B"), ("B", "C"), ("A", "C"), ("C", "D")]),
    "4-cycle (C₄)": (["A", "B", "C", "D"], [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")]),
    "Complete K₄": (list("ABCD"), [(u, v) for i, u in enumerate("ABCD") for v in "ABCD"[i + 1:]]),
    "Complete K₅": (list("ABCDE"), [(u, v) for i, u in enumerate("ABCDE") for v in "ABCDE"[i + 1:]]),
    "Complete bipartite K₃,₃": (list("ABCXYZ"), [(u, v) for u in "ABC" for v in "XYZ"]),
    "Path (P₄)": (list("ABCD"), [("A", "B"), ("B", "C"), ("C", "D")]),
    "Star (K₁,₃)": (list("CABD"), [("C", "A"), ("C", "B"), ("C", "D")]),
    "Disconnected (2 + 2)": (list("ABCD"), [("A", "B"), ("C", "D")]),
    "Single vertex": (["A"], []),
}


def _show(fig) -> None:
    st.pyplot(fig)
    plt.close(fig)


def _degrees(vertices, und):
    d = {v: 0 for v in vertices}
    for u, v in und:
        d[u] += 1
        d[v] += 1
    return d


def _pairs(seq):
    return {frozenset(p) for p in zip(seq, seq[1:])}


def _ready(G) -> bool:
    if not G["ok"]:
        callout(G["reason"], "info")
    return G["ok"]


def _mark(flag) -> str:
    return "✓" if flag else "✗"


# ---------------------------------------------------------------- source ----

def _load_preset() -> None:
    p = _PRESETS.get(st.session_state.get("gt_preset"))
    if p:
        st.session_state["gt_v"] = ", ".join(p[0])
        st.session_state["gt_e"] = "\n".join(f"{u},{v}" for u, v in p[1])


def _graph_label(parsed, directed: bool) -> str:
    if not directed:
        vertices = set(parsed["vertices"])
        edges = {frozenset(edge) for edge in parsed["und"]}
        for name, (preset_vertices, preset_edges) in _PRESETS.items():
            if vertices == set(preset_vertices) and edges == {frozenset(edge) for edge in preset_edges}:
                return name
    return "Custom directed graph" if directed else "Custom graph"


def graph_source(c_vertices, c_edges) -> dict:
    src = st.radio("Graph to analyse (used by every tab except Campus Graph and Matching)",
                   ["Campus graph", "Custom graph"], horizontal=True, key="gt_source")
    if src == "Campus graph":
        ok = len(c_vertices) > 0
        return {"source": src, "label": "Campus graph", "vertices": list(c_vertices), "edges": list(c_edges),
                "und": list(c_edges), "directed": False, "ok": ok,
                "reason": "No building is eligible. Change thresholds on Sets, or choose Custom graph."}
    if "gt_v" not in st.session_state:
        st.session_state["gt_preset"] = "Triangle (K₃)"
        _load_preset()
    with st.container(border=True):
        st.selectbox("Example", list(_PRESETS), key="gt_preset", on_change=_load_preset)
        c1, c2 = st.columns(2)
        v_text = c1.text_input("Vertices (comma-separated, at most 8)", key="gt_v")
        directed = c1.checkbox("Directed graph", key="gt_dir")
        e_text = c2.text_area("Edges (u,v one per line)", key="gt_e", height=130)
        P = gx.parse_graph(v_text, e_text, directed)
    for w in P["warnings"]:
        callout(w, "warning")
    if P["errors"]:
        for e in P["errors"]:
            callout(e, "error")
        return {"source": src, "label": "Custom graph", "vertices": [], "edges": [], "und": [], "directed": directed,
                "ok": False, "reason": "Fix the custom graph above to continue."}
    label = _graph_label(P, directed)
    st.caption(
        f"Analyzing **{label}**: {len(P['vertices'])} vertices, {len(P['edges'])} edges. "
        "Campus Graph is hidden; Matching uses a separate graph."
    )
    return {"source": src, "label": label, "vertices": P["vertices"], "edges": P["edges"], "und": P["und"],
            "directed": directed, "ok": True, "reason": ""}


# ------------------------------------------------------- representations ----

def repr_tab(G) -> None:
    if not _ready(G):
        return
    V, E, d = G["vertices"], G["edges"], G["directed"]
    with section_card("Three ways to store a graph"):
        st.markdown("- **Adjacency list:** each vertex with its neighbours.\n"
                    "- **Adjacency matrix:** n × n, entry 1 when there is an edge.\n"
                    "- **Incidence matrix:** vertices × edges, entry 1 when the vertex is an end of the edge "
                    "(directed: +1 at the tail, −1 at the head).")
    _show(draw_graph(V, E, directed=d, title=G["label"]))
    c1, c2 = st.columns(2)
    with c1:
        section_title("Adjacency list")
        for v, nb in adjacency_list(V, E, directed=d).items():
            st.markdown(f"**{v}** → {', '.join(nb) if nb else '∅'}")
    am = pd.DataFrame(0, index=V, columns=V)
    for u, v in E:
        am.at[u, v] = 1
        if not d:
            am.at[v, u] = 1
    with c2:
        section_title("Adjacency matrix")
        st.dataframe(am, width="stretch")
    inc = incidence_matrix(V, E, directed=d)
    section_title("Incidence matrix")
    if not E:
        st.caption("No edges, so the incidence matrix has no columns.")
    else:
        st.dataframe(pd.DataFrame(inc["matrix"], index=inc["rows"], columns=inc["cols"]),
                     width="stretch")
    out_deg, in_deg = am.sum(axis=1), am.sum(axis=0)
    if d:
        checks = [
            ("Sum of out-degrees = number of edges", int(out_deg.sum()) == len(E)),
            ("Sum of in-degrees = number of edges", int(in_deg.sum()) == len(E)),
            ("Every incidence column sums to 0", all(s == 0 for s in inc["col_sums"])),
            ("Incidence row sum = out-degree − in-degree",
             inc["row_sums"] == [int(out_deg[v] - in_deg[v]) for v in V]),
        ]
        section_title("In and out degrees")
        st.dataframe(pd.DataFrame({"Vertex": V, "In-degree": [int(in_deg[v]) for v in V],
                                   "Out-degree": [int(out_deg[v]) for v in V]}),
                     hide_index=True, width="stretch")
    else:
        checks = [
            ("Adjacency matrix is symmetric", bool((am.values == am.values.T).all())),
            ("Every incidence column sums to 2", all(s == 2 for s in inc["col_sums"])),
            ("Degree = adjacency row sum = incidence row sum", [int(x) for x in am.sum(axis=1)] == inc["row_sums"]),
            ("Sum of degrees = 2 × edges", int(am.values.sum()) == 2 * len(E)),
        ]
    st.dataframe(pd.DataFrame([{"Check": c, "Result": _mark(ok)} for c, ok in checks]),
                 hide_index=True, width="stretch")
    callout("All checks hold ✅" if all(ok for _, ok in checks) else "A check failed ❌",
            "success" if all(ok for _, ok in checks) else "error")


# ----------------------------------------------------------------- euler ----

def euler_tab(G) -> None:
    if not _ready(G):
        return
    V, U = G["vertices"], G["und"]
    with section_card("Euler circuit and path"):
        math_box(r"\text{Circuit}\iff\text{connected and every degree even};\quad"
                 r"\text{Path}\iff\text{connected and exactly 0 or 2 odd degrees}", "Euler's conditions")
        st.caption("Isolated vertices are ignored: only the edges must be connected.")
    if G["directed"]:
        st.caption("Directions are ignored on this tab.")
    if not U:
        callout("No edges, so there is nothing to traverse.", "info")
        return
    deg = _degrees(V, U)
    r = euler_check(V, U)
    kpi_row([
        {"label": "Euler circuit", "value": "Yes" if r["circuit_exists"] else "No",
         "accent": GREEN if r["circuit_exists"] else AMBER},
        {"label": "Euler path", "value": "Yes" if r["path_exists"] else "No",
         "accent": GREEN if r["path_exists"] else AMBER},
        {"label": "Odd-degree vertices", "value": len(r["odd_degree_vertices"])},
    ])
    st.dataframe(pd.DataFrame({"Vertex": V, "Degree": [deg[v] for v in V],
                               "Parity": ["odd" if deg[v] % 2 else "even" for v in V]}),
                 hide_index=True, width="stretch")
    if r["circuit_exists"] or r["path_exists"]:
        seq = r["circuit"] if r["circuit_exists"] else r["path"]
        kind = "circuit" if r["circuit_exists"] else "path"
        ok = gx.verify_euler(seq, U, closed=r["circuit_exists"])
        callout(f"Euler {kind}: " + " → ".join(seq) +
                (" — every edge used exactly once ✅" if ok else " — verification failed ❌"),
                "success" if ok else "error")
    elif not r["connected"]:
        callout("The edges form more than one piece, so no Euler walk exists.", "warning")
    else:
        callout(f"{len(r['odd_degree_vertices'])} vertices have odd degree; a circuit needs 0 and a path needs 0 or 2.",
                "warning")


# ----------------------------------------------------------- hamiltonian ----

def ham_tab(G) -> None:
    if not _ready(G):
        return
    V, U = G["vertices"], G["und"]
    with section_card("Hamiltonian cycle and path"):
        st.markdown("A **Hamiltonian cycle** visits every vertex exactly once and returns to the start "
                    "(needs at least 3 vertices). A **Hamiltonian path** visits every vertex once. "
                    "No simple test exists, so the page searches by backtracking (at most 8 vertices).")
        math_box(r"\text{Dirac: } n\ge3,\ \delta(G)\ge n/2\ \Rightarrow\ \text{Hamiltonian cycle exists}",
                 "Sufficient condition only")
    if len(V) > gx.MAX_V:
        callout(f"The search is limited to {gx.MAX_V} vertices; this graph has {len(V)}.", "warning")
        return
    r = gx.hamiltonian(V, U)
    cyc, pth = r["cycle"], r["path"]
    kpi_row([
        {"label": "Hamiltonian cycle", "value": "Yes" if cyc else "No", "accent": GREEN if cyc else AMBER},
        {"label": "Hamiltonian path", "value": "Yes" if pth else "No", "accent": GREEN if pth else AMBER},
    ])
    seq = cyc or pth
    if seq:
        ok = gx.verify_hamiltonian(seq, V, U, bool(cyc))
        callout(("Cycle: " if cyc else "Path: ") + " → ".join(seq) +
                (" — visits every vertex once, along real edges ✅" if ok else " — verification failed ❌"),
                "success" if ok else "error")
    else:
        callout("No Hamiltonian cycle or path exists in this graph.", "warning")
    deg = _degrees(V, U)
    dirac = gx.dirac(len(V), list(deg.values()))
    st.caption(f"Dirac's condition: {'holds' if dirac else 'does not hold'} "
               f"(smallest degree {min(deg.values())}, n/2 = {len(V) / 2:g}). "
               + ("It holds, and a cycle was indeed found ✅" if dirac and cyc
                  else "It is sufficient but not necessary, so a cycle can exist without it."))
    _show(draw_graph(V, U, highlight=_pairs(seq) if seq else None,
                     highlight_label="Hamiltonian cycle" if cyc else "Hamiltonian path"))


# ----------------------------------------------------------------- trees ----

def tree_tab(G) -> None:
    if not _ready(G):
        return
    V, U = G["vertices"], G["und"]
    n, e = len(V), len(U)
    with section_card("Trees"):
        math_box(r"\text{Tree}\iff\text{connected and acyclic}\iff\text{connected and }e=n-1"
                 r"\iff\text{acyclic and }e=n-1", "Equivalent definitions")
    tc = tree_check(V, U)
    conn, cyc = tc["connected"], has_cycle(V, U)
    comps = len(connected_components(V, U))
    c1, c2, c3 = conn and not cyc, conn and e == n - 1, (not cyc) and e == n - 1
    kpi_row([{"label": "Is a tree", "value": "Yes" if tc["is_tree"] else "No",
              "accent": GREEN if tc["is_tree"] else AMBER},
             {"label": "Vertices n", "value": n}, {"label": "Edges e", "value": e},
             {"label": "Components", "value": comps}])
    rows = [("Connected", conn), ("Acyclic (no cycle)", not cyc), (f"e = n − 1  ({e} = {n - 1})", e == n - 1),
            ("Connected and acyclic", c1), ("Connected and e = n − 1", c2), ("Acyclic and e = n − 1", c3)]
    st.dataframe(pd.DataFrame([{"Condition": a, "Holds": _mark(b)} for a, b in rows]),
                 hide_index=True, width="stretch")
    callout("The three definitions agree on this graph ✅" if c1 == c2 == c3 else "The definitions disagree ❌",
            "success" if c1 == c2 == c3 else "error")
    if not cyc:
        st.caption(f"Acyclic graph (forest): e = n − components → {e} = {n} − {comps} "
                   f"{'✅' if e == n - comps else '❌'}")
    if tc["is_tree"] and n >= 2:
        st.caption(f"Leaves (degree 1): {', '.join(tc['leaves'])}. A tree with n ≥ 2 has at least 2 leaves "
                   f"{'✅' if len(tc['leaves']) >= 2 else '❌'}. Sum of degrees = {2 * e} = 2(n − 1).")
    elif tc["leaves"]:
        st.caption("Leaves (degree 1): " + ", ".join(tc["leaves"]))
    _show(draw_graph(V, U))


# ------------------------------------------------------ bipartite/planar ----

def bip_tab(G) -> None:
    if not _ready(G):
        return
    V, U = G["vertices"], G["und"]
    with section_card("Bipartite graphs"):
        math_box(r"G\text{ bipartite}\iff G\text{ has no odd cycle}\iff 2\text{-colourable}", "Characterisation")
    br = bipartite_check(V, U)
    if br["is_bipartite"]:
        parts = br["partition"]
        ok = gx.verify_bipartition(U, parts)
        callout("Bipartite ✅" + (" — every edge joins the two parts" if ok else " — verification failed"),
                "success" if ok else "error")
        st.markdown(f"**Part 0:** {', '.join(parts[0]) or '∅'}  \n**Part 1:** {', '.join(parts[1]) or '∅'}")
        colours = {v: i for i, part in enumerate(parts) for v in part}
        pos = two_column_positions(parts[0], parts[1])
        _show(draw_graph(V, U, colours=colours, positions=pos))
    else:
        cyc = br["odd_cycle"]
        ok = gx.verify_odd_cycle(cyc, U)
        callout("Not bipartite ❌ — odd cycle: " + " → ".join(cyc + cyc[:1]) +
                (f" (length {len(cyc)}, checked ✅)" if ok else " (check failed)"), "error")
        _show(draw_graph(V, U, highlight=_pairs(cyc + cyc[:1]), highlight_label="Odd cycle"))
    with section_card("Planar graphs: a necessary condition"):
        math_box(r"\text{planar},\ v\ge3\ \Rightarrow\ e\le 3v-6;\qquad \text{planar and bipartite}\ \Rightarrow\ e\le 2v-4",
                 "Edge bounds")
        pb = planarity_bound_check(len(V), len(U), br["is_bipartite"])
        if pb.get("bound") is None:
            st.caption(pb.get("note", ""))
        else:
            kpi_row([{"label": "Edges e", "value": len(U)}, {"label": "Bound", "value": pb["bound"]},
                     {"label": "Within bound", "value": "Yes" if pb["satisfies_bound"] else "No",
                      "accent": GREEN if pb["satisfies_bound"] else DANGER}])
            st.caption(pb["formula"])
            if pb["satisfies_bound"]:
                callout("The bound holds. This does not prove the graph is planar.", "info")
            else:
                callout("The bound is violated, so the graph is NOT planar.", "error")


# ------------------------------------------------------------- colouring ----

def colour_tab(G) -> None:
    if not _ready(G):
        return
    V, U = G["vertices"], G["und"]
    with section_card("Graph colouring"):
        math_box(r"\chi(G)=\min\{k: G\text{ can be properly }k\text{-coloured}\}", "Chromatic number")
        st.markdown("A colouring is proper when adjacent vertices never share a colour. "
                    "Greedy colouring gives an upper bound; for up to 8 vertices the exact value is found by backtracking.")
    cr = graph_colouring(V, U)
    exact = len(V) <= gx.MAX_V
    colouring = cr["exact_colouring"] or cr["greedy_colouring"]
    bad = gx.verify_colouring(U, colouring)
    delta = max(_degrees(V, U).values()) if V else 0
    kpi_row([{"label": "Greedy colours", "value": cr["greedy_colours"]},
             {"label": "χ(G)" if exact else "Colours used (upper bound)", "value": cr["chromatic_number"],
              "accent": GREEN},
             {"label": "Δ + 1 bound", "value": delta + 1}])
    callout("Proper colouring: no edge has two equal ends ✅" if not bad
            else f"Improper colouring on {bad} ❌", "success" if not bad else "error")
    st.dataframe(pd.DataFrame({
        "Vertex": sorted(colouring), "Colour number": [colouring[v] for v in sorted(colouring)],
        "Colour": [COLOUR_NAMES[colouring[v]] if colouring[v] < len(COLOUR_NAMES) else f"colour {colouring[v]}"
                   for v in sorted(colouring)]}), hide_index=True, width="stretch")
    if exact:
        br = bipartite_check(V, U)
        st.caption(f"Bipartite ⇔ χ ≤ 2: bipartite = {br['is_bipartite']}, χ = {cr['chromatic_number']} → "
                   f"{'consistent ✅' if br['is_bipartite'] == (cr['chromatic_number'] <= 2) else 'inconsistent ❌'}. "
                   f"Also χ ≤ Δ + 1 = {delta + 1} "
                   f"{'✅' if cr['chromatic_number'] <= delta + 1 else '❌'}. "
                   "(Four Colour Theorem, statement only: every planar graph has χ ≤ 4.)")
    _show(draw_graph(V, U, colours=colouring))


# -------------------------------------------------------------- matching ----

def matching_tab() -> None:
    with section_card("Bipartite matching"):
        st.markdown("A **matching** is a set of edges with no shared vertex. **Hall's condition:** "
                    "every set S of left vertices has at least |S| neighbours.")
        math_box(r"\text{Left side can be fully matched}\iff |N(S)|\ge |S|\ \text{for every } S\subseteq L",
                 "Hall's theorem")
    c1, c2 = st.columns(2)
    lt = c1.text_input("Left side (comma-separated)", "A, B, C", key="gt_mL")
    rt = c1.text_input("Right side (comma-separated)", "1, 2, 3", key="gt_mR")
    et = c2.text_area("Edges (left,right one per line)", "A,1\nA,2\nB,2\nB,3\nC,3", key="gt_mE", height=130)
    P = gx.parse_matching(lt, rt, et)
    if P["errors"]:
        for e in P["errors"]:
            callout(e, "error")
        return
    L, R, E = P["left"], P["right"], P["edges"]
    r = max_matching(L, R, E)
    m = r["matching"]
    ok = gx.verify_matching(m, E)
    perfect = r["size"] == len(L) == len(R)
    kpi_row([{"label": "Maximum matching", "value": r["size"], "accent": GREEN},
             {"label": "Hall's condition", "value": "Holds" if r["hall_satisfied"] else "Fails",
              "accent": GREEN if r["hall_satisfied"] else DANGER},
             {"label": "Perfect matching", "value": "Yes" if perfect else "No"}])
    if m:
        st.markdown("**Matching:** " + ", ".join(f"{u} ↔ {v}" for u, v in m))
    callout("Matching verified: real edges, no vertex used twice ✅" if ok else "Matching check failed ❌",
            "success" if ok else "error")
    if not r["hall_satisfied"] and r["violating_set"]:
        S = r["violating_set"]
        N = sorted({v for u, v in E if u in S})
        callout(f"Hall fails: S = {{{', '.join(S)}}} has |S| = {len(S)} but N(S) = "
                f"{{{', '.join(N) or '∅'}}} has only {len(N)}.", "warning")
    st.caption(f"Theorem check: Hall holds ⇔ every left vertex is matched → "
               f"{r['hall_satisfied']} and {r['size'] == len(L)} "
               f"{'✅' if r['hall_satisfied'] == (r['size'] == len(L)) else '❌'}")
    pos = two_column_positions(L, R)
    _show(draw_graph(L + R, E, highlight={frozenset(p) for p in m},
                     highlight_label="Matching", positions=pos))