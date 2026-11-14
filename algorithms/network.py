"""
network.py — Undirected graph construction from eligible buildings and
candidate connections.

Only connections supplied by the caller are used; pairs of buildings are never
auto-connected.  A connection is the canonical tuple (u, v) with u < v
alphabetically, produced by canonicalize_edge.

No Streamlit imports allowed in this module.
"""

from algorithms.validation import canonicalize_edge


def build_network(eligible_names, edges) -> dict:
    """
    Filter candidate *edges* to those whose both endpoints are eligible.

    Returns
    -------
    dict
        vertices : sorted list of eligible names
        edges    : kept canonical connections, sorted by (u, v)
        dropped  : [{"edge": (u, v), "reason": str}, ...] for connections with
                   an ineligible or unknown endpoint
    """
    names     = list(eligible_names) if eligible_names is not None else []
    raw_edges = list(edges)          if edges          is not None else []

    vertices = sorted({str(n) for n in names})
    eligible = set(vertices)

    kept       = []
    dropped    = []
    seen_pairs = set()

    for raw in raw_edges:
        u, v = raw[0], raw[1]
        edge = canonicalize_edge(u, v)
        cu, cv = edge
        missing  = [x for x in (cu, cv) if x not in eligible]
        if missing:
            if len(missing) == 2:
                reason = f"{cu} and {cv} are not eligible"
            else:
                reason = f"{missing[0]} is not eligible"
            dropped.append({"edge": edge, "reason": reason})
            continue
        pair = (cu, cv)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        kept.append(edge)

    kept.sort(key=lambda e: (e[0], e[1]))
    return {"vertices": vertices, "edges": kept, "dropped": dropped}


def connected_components(vertices, edges) -> list:
    """
    Return connected components as a list of sorted name lists.

    The outer list is sorted by each component's first element.
    Isolated vertices are included as singleton components.
    Uses simple BFS.
    """
    verts  = list({str(v) for v in (vertices or [])})
    verts  = sorted(verts)

    adj = {v: [] for v in verts}
    vertex_set = set(verts)
    for raw in edges or []:
        u, v = str(raw[0]).strip(), str(raw[1]).strip()
        if u in vertex_set and v in vertex_set and u != v:
            adj[u].append(v)
            adj[v].append(u)

    visited = set()
    comps   = []
    for start in verts:
        if start in visited:
            continue
        component = []
        queue     = [start]
        visited.add(start)
        while queue:
            cur = queue.pop(0)
            component.append(cur)
            for nxt in adj[cur]:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        comps.append(sorted(component))

    comps.sort(key=lambda c: c[0])
    return comps


def is_connected(vertices, edges) -> bool:
    """True if the graph is connected.  Vacuously True for 0 or 1 vertex."""
    verts = [str(v) for v in (vertices or [])]
    n     = len(set(verts))
    if n <= 1:
        return True
    return len(connected_components(verts, edges)) == 1


def has_cycle(vertices, edges) -> bool:
    """
    Return True if the undirected graph contains a cycle.

    Uses DFS with a parent-tracking scheme.
    A self-loop counts as a cycle.
    """
    verts     = list({str(v) for v in (vertices or [])})
    adj       = {v: [] for v in verts}
    vset      = set(verts)

    for raw in edges or []:
        u, v = str(raw[0]).strip(), str(raw[1]).strip()
        if u not in vset or v not in vset:
            continue
        if u == v:
            return True      # self-loop
        adj[u].append(v)
        adj[v].append(u)

    visited = set()

    def _dfs(node, parent):
        visited.add(node)
        for nxt in adj[node]:
            if nxt not in visited:
                if _dfs(nxt, node):
                    return True
            elif nxt != parent:
                return True
        return False

    for v in verts:
        if v not in visited:
            if _dfs(v, None):
                return True
    return False


def adjacency_matrix(vertices, edges) -> "pd.DataFrame":
    """
    0/1 adjacency matrix for the candidate connection graph.

    A cell is 1 when a connection exists, 0 when it does not.
    The diagonal is 0 (no self-loops).
    Rows/columns are the vertices sorted by name.
    """
    import pandas as pd
    names = sorted({str(v) for v in (vertices or [])})
    if not names:
        return pd.DataFrame()

    matrix = pd.DataFrame(0, index=names, columns=names, dtype=int)
    vset   = set(names)
    for raw in edges or []:
        u, v = str(raw[0]).strip(), str(raw[1]).strip()
        if u in vset and v in vset and u != v:
            matrix.at[u, v] = 1
            matrix.at[v, u] = 1
    return matrix


def degree_table(vertices, edges) -> "pd.DataFrame":
    """
    Degree per vertex.

    Columns: ``vertex, degree``.  Sorted by vertex name.
    The degrees always sum to twice the edge count (degree-sum theorem).
    """
    import pandas as pd
    names  = sorted({str(v) for v in (vertices or [])})
    degree = {n: 0 for n in names}
    vset   = set(names)
    for raw in edges or []:
        u, v = str(raw[0]).strip(), str(raw[1]).strip()
        if u in vset and v in vset and u != v:
            degree[u] += 1
            degree[v] += 1
    rows = [{"vertex": n, "degree": degree[n]} for n in names]
    return pd.DataFrame(rows, columns=["vertex", "degree"])
