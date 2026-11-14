"""
graph_algorithms.py — Extended graph algorithms for the Graph Theory page.

Covers: incidence matrix, directed in/out degree, Euler circuit (Hierholzer),
Hamiltonian cycle/path (backtracking), bipartite check, graph colouring,
maximum matching (augmenting paths), planarity bound check.

No Streamlit imports. Graphs are given as adjacency lists / edge lists.
All vertex names are strings. n ≤ 8 for backtracking algorithms.
"""

from __future__ import annotations
import itertools
from collections import defaultdict, deque


# ===========================================================================
# Helpers
# ===========================================================================

def _build_adj(vertices: list[str], edges: list[tuple],
               directed: bool = False) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {v: [] for v in vertices}
    for e in edges:
        u, v = str(e[0]), str(e[1])
        if u in adj and v in adj:
            adj[u].append(v)
            if not directed:
                adj[v].append(u)
    return adj


def _degree_dict(vertices, edges, directed=False):
    if directed:
        out_deg = {v: 0 for v in vertices}
        in_deg  = {v: 0 for v in vertices}
        for e in edges:
            u, v = str(e[0]), str(e[1])
            if u in out_deg:
                out_deg[u] += 1
            if v in in_deg:
                in_deg[v] += 1
        return {"out": out_deg, "in": in_deg}
    else:
        deg = {v: 0 for v in vertices}
        for e in edges:
            u, v = str(e[0]), str(e[1])
            if u in deg:
                deg[u] += 1
            if v in deg:
                deg[v] += 1
        return deg


# ===========================================================================
# 1. Graph representations
# ===========================================================================

def adjacency_list(vertices: list[str], edges: list[tuple],
                   directed: bool = False) -> dict:
    """Return adjacency list as a dict vertex → sorted list of neighbours."""
    adj = _build_adj(vertices, edges, directed)
    return {v: sorted(adj[v]) for v in sorted(vertices)}


def incidence_matrix(vertices: list[str], edges: list[tuple],
                     directed: bool = False) -> dict:
    """
    Build the incidence matrix (|V| × |E|).

    For undirected: entry (v, e) = 1 if v is an endpoint of e.
    For directed:   entry (v, e) = +1 if v is tail, -1 if v is head, 0 otherwise.

    Returns dict with 'matrix' (list of lists), 'rows' (vertices), 'cols' (edge labels).
    """
    verts = sorted(vertices)
    v_idx = {v: i for i, v in enumerate(verts)}
    edge_labels = [f"{str(e[0])}-{str(e[1])}" for e in edges]
    n_v = len(verts)
    n_e = len(edges)
    matrix = [[0] * n_e for _ in range(n_v)]

    for j, e in enumerate(edges):
        u, v = str(e[0]), str(e[1])
        if directed:
            if u in v_idx:
                matrix[v_idx[u]][j] = 1
            if v in v_idx:
                matrix[v_idx[v]][j] = -1
        else:
            if u in v_idx:
                matrix[v_idx[u]][j] += 1
            if v in v_idx:
                matrix[v_idx[v]][j] += 1

    # Property checks
    # Each column should sum to 2 for undirected (self-loops sum to 2 too)
    col_sums = [sum(matrix[i][j] for i in range(n_v)) for j in range(n_e)]
    col_check = all(s == 2 for s in col_sums) if not directed else None

    # Degree = row sum
    row_sums = [sum(matrix[i][j] for j in range(n_e)) for i in range(n_v)]

    return {
        "matrix":       matrix,
        "rows":         verts,
        "cols":         edge_labels,
        "col_sums":     col_sums,
        "col_sum_check": col_check,
        "row_sums":     row_sums,
        "errors":       [],
    }


# ===========================================================================
# 2. Euler circuit / path
# ===========================================================================

