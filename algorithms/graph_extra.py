"""Validation and exact checks for the Graph Theory page. No Streamlit."""
from __future__ import annotations

MAX_V = 8


def _canon(u, v):
    return (u, v) if u <= v else (v, u)


def parse_graph(vertex_text, edge_text, directed=False):
    errors, warnings, verts = [], [], []
    for x in vertex_text.replace(";", ",").split(","):
        x = x.strip()
        if not x:
            continue
        if len(x) > 12:
            errors.append(f"Vertex name '{x[:12]}…' is longer than 12 characters.")
        elif x in verts:
            errors.append(f"Vertex {x} is listed twice.")
        else:
            verts.append(x)
    if not verts:
        errors.append("Enter at least one vertex.")
    if len(verts) > MAX_V:
        errors.append(f"Use at most {MAX_V} vertices.")
    edges, seen = [], set()
    for i, line in enumerate(edge_text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 2 or not all(parts):
            errors.append(f"Edge line {i}: write it as u,v.")
            continue
        u, v = parts
        bad = u if u not in verts else (v if v not in verts else None)
        if bad:
            errors.append(f"Edge line {i}: {bad} is not a listed vertex.")
            continue
        if u == v:
            errors.append(f"Edge line {i}: a vertex cannot connect to itself.")
            continue
        key = (u, v) if directed else _canon(u, v)
        if key in seen:
            warnings.append(f"Edge line {i}: {u},{v} repeated, counted once.")
            continue
        seen.add(key)
        edges.append(key)
    und = sorted({_canon(u, v) for u, v in edges})
    return {"errors": errors, "warnings": warnings, "vertices": sorted(verts),
            "edges": edges, "und": und}


def parse_matching(left_text, right_text, edge_text):
    errors = []

    def names(text, label):
        out = []
        for x in text.split(","):
            x = x.strip()
            if not x:
                continue
            if x in out:
                errors.append(f"{label}: {x} appears twice.")
            else:
                out.append(x)
        if not out:
            errors.append(f"The {label.lower()} side needs at least one vertex.")
        if len(out) > MAX_V:
            errors.append(f"The {label.lower()} side can have at most {MAX_V} vertices.")
        return out

    L, R = names(left_text, "Left"), names(right_text, "Right")
    both = set(L) & set(R)
    if both:
        errors.append("A name cannot be on both sides: " + ", ".join(sorted(both)) + ".")
    edges, seen = [], set()
    for i, line in enumerate(edge_text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 2 or not all(parts):
            errors.append(f"Edge line {i}: write it as left,right.")
            continue
        a, b = parts
        if a in R and b in L:
            a, b = b, a
        if a not in L or b not in R:
            errors.append(f"Edge line {i}: each edge must join a left vertex to a right vertex.")
            continue
        if (a, b) not in seen:
            seen.add((a, b))
            edges.append((a, b))
    return {"errors": errors, "left": L, "right": R, "edges": sorted(edges)}


def hamiltonian(vertices, edges):
    verts = sorted(str(v) for v in vertices)
    n = len(verts)
    if n == 0 or n > MAX_V:
        return {"cycle": [], "path": [], "n": n, "errors": [f"Use between 1 and {MAX_V} vertices."]}
    adj = {v: set() for v in verts}
    for u, v in edges:
        if u != v and u in adj and v in adj:
            adj[u].add(v)
            adj[v].add(u)

    def search(path, need_cycle):
        if len(path) == n:
            if not need_cycle:
                return path
            return path + [path[0]] if path[0] in adj[path[-1]] else None
        for v in sorted(adj[path[-1]]):
            if v not in path:
                r = search(path + [v], need_cycle)
                if r:
                    return r
        return None

    cycle = (search([verts[0]], True) or []) if n >= 3 else []
    path = []
    for s in verts:
        path = search([s], False) or []
        if path:
            break
    return {"cycle": cycle, "path": path, "n": n, "errors": []}


def dirac(n, degrees):
    """Sufficient (not necessary) condition for a Hamiltonian cycle."""
    return n >= 3 and bool(degrees) and 2 * min(degrees) >= n


def verify_euler(seq, edges, closed):
    if len(seq) != len(edges) + 1 or (closed and seq[0] != seq[-1]):
        return False
    used = sorted(_canon(a, b) for a, b in zip(seq, seq[1:]))
    return used == sorted(_canon(u, v) for u, v in edges)


def verify_hamiltonian(seq, vertices, edges, cycle):
    n = len(vertices)
    if cycle and (len(seq) != n + 1 or seq[0] != seq[-1]):
        return False
    body = seq[:-1] if cycle else seq
    if sorted(body) != sorted(vertices):
        return False
    es = {_canon(u, v) for u, v in edges}
    return all(_canon(a, b) in es for a, b in zip(seq, seq[1:]))


def verify_bipartition(edges, parts):
    side = {v: i for i, part in enumerate(parts) for v in part}
    return all(u in side and v in side and side[u] != side[v] for u, v in edges)


def verify_odd_cycle(cycle, edges):
    if len(cycle) < 3 or len(cycle) % 2 == 0 or len(set(cycle)) != len(cycle):
        return False
    es = {_canon(u, v) for u, v in edges}
    ring = list(cycle) + [cycle[0]]
    return all(_canon(a, b) in es for a, b in zip(ring, ring[1:]))


def verify_colouring(edges, colouring):
    return [e for e in edges
            if e[0] in colouring and e[1] in colouring and colouring[e[0]] == colouring[e[1]]]


def verify_matching(matching, edges):
    es = set(edges)
    lefts = [u for u, _ in matching]
    rights = [v for _, v in matching]
    return (all((u, v) in es for u, v in matching)
            and len(set(lefts)) == len(lefts) and len(set(rights)) == len(rights))