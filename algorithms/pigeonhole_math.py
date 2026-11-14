"""Pigeonhole helpers for the Pigeonhole page. Pure Python, no Streamlit."""
from __future__ import annotations

from itertools import combinations
from math import isqrt


def pigeonhole_min(n_items, m_holes):
    """Smallest possible size of the fullest hole: ceil(n / m)."""
    if (isinstance(n_items, bool) or isinstance(m_holes, bool)
            or not isinstance(n_items, int) or not isinstance(m_holes, int)):
        raise ValueError("n and m must be whole numbers.")
    if n_items < 0 or m_holes < 1:
        raise ValueError("n must be 0 or more and m must be at least 1.")
    return -(-n_items // m_holes)


def solar_bands(values, m):
    """Equal-width bands over 0-100 %; returns a band number 0..m-1 for each value."""
    if m < 1:
        raise ValueError("There must be at least one band.")
    width = 100 / m
    out = []
    for v in values:
        v = float(v)
        if v < 0 or v > 100:
            raise ValueError("Solar potential must be between 0 and 100.")
        out.append(min(m - 1, int(v // width)))
    return out


def hole_contents(names, holes, m):
    contents = [[] for _ in range(m)]
    for name, h in zip(names, holes):
        contents[h].append(name)
    return contents


def fullest(contents):
    sizes = [len(c) for c in contents]
    return sizes.index(max(sizes)) if sizes else None


# ---------------------------------------------------------------- Ramsey ----

def mono_triple(n, colour):
    """First trio whose three connections share one colour, or None.
    colour maps (i, j) with i < j to 0 or 1."""
    for a, b, c in combinations(range(n), 3):
        if colour[(a, b)] == colour[(a, c)] == colour[(b, c)]:
            return (a, b, c)
    return None


def ramsey_scan(n):
    """Try every 2-colouring of the connections between n buildings (n = 5 or 6)."""
    if n not in (5, 6):
        raise ValueError("Only 5 or 6 buildings can be scanned.")
    edges = list(combinations(range(n), 2))
    index = {e: i for i, e in enumerate(edges)}
    trios = [(index[(a, b)], index[(a, c)], index[(b, c)])
             for a, b, c in combinations(range(n), 3)]
    free = 0
    example = None
    for mask in range(1 << len(edges)):
        ok = True
        for x, y, z in trios:
            bx, by, bz = (mask >> x) & 1, (mask >> y) & 1, (mask >> z) & 1
            if bx == by == bz:
                ok = False
                break
        if ok:
            free += 1
            if example is None:
                example = {edges[i]: (mask >> i) & 1 for i in range(len(edges))}
    return {"n": n, "total": 1 << len(edges), "free": free, "example": example}


def campus_colouring(names, pairs):
    """1 if two of the named buildings can be connected, else 0."""
    idx = {n: i for i, n in enumerate(names)}
    connected = {tuple(sorted((idx[u], idx[v]))) for u, v in pairs
                 if u in idx and v in idx and u != v}
    return {e: 1 if e in connected else 0
            for e in combinations(range(len(names)), 2)}


# ---------------------------------------------------------------- Mantel ----

def mantel_bound(n):
    if n < 0:
        raise ValueError("n must be 0 or more.")
    return n * n // 4


def find_triangles(vertices, pairs):
    adj = {v: set() for v in vertices}
    for u, v in pairs:
        if u in adj and v in adj and u != v:
            adj[u].add(v)
            adj[v].add(u)
    out = []
    for a, b, c in combinations(sorted(vertices), 3):
        if b in adj[a] and c in adj[a] and c in adj[b]:
            out.append((a, b, c))
    return out


def complete_bipartite(names):
    """Split the names into two halves and join every left name to every right name."""
    names = list(names)
    half = len(names) // 2
    left, right = names[:half], names[half:]
    return left, right, [(u, v) for u in left for v in right]


# ------------------------------------------------------- Erdos-Szekeres ----

def longest_monotone(seq):
    """Indices of a longest strictly increasing and a longest strictly decreasing run."""
    n = len(seq)
    if n == 0:
        return {"increasing": [], "decreasing": []}

    def best(better):
        length = [1] * n
        prev = [-1] * n
        for i in range(n):
            for j in range(i):
                if better(seq[j], seq[i]) and length[j] + 1 > length[i]:
                    length[i] = length[j] + 1
                    prev[i] = j
        end = max(range(n), key=lambda i: length[i])
        path = []
        while end != -1:
            path.append(end)
            end = prev[end]
        return path[::-1]

    return {"increasing": best(lambda a, b: a < b),
            "decreasing": best(lambda a, b: a > b)}


def es_k(n):
    """Largest k with k*k + 1 <= n."""
    return isqrt(n - 1) if n >= 1 else 0


def es_guarantee(n):
    """Any n different numbers contain a monotone run of at least this length."""
    return es_k(n) + 1 if n >= 1 else 0