def euler_check(vertices: list[str], edges: list[tuple]) -> dict:
    """
    Check Euler circuit / path conditions on an undirected graph.

    Euler circuit: exists iff graph is connected and every vertex has even degree.
    Euler path:    exists iff graph is connected and exactly 2 vertices have odd degree.

    Returns 'circuit_exists', 'path_exists', 'odd_degree_vertices', and a
    circuit found by Hierholzer's algorithm if one exists.
    """
    if not vertices:
        return {
            "circuit_exists": False, "path_exists": False,
            "odd_degree_vertices": [], "circuit": [],
            "path": [], "errors": [],
        }

    verts = [str(v) for v in vertices]
    # Build adjacency as multiset (edge list based)
    adj: dict[str, list[str]] = {v: [] for v in verts}
    for e in edges:
        u, v = str(e[0]), str(e[1])
        if u in adj and v in adj and u != v:
            adj[u].append(v)
            adj[v].append(u)

    deg = {v: len(adj[v]) for v in verts}
    odd_verts = [v for v in verts if deg[v] % 2 == 1]

    # Connectivity (BFS from any vertex with edges)
    start = next((v for v in verts if deg[v] > 0), verts[0])
    visited: set[str] = set()
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        if cur in visited:
            continue
        visited.add(cur)
        for nb in adj[cur]:
            if nb not in visited:
                queue.append(nb)

    # All vertices with edges must be reachable
    active = {v for v in verts if deg[v] > 0}
    connected = active.issubset(visited)

    circuit_exists = connected and len(odd_verts) == 0
    path_exists    = connected and len(odd_verts) == 2

    circuit: list[str] = []
    if circuit_exists and verts:
        circuit = _hierholzer(verts, edges, start)

    path: list[str] = []
    if path_exists:
        path_start = odd_verts[0]
        path = _hierholzer(verts, edges, path_start)

    return {
        "circuit_exists":      circuit_exists,
        "path_exists":         path_exists,
        "odd_degree_vertices": sorted(odd_verts),
        "connected":           connected,
        "circuit":             circuit,
        "path":                path,
        "errors":              [],
    }


def _hierholzer(vertices: list[str], edges: list[tuple],
                start: str) -> list[str]:
    """Hierholzer's algorithm — returns an Euler circuit starting at *start*."""
    # Build multiset adjacency using edge indices
    adj: dict[str, list[list]] = {str(v): [] for v in vertices}
    for e in edges:
        u, v = str(e[0]), str(e[1])
        if u in adj and v in adj and u != v:
            marker = [False]
            adj[u].append([v, marker])
            adj[v].append([u, marker])

    circuit: list[str] = []
    stack = [start]
    while stack:
        v = stack[-1]
        found = False
        while adj[v]:
            entry = adj[v][-1]
            adj[v].pop()
            nb, used = entry[0], entry[1]
            if not used[0]:
                used[0] = True
                stack.append(nb)
                found = True
                break
        if not found:
            circuit.append(stack.pop())

    return list(reversed(circuit))


# ===========================================================================
# 3. Hamiltonian cycle / path (backtracking, n ≤ 8)
# ===========================================================================

def hamiltonian_check(vertices: list[str], edges: list[tuple]) -> dict:
    """
    Find a Hamiltonian cycle and path by backtracking (n ≤ 8).

    Returns 'cycle' and 'path' (lists of vertex names), or [] if none found.
    """
    n = len(vertices)
    if n == 0:
        return {"cycle": [], "path": [], "n": 0, "errors": []}
    if n > 8:
        return {
            "cycle": [], "path": [], "n": n,
            "errors": ["Hamiltonian check is limited to n ≤ 8 vertices."],
        }

    verts = [str(v) for v in vertices]
    adj_set: set[tuple[str, str]] = set()
    for e in edges:
        u, v = str(e[0]), str(e[1])
        adj_set.add((u, v))
        adj_set.add((v, u))

    # Hamiltonian cycle: visit all vertices and return to start
    def _ham_cycle(path: list[str]) -> list[str] | None:
        if len(path) == n:
            if (path[-1], path[0]) in adj_set:
                return path + [path[0]]
            return None
        last = path[-1]
        for v in verts:
            if v not in path and (last, v) in adj_set:
                result = _ham_cycle(path + [v])
                if result:
                    return result
        return None

    # Hamiltonian path: visit all vertices
    def _ham_path(path: list[str]) -> list[str] | None:
        if len(path) == n:
            return path
        last = path[-1]
        for v in verts:
            if v not in path and (last, v) in adj_set:
                result = _ham_path(path + [v])
                if result:
                    return result
        return None

    cycle = _ham_cycle([verts[0]]) or []
    path  = _ham_path([verts[0]]) or []

    return {"cycle": cycle, "path": path, "n": n, "errors": []}


# ===========================================================================
# 4. Bipartite check (BFS 2-colouring)
# ===========================================================================

