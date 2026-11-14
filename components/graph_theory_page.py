"""
graph_theory_page.py — Graph Theory page for Sustainable Solar Energy Allocation.

Shows the eligible-building network and the extra network views.
Every connection is simply present or absent.
No algorithm logic lives here; everything delegates to algorithms/.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from components import graph_tabs as gt

from algorithms.set_theory import build_sets, eligible_set
from algorithms.network import (
    build_network,
    connected_components,
    is_connected,
    has_cycle,
    adjacency_matrix,
    degree_table,
)
from algorithms.graph_algorithms import (
    adjacency_list,
    incidence_matrix,
    euler_check,
    hamiltonian_check,
    bipartite_check,
    graph_colouring,
    max_matching,
    planarity_bound_check,
    tree_check,
)
from components.network_graph import draw_network
from components.style import (
    AMBER,
    DANGER,
    GREEN,
    callout,
    concept_card,
    empty_buildings_notice,
    esc,
    kpi_row,
    math_box,
    page_header,
    pill,
    section_card,
    section_title,
    show_figure,
)

# ---------------------------------------------------------------------------
# Default "custom graph" presets for the standalone editor
# ---------------------------------------------------------------------------

_PRESET_GRAPHS = {
    "Triangle (K₃)":          (["A","B","C"],         [("A","B"),("B","C"),("A","C")]),
    "4-cycle (C₄)":           (["A","B","C","D"],     [("A","B"),("B","C"),("C","D"),("D","A")]),
    "Complete K₄":            (["A","B","C","D"],     [(u,v) for i,u in enumerate(["A","B","C","D"]) for v in ["A","B","C","D"][i+1:]]),
    "Path (P₄)":              (["A","B","C","D"],     [("A","B"),("B","C"),("C","D")]),
    "Star (K₁,₃)":            (["C","A","B","D"],     [("C","A"),("C","B"),("C","D")]),
    "Disconnected (2+2)":     (["A","B","C","D"],     [("A","B"),("C","D")]),
    "Single vertex":          (["A"],                 []),
}


def render_graph_theory_page() -> None:
    page_header("Graph Theory",
                "Campus graph, representations, Euler and Hamiltonian, trees, bipartite, planar bound, colouring and matching.")
    df = st.session_state.get("buildings", pd.DataFrame())
    thresholds = st.session_state.get("thresholds", {})
    edges_in = st.session_state.get("edges", [])
    vertices_c, g_edges_c = [], []
    if df is not None and not df.empty:
        sets = build_sets(df, thresholds)
        E = eligible_set(sets["A"], sets["B"], sets["C"])
        if E:
            net = build_network(E, edges_in)
            vertices_c, g_edges_c = net["vertices"], net["edges"]
    G = gt.graph_source(vertices_c, g_edges_c)
    tab_specs = [
        ("🏫 Campus Graph", lambda: _campus_tab(df, thresholds, edges_in, vertices_c, g_edges_c)),
        ("🧮 Representations", lambda: gt.repr_tab(G)),
        ("🔄 Euler", lambda: gt.euler_tab(G)),
        ("🔁 Hamiltonian", lambda: gt.ham_tab(G)),
        ("🌳 Trees", lambda: gt.tree_tab(G)),
        ("🎨 Bipartite & Planar", lambda: gt.bip_tab(G)),
        ("🖌️ Colouring", lambda: gt.colour_tab(G)),
        ("🔗 Matching", gt.matching_tab),
    ]
    if G["source"] == "Custom graph":
        tab_specs = tab_specs[1:]
    tabs = st.tabs([label for label, _ in tab_specs])
    for tab, (_, render) in zip(tabs, tab_specs):
        with tab:
            render()


# ---------------------------------------------------------------------------
# Tab: Campus Graph (existing functionality, preserved)
# ---------------------------------------------------------------------------

def _campus_tab(df, thresholds, edges_in, vertices, g_edges) -> None:
    if df is None or df.empty:
        empty_buildings_notice()
        return

    math_box(
        r"G = (V, E_g), \qquad V = E = A \cap B \cap C",
        "The graph vertices are the eligible buildings and each edge "
        "is a candidate connection — present or absent.",
    )

    sets = build_sets(df, thresholds)
    E    = eligible_set(sets["A"], sets["B"], sets["C"])

    if not E:
        callout(
            "**No building is eligible** with the current thresholds.\n\n"
            "**What to do:** adjust the thresholds on **Sets** or the "
            "buildings on **Campus Data**.",
            "warning",
        )
        return

    net      = build_network(E, edges_in)
    vertices = net["vertices"]
    g_edges  = net["edges"]
    dropped  = net["dropped"]

    if dropped:
        callout(f"{len(dropped)} candidate connection(s) dropped (endpoint not eligible).", "warning")

    if len(vertices) < 2:
        callout("Fewer than two eligible buildings — no connections possible.", "info")
        return

    conn  = is_connected(vertices, g_edges)
    comps = connected_components(vertices, g_edges)
    cycle = has_cycle(vertices, g_edges)
    deg   = degree_table(vertices, g_edges)
    deg_sum = int(deg["degree"].sum())
    is_tree = conn and not cycle

    if not g_edges:
        callout("No candidate connections defined.", "info")
    elif conn:
        callout("Graph is connected.", "success")
    else:
        callout("Graph is disconnected.", "error")
        comp_str = "; ".join("{" + ", ".join(c) + "}" for c in comps)
        st.markdown(f"**Connected components:** {comp_str}")

    kpi_row([
        {"label": "Vertices |V|",     "value": len(vertices), "sublabel": "Eligible buildings", "accent": GREEN},
        {"label": "Edges |E|",        "value": len(g_edges),  "sublabel": "Candidate connections", "accent": GREEN},
        {"label": "Components",       "value": len(comps),    "sublabel": "1 = connected", "accent": AMBER},
        {"label": "Contains a cycle", "value": "Yes" if cycle else "No", "accent": DANGER if cycle else GREEN},
        {"label": "Is a tree",        "value": "Yes" if is_tree else "No", "accent": GREEN if is_tree else AMBER},
    ])

    with section_card("Campus connection graph", "Connections only"):
        col_chart, col_help = st.columns([3, 2])
        with col_chart:
            fig = draw_network(vertices, g_edges, title="Candidate connection graph")
            st.pyplot(fig)
            plt.close(fig)
        with col_help:
            st.markdown(
                concept_card("How to read this",
                             "Each node is an eligible building. Edges are candidate "
                             "connections — every one is simply present or absent."),
                unsafe_allow_html=True,
            )

    inner_tab1, inner_tab2, inner_tab3 = st.tabs(["Adjacency Matrix", "Degree Table", "Components"])
    with inner_tab1:
        adj = adjacency_matrix(vertices, g_edges)
        if not adj.empty:
            st.dataframe(adj, width="stretch")
    with inner_tab2:
        if not deg.empty:
            st.dataframe(deg, hide_index=True, width="stretch")
            callout(f"Degree-sum = {deg_sum} = 2 × {len(g_edges)} ✅" if deg_sum == 2 * len(g_edges) else "Mismatch ❌",
                    "success" if deg_sum == 2 * len(g_edges) else "error")
    with inner_tab3:
        rows = [{"Component": f"C{i+1}", "Vertices": ", ".join(c), "Size": len(c)} for i, c in enumerate(comps)]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# Tab: Representations
# ---------------------------------------------------------------------------

def _repr_tab(vertices, edges) -> None:
    with section_card("Graph Representations"):
        st.markdown(
            "The same graph can be represented in three standard ways.\n\n"
            "- **Adjacency list:** for each vertex, list its neighbours.\n"
            "- **Adjacency matrix:** n×n matrix; entry (i,j)=1 if edge exists, 0 otherwise.\n"
            "- **Incidence matrix:** |V|×|E| matrix; entry (v,e)=1 if v is an endpoint of e."
        )

    directed = st.checkbox("Treat as directed graph", value=False, key="repr_directed")

    if not vertices:
        callout("No eligible buildings to show. Load data or use the Custom Graph tab.", "info")
        return

    col1, col2 = st.columns(2)
    with col1:
        section_title("Adjacency List")
        adj_l = adjacency_list(vertices, edges, directed=directed)
        for v, nbs in adj_l.items():
            st.markdown(f"**{v}** → {', '.join(nbs) if nbs else '∅'}")

    with col2:
        section_title("Adjacency Matrix (0/1)")
        adj_m = adjacency_matrix(vertices, edges)
        if not adj_m.empty:
            st.dataframe(adj_m, width="stretch")

    section_title("Incidence Matrix")
    inc = incidence_matrix(vertices, edges, directed=directed)
    if inc["matrix"]:
        df_inc = pd.DataFrame(inc["matrix"], index=inc["rows"], columns=inc["cols"])
        st.dataframe(df_inc, width="stretch")
        if not directed:
            all_2 = all(s == 2 for s in inc["col_sums"])
            callout(
                "Each column sums to 2 (each edge has exactly 2 endpoints) ✅"
                if all_2 else "Some column does not sum to 2 ❌",
                "success" if all_2 else "error",
            )

    section_title("In/Out Degree (directed)")
    if directed and vertices:
        from algorithms.graph_algorithms import _degree_dict
        degs = _degree_dict(vertices, edges, directed=True)
        rows = [{"Vertex": v, "In-degree": degs["in"][v], "Out-degree": degs["out"][v]} for v in sorted(vertices)]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# Tab: Euler Circuit / Path
# ---------------------------------------------------------------------------

def _euler_tab(vertices, edges) -> None:
    with section_card("Euler Circuit and Path"):
        st.markdown(
            "**Euler circuit:** traverses every edge exactly once and returns to start. "
            "Exists iff graph is connected and every vertex has even degree.\n\n"
            "**Euler path:** traverses every edge exactly once. "
            "Exists iff graph is connected and exactly 2 vertices have odd degree."
        )
        math_box(
            r"\text{Euler circuit} \iff \text{connected} \land \forall v: \deg(v) \text{ even}",
            "Euler circuit condition",
        )

    if not vertices:
        callout("No eligible buildings. Load data or use Custom Graph tab.", "info")
        return

    r = euler_check(vertices, edges)
    kpi_row([
        {"label": "Euler circuit", "value": "Yes ✅" if r["circuit_exists"] else "No ❌",
         "accent": GREEN if r["circuit_exists"] else AMBER},
        {"label": "Euler path",    "value": "Yes ✅" if r["path_exists"] else "No ❌",
         "accent": GREEN if r["path_exists"] else AMBER},
        {"label": "Odd-degree vertices", "value": len(r["odd_degree_vertices"])},
    ])
    if r["odd_degree_vertices"]:
        st.markdown(f"**Odd-degree:** {', '.join(r['odd_degree_vertices'])}")

    if r["circuit_exists"] and r["circuit"]:
        callout("**Euler circuit** (Hierholzer): " + " → ".join(r["circuit"]), "success")
    elif r["path_exists"] and r["path"]:
        callout("**Euler path** (Hierholzer): " + " → ".join(r["path"]), "success")


# ---------------------------------------------------------------------------
# Tab: Hamiltonian
# ---------------------------------------------------------------------------

def _ham_tab(vertices, edges) -> None:
    with section_card("Hamiltonian Cycle and Path"):
        st.markdown(
            "A **Hamiltonian cycle** visits every vertex exactly once and returns to start. "
            "A **Hamiltonian path** visits every vertex exactly once (no return required). "
            "Found by backtracking (n ≤ 8)."
        )

    tc = tree_check(vertices, edges)
    kpi_row([
        {"label": "Is tree",    "value": "Yes" if tc["is_tree"] else "No"},
        {"label": "Leaves",     "value": len(tc["leaves"])},
        {"label": "|V|",        "value": tc["n"]},
        {"label": "|E|",        "value": tc["e"]},
        {"label": "n-1 check",  "value": "✅" if tc["e"] == tc["n"] - 1 or tc["n"] == 0 else "❌"},
    ])
    if tc["leaves"]:
        st.markdown(f"**Leaves:** {', '.join(tc['leaves'])}")

    if not vertices:
        callout("No eligible buildings to check.", "info")
        return
    if len(vertices) > 8:
        callout("Hamiltonian check limited to n ≤ 8 vertices.", "warning")
        return

    r = hamiltonian_check(vertices, edges)
    if r["errors"]:
        callout(r["errors"][0], "error")
        return

    if r["cycle"]:
        callout("**Hamiltonian cycle:** " + " → ".join(r["cycle"]), "success")
    else:
        callout("No Hamiltonian cycle found.", "warning")
    if r["path"]:
        callout("**Hamiltonian path:** " + " → ".join(r["path"]), "success")
    else:
        callout("No Hamiltonian path found.", "warning")


# ---------------------------------------------------------------------------
# Tab: Bipartite
# ---------------------------------------------------------------------------

def _bipartite_tab(vertices, edges) -> None:
    with section_card("Bipartite Check"):
        st.markdown(
            "A graph is **bipartite** iff it has no odd-length cycle — "
            "equivalently, its vertices can be 2-coloured such that no edge connects "
            "two vertices of the same colour. Checked by BFS."
        )
        math_box(r"G \text{ bipartite} \iff G \text{ has no odd cycle}", "Bipartite characterisation")
        pb = planarity_bound_check(len(vertices), len(edges))
        st.markdown(
            f"**Planarity necessary condition** ({pb.get('formula', 'n/a')}): "
            + ("satisfied ✅" if pb.get("satisfies_bound") else "violated ❌")
            + f"\n\n_{pb.get('note', '')}_"
        )

    if not vertices:
        callout("No eligible buildings.", "info")
        return

    r = bipartite_check(vertices, edges)
    if r["is_bipartite"]:
        callout("Graph is **bipartite** ✅", "success")
        st.markdown(f"**Part 0:** {', '.join(r['partition'][0])}")
        st.markdown(f"**Part 1:** {', '.join(r['partition'][1])}")
    else:
        callout("Graph is **not bipartite** ❌ (contains an odd cycle)", "error")
        if r["odd_cycle"]:
            st.markdown("**Odd cycle:** " + " → ".join(r["odd_cycle"]))


# ---------------------------------------------------------------------------
# Tab: Graph Colouring
# ---------------------------------------------------------------------------

def _colour_tab(vertices, edges) -> None:
    with section_card("Graph Colouring"):
        st.markdown(
            "Assign colours to vertices so no two adjacent vertices share a colour. "
            "The minimum number of colours needed is the **chromatic number χ(G)**. "
            "Greedy gives an upper bound; exact χ is found by backtracking (n ≤ 8)."
        )
        math_box(r"\chi(G) = \min\{k : G \text{ is k-colourable}\}", "Chromatic number")

    if not vertices:
        callout("No eligible buildings.", "info")
        return
    if len(vertices) > 8:
        callout("Exact chromatic number limited to n ≤ 8.", "warning")

    r = graph_colouring(vertices, edges)
    kpi_row([
        {"label": "Greedy colours",    "value": r["greedy_colours"]},
        {"label": "Chromatic number χ", "value": r["chromatic_number"], "accent": GREEN},
    ])

    section_title("Exact colouring plan")
    colouring = r["exact_colouring"] or r["greedy_colouring"]
    colour_names = ["red", "blue", "green", "yellow", "purple", "orange", "pink", "brown"]
    for v, c in sorted(colouring.items()):
        name = colour_names[c] if c < len(colour_names) else f"colour {c}"
        st.markdown(f"**{v}** → colour {c} ({name})")


# ---------------------------------------------------------------------------
# Tab: Bipartite Matching
# ---------------------------------------------------------------------------

def _match_tab() -> None:
    with section_card("Maximum Bipartite Matching"):
        st.markdown(
            "Given a bipartite graph (left set L, right set R, edges between them), "
            "find the largest matching (set of edges with no shared vertex). "
            "Checked via Hall's marriage condition: a perfect matching exists iff "
            "for every subset S ⊆ L, |N(S)| ≥ |S|."
        )
        math_box(
            r"|M| = \text{max matching}",
            "Augmenting-path algorithm",
        )

    col1, col2 = st.columns(2)
    with col1:
        left_str  = st.text_input("Left vertices (comma-sep)", value="A,B,C", key="match_L")
        right_str = st.text_input("Right vertices (comma-sep)", value="1,2,3", key="match_R")
    with col2:
        edges_str = st.text_area(
            "Edges (left,right — one per line)",
            value="A,1\nA,2\nB,2\nB,3\nC,3",
            key="match_E", height=130,
        )

    if st.button("Find Maximum Matching", key="btn_match", type="primary"):
        try:
            L = [x.strip() for x in left_str.split(",") if x.strip()]
            R = [x.strip() for x in right_str.split(",") if x.strip()]
            E = []
            for line in edges_str.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) == 2:
                    E.append((parts[0], parts[1]))
        except Exception as exc:
            callout(f"Parse error: {exc}", "error")
            return

        r = max_matching(L, R, E)
        if r["errors"]:
            callout(r["errors"][0], "error")
            return

        kpi_row([
            {"label": "Max matching size", "value": r["size"], "accent": GREEN},
            {"label": "Hall's condition",  "value": "✅ Satisfied" if r["hall_satisfied"] else "❌ Violated",
             "accent": GREEN if r["hall_satisfied"] else DANGER},
        ])
        if r["matching"]:
            st.markdown("**Matching pairs:** " + ", ".join(f"{u}↔{v}" for u, v in r["matching"]))
        if not r["hall_satisfied"] and r["violating_set"]:
            callout(
                f"Hall's condition violated: subset {r['violating_set']} has fewer neighbours.",
                "warning",
            )


# ---------------------------------------------------------------------------
# Tab: Custom Graph Editor
# ---------------------------------------------------------------------------

def _custom_graph_tab() -> None:
    with section_card("Custom Graph Editor"):
        st.markdown(
            "Build any graph with up to 8 vertices and run all graph-theory checks on it. "
            "Choose a preset or enter vertices and edges manually."
        )

    preset = st.selectbox(
        "Load a preset", ["(manual)"] + list(_PRESET_GRAPHS.keys()),
        key="custom_preset",
    )

    if preset != "(manual)" and preset in _PRESET_GRAPHS:
        pv, pe = _PRESET_GRAPHS[preset]
        default_v = ",".join(pv)
        default_e = "\n".join(f"{u},{v}" for u, v in pe)
    else:
        default_v = "A,B,C"
        default_e = "A,B\nB,C\nA,C"

    col1, col2 = st.columns(2)
    with col1:
        v_str = st.text_input("Vertices (comma-sep, max 8)", value=default_v, key="cg_v")
        e_str = st.text_area("Edges (u,v — one per line)", value=default_e, key="cg_e", height=160)
        directed = st.checkbox("Directed graph", value=False, key="cg_directed")
    with col2:
        st.markdown("**Tips:**")
        st.markdown("- Vertex names must match exactly (case-sensitive).\n"
                    "- For undirected graphs, enter each edge once.\n"
                    "- Maximum 8 vertices for backtracking algorithms.")

    if st.button("Analyse Custom Graph", key="btn_cg", type="primary"):
        try:
            verts = [x.strip() for x in v_str.split(",") if x.strip()][:8]
            edges = []
            for line in e_str.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) == 2 and parts[0] in verts and parts[1] in verts:
                    edges.append((parts[0], parts[1]))
        except Exception as exc:
            callout(f"Parse error: {exc}", "error")
            return

        if not verts:
            callout("Please enter at least one vertex.", "error")
            return

        _run_all_checks(verts, edges, directed)


def _run_all_checks(vertices, edges, directed) -> None:
    """Run all graph checks on a custom graph and display results."""
    st.divider()
    section_title(f"Results for G = ({len(vertices)} vertices, {len(edges)} edges)")

    # Draw
    try:
        fig = draw_network(vertices, edges, title="Custom Graph")
        st.pyplot(fig)
        plt.close(fig)
    except Exception:
        pass

    # Connectivity & basic
    conn  = is_connected(vertices, edges)
    comps = connected_components(vertices, edges)
    cycle = has_cycle(vertices, edges)
    tc    = tree_check(vertices, edges)

    kpi_row([
        {"label": "Connected",    "value": "✅" if conn else "❌", "accent": GREEN if conn else DANGER},
        {"label": "Components",   "value": len(comps)},
        {"label": "Has cycle",    "value": "Yes" if cycle else "No"},
        {"label": "Is tree",      "value": "Yes" if tc["is_tree"] else "No"},
    ])

    # Euler
    er = euler_check(vertices, edges)
    st.markdown(
        f"**Euler circuit:** {'✅' if er['circuit_exists'] else '❌'}  |  "
        f"**Euler path:** {'✅' if er['path_exists'] else '❌'}  |  "
        f"**Odd-degree vertices:** {er['odd_degree_vertices']}"
    )
    if er["circuit"]:
        callout("Euler circuit: " + " → ".join(er["circuit"]), "success")

    # Hamiltonian
    if len(vertices) <= 8:
        hr = hamiltonian_check(vertices, edges)
        st.markdown(
            f"**Hamiltonian cycle:** {'✅ ' + '→'.join(hr['cycle']) if hr['cycle'] else '❌'}  |  "
            f"**Hamiltonian path:** {'✅ ' + '→'.join(hr['path']) if hr['path'] else '❌'}"
        )

    # Bipartite
    br = bipartite_check(vertices, edges)
    if br["is_bipartite"]:
        callout(f"Bipartite ✅ — Parts: {br['partition'][0]} | {br['partition'][1]}", "success")
    else:
        callout(f"Not bipartite ❌ — Odd cycle: {br['odd_cycle']}", "error")

    # Planarity bound
    pb = planarity_bound_check(len(vertices), len(edges), br["is_bipartite"])
    callout(f"Planarity bound: {pb.get('formula', 'n/a')} — "
            + ("satisfied ✅ (necessary condition only)" if pb["satisfies_bound"]
               else "violated ❌ (proves non-planar)"),
            "success" if pb["satisfies_bound"] else "error")

    # Colouring
    cr = graph_colouring(vertices, edges)
    st.markdown(f"**Chromatic number χ(G) = {cr['chromatic_number']}** "
                f"(greedy upper bound: {cr['greedy_colours']})")
    colouring = cr["exact_colouring"] or cr["greedy_colouring"]
    if colouring:
        st.markdown("Colouring: " + ", ".join(f"{v}→c{c}" for v, c in sorted(colouring.items())))


# ---------------------------------------------------------------------------
# BFS path helper
# ---------------------------------------------------------------------------

def _bfs_path(vertices, edges, src, tgt):
    """Return a BFS path from *src* to *tgt*, or [] if unreachable."""
    adj = {v: [] for v in vertices}
    vset = set(vertices)
    for raw in edges or []:
        u, v = str(raw[0]).strip(), str(raw[1]).strip()
        if u in vset and v in vset and u != v:
            adj[u].append(v)
            adj[v].append(u)
    if src not in adj or tgt not in adj:
        return []
    prev  = {src: None}
    queue = [src]
    while queue:
        cur = queue.pop(0)
        if cur == tgt:
            break
        for nxt in adj[cur]:
            if nxt not in prev:
                prev[nxt] = cur
                queue.append(nxt)
    if tgt not in prev:
        return []
    path, cur = [], tgt
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path