def bipartite_check(vertices: list[str], edges: list[tuple]) -> dict:
    """
    Check if the graph is bipartite by BFS 2-colouring.

    Returns 'is_bipartite', 'partition' (two sets), and 'odd_cycle' if not bipartite.
    """
    if not vertices:
        return {"is_bipartite": True, "partition": [[], []], "odd_cycle": [], "errors": []}

    verts = [str(v) for v in vertices]
    adj = _build_adj(verts, edges)
    colour: dict[str, int] = {}
    parent: dict[str, str | None] = {}

    odd_cycle: list[str] = []

    for start in verts:
        if start in colour:
            continue
        colour[start] = 0
        parent[start] = None
        queue = deque([start])
        while queue:
            v = queue.popleft()
            for nb in adj[v]:
                if nb not in colour:
                    colour[nb] = 1 - colour[v]
                    parent[nb] = v
                    queue.append(nb)
                elif colour[nb] == colour[v]:
                    # Odd cycle found — reconstruct
                    odd_cycle = _reconstruct_odd_cycle(v, nb, parent)
                    break
            if odd_cycle:
                break
        if odd_cycle:
            break

    is_bipartite = len(odd_cycle) == 0
    part0 = sorted(v for v, c in colour.items() if c == 0)
    part1 = sorted(v for v, c in colour.items() if c == 1)

    return {
        "is_bipartite": is_bipartite,
        "partition":    [part0, part1],
        "odd_cycle":    odd_cycle,
        "errors":       [],
    }


def _reconstruct_odd_cycle(u: str, v: str, parent: dict) -> list[str]:
    """Reconstruct cycle from the two endpoints u, v that share a colour."""
    path_u: list[str] = []
    path_v: list[str] = []
    cur = u
    while cur is not None:
        path_u.append(cur)
        cur = parent.get(cur)
    cur = v
    while cur is not None:
        path_v.append(cur)
        cur = parent.get(cur)

    # Find LCA
    set_u = {n: i for i, n in enumerate(path_u)}
    lca = None
    for node in path_v:
        if node in set_u:
            lca = node
            break
    if lca is None:
        return [u, v]

    cycle = path_u[:set_u[lca] + 1]
    branch = []
    for node in path_v:
        branch.append(node)
        if node == lca:
            break
    return cycle + list(reversed(branch[:-1]))


# ===========================================================================
# 5. Graph colouring (greedy + exact by backtracking, n ≤ 8)
# ===========================================================================

def graph_colouring(vertices: list[str], edges: list[tuple]) -> dict:
    """
    Greedy colouring and exact chromatic number by backtracking (n ≤ 8).

    Returns 'greedy_colouring' (dict vertex→colour), 'greedy_colours' (int),
    'chromatic_number' (exact, int), 'exact_colouring' (dict vertex→colour).
    """
    n = len(vertices)
    if n == 0:
        return {
            "greedy_colouring": {}, "greedy_colours": 0,
            "chromatic_number": 0, "exact_colouring": {},
            "errors": [],
        }

    verts = [str(v) for v in vertices]
    adj_set: set[tuple[str, str]] = set()
    for e in edges:
        u, v = str(e[0]), str(e[1])
        adj_set.add((u, v))
        adj_set.add((v, u))

    # Build adjacency for greedy
    adj_g: dict[str, set[str]] = {v: set() for v in verts}
    for (u, v) in adj_set:
        adj_g[u].add(v)

    # Greedy colouring
    greedy: dict[str, int] = {}
    for v in verts:
        used = {greedy[nb] for nb in adj_g[v] if nb in greedy}
        c = 0
        while c in used:
            c += 1
        greedy[v] = c

    greedy_k = max(greedy.values()) + 1 if greedy else 0

    # Exact chromatic number by backtracking (n ≤ 8)
    exact_colouring: dict[str, int] = {}
    chromatic = greedy_k  # upper bound

    if n <= 8:
        for k in range(1, greedy_k + 1):
            result = _backtrack_colour(verts, adj_set, k)
            if result is not None:
                chromatic = k
                exact_colouring = {verts[i]: result[i] for i in range(n)}
                break
    else:
        exact_colouring = greedy
        chromatic = greedy_k

    return {
        "greedy_colouring": {v: greedy[v] for v in verts},
        "greedy_colours":   greedy_k,
        "chromatic_number": chromatic,
        "exact_colouring":  exact_colouring,
        "errors":           [],
    }


def _backtrack_colour(verts, adj_set, k):
    n = len(verts)
    colouring = [-1] * n

    def _is_safe(idx, colour):
        v = verts[idx]
        for j in range(idx):
            nb = verts[j]
            if colouring[j] == colour and ((v, nb) in adj_set or (nb, v) in adj_set):
                return False
        return True

    def _solve(idx):
        if idx == n:
            return True
        for c in range(k):
            if _is_safe(idx, c):
                colouring[idx] = c
                if _solve(idx + 1):
                    return True
                colouring[idx] = -1
        return False

    if _solve(0):
        return colouring
    return None


# ===========================================================================
# 6. Maximum bipartite matching (augmenting paths / Hopcroft-Karp simplified)
# ===========================================================================

def max_matching(left: list[str], right: list[str],
                 edges: list[tuple[str, str]]) -> dict:
    """
    Find maximum matching in a bipartite graph by augmenting paths.
    Also check Hall's marriage condition.

    Parameters
    ----------
    left  : left-side vertices
    right : right-side vertices
    edges : list of (left_vertex, right_vertex) pairs

    Returns
    -------
    dict with 'matching' (list of pairs), 'size', 'hall_satisfied', 'errors'.
    """
    L = [str(v) for v in left]
    R = [str(v) for v in right]
    edge_set = {(str(u), str(v)) for u, v in edges}

    # Build neighbourhood
    nbrs: dict[str, list[str]] = {v: [] for v in L}
    for u, v in edge_set:
        if u in nbrs:
            nbrs[u].append(v)

    match_L: dict[str, str | None] = {v: None for v in L}
    match_R: dict[str, str | None] = {v: None for v in R}

    def _augment(u, visited):
        for v in nbrs[u]:
            if v not in visited:
                visited.add(v)
                if match_R[v] is None or _augment(match_R[v], visited):
                    match_L[u] = v
                    match_R[v] = u
                    return True
        return False

    for u in L:
        _augment(u, set())

    matching = [(u, match_L[u]) for u in L if match_L[u] is not None]

    # Hall's condition check
    hall_satisfied = True
    violating_set: list[str] | None = None
    for r in range(1, len(L) + 1):
        for subset in itertools.combinations(L, r):
            neighbourhood = set()
            for u in subset:
                neighbourhood |= set(nbrs[u])
            if len(neighbourhood) < len(subset):
                hall_satisfied = False
                violating_set = list(subset)
                break
        if not hall_satisfied:
            break

    return {
        "matching":       matching,
        "size":           len(matching),
        "hall_satisfied": hall_satisfied,
        "violating_set":  violating_set,
        "errors":         [],
    }


# ===========================================================================
# 7. Planarity bound check (necessary condition only)
# ===========================================================================

def planarity_bound_check(n_vertices: int, n_edges: int,
                          is_bipartite: bool = False) -> dict:
    """
    Check the necessary condition for planarity:
      - Any planar graph: e ≤ 3v − 6  (v ≥ 3)
      - Bipartite planar graph: e ≤ 2v − 4  (v ≥ 3)

    This is a NECESSARY CONDITION only — passing does not guarantee planarity.

    Parameters
    ----------
    n_vertices, n_edges : non-negative integers
    is_bipartite        : bool
    """
    errors: list[str] = []
    if not isinstance(n_vertices, int) or n_vertices < 0:
        errors.append("n_vertices must be a non-negative integer.")
    if not isinstance(n_edges, int) or n_edges < 0:
        errors.append("n_edges must be a non-negative integer.")
    if errors:
        return {"satisfies_bound": False, "errors": errors}

    if n_vertices < 3:
        return {
            "n_vertices":       n_vertices,
            "n_edges":          n_edges,
            "bound":            None,
            "satisfies_bound":  True,
            "note":             "Bound only applies for v ≥ 3; trivially planar.",
            "errors":           [],
        }

    if is_bipartite:
        bound = 2 * n_vertices - 4
        formula = f"e ≤ 2v − 4 = 2×{n_vertices} − 4 = {bound}"
    else:
        bound = 3 * n_vertices - 6
        formula = f"e ≤ 3v − 6 = 3×{n_vertices} − 6 = {bound}"

    satisfies = n_edges <= bound

    return {
        "n_vertices":      n_vertices,
        "n_edges":         n_edges,
        "bound":           bound,
        "formula":         formula,
        "satisfies_bound": satisfies,
        "is_bipartite":    is_bipartite,
        "note":            (
            "This is a necessary condition only — satisfying the bound "
            "does not prove planarity."
        ),
        "errors": [],
    }


# ===========================================================================
# 8. Tree check
# ===========================================================================

def tree_check(vertices: list[str], edges: list[tuple]) -> dict:
    """
    Check whether the graph is a tree: connected and has exactly n-1 edges.

    Also reports leaves (degree 1 vertices).
    """
    n = len(vertices)
    e = len(edges)
    if n == 0:
        return {"is_tree": True, "leaves": [], "n": 0, "e": 0, "errors": []}

    from algorithms.network import is_connected
    connected = is_connected(vertices, edges)
    is_tree = connected and e == n - 1
    deg = {str(v): 0 for v in vertices}
    for edge in edges:
        u, v = str(edge[0]), str(edge[1])
        if u in deg:
            deg[u] += 1
        if v in deg:
            deg[v] += 1

    leaves = sorted(v for v, d in deg.items() if d == 1)

    return {
        "is_tree":   is_tree,
        "connected": connected,
        "n":         n,
        "e":         e,
        "n_minus_1": n - 1,
        "leaves":    leaves,
        "errors":    [],
    }
