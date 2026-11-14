"""
pigeonhole.py — Pigeonhole principle, Ramsey R(3,3), Mantel theorem,
                and Erdos-Szekeres monotone subsequence.

No Streamlit imports. No eval(). All results computed from data.
"""

from __future__ import annotations
import math
import itertools
from functools import lru_cache
from typing import Any



# ===========================================================================
# 1. Basic pigeonhole principle
# ===========================================================================

def pigeonhole(n_items: int, n_boxes: int) -> dict:
    """
    Pigeonhole principle: if n_items go into n_boxes, at least one box holds
    ceil(n_items / n_boxes) items.

    Parameters
    ----------
    n_items : int >= 1
    n_boxes : int >= 1

    Returns
    -------
    dict with 'guaranteed', 'statement', 'errors'.
    """
    errors: list[str] = []
    if not isinstance(n_items, int) or n_items < 1:
        errors.append(f"n_items must be a positive integer (got {n_items!r}).")
    if not isinstance(n_boxes, int) or n_boxes < 1:
        errors.append(f"n_boxes must be a positive integer (got {n_boxes!r}).")
    if errors:
        return {"guaranteed": 0, "statement": "", "errors": errors}

    guaranteed = math.ceil(n_items / n_boxes)
    statement = (
        f"With {n_items} items in {n_boxes} boxes, at least one box contains "
        f"⌈{n_items}/{n_boxes}⌉ = {guaranteed} item(s)."
    )
    return {"guaranteed": guaranteed, "statement": statement, "errors": []}


def generalized_pigeonhole(n_items: int, n_boxes: int) -> dict:
    """
    Generalized pigeonhole: at least one box holds at least ⌊(n-1)/m⌋ + 1 items.
    (Same as ceil(n/m) for positive integers, derived differently.)

    Also computes the minimum n needed to guarantee t items in one box.
    """
    errors: list[str] = []
    if not isinstance(n_items, int) or n_items < 1:
        errors.append(f"n_items must be a positive integer (got {n_items!r}).")
    if not isinstance(n_boxes, int) or n_boxes < 1:
        errors.append(f"n_boxes must be a positive integer (got {n_boxes!r}).")
    if errors:
        return {"guaranteed": 0, "min_for_t": {}, "errors": errors}

    guaranteed = (n_items - 1) // n_boxes + 1
    # For t = 1..5, minimum items needed to guarantee t in one box
    min_for_t = {t: n_boxes * (t - 1) + 1 for t in range(1, 6)}

    return {
        "guaranteed": guaranteed,
        "formula":    f"⌊({n_items}-1)/{n_boxes}⌋ + 1 = {guaranteed}",
        "min_for_t":  min_for_t,
        "errors":     [],
    }


def campus_pigeonhole_demo(building_solars: list[float], n_bands: int = 3) -> dict:
    """
    Assign buildings to solar-percentage bands and show which band must hold
    at least ceil(n/n_bands) buildings (pigeonhole guarantee).

    Parameters
    ----------
    building_solars : list of solar_potential_pct values (0–100)
    n_bands         : number of equal-width bands (default 3: low/mid/high)

    Returns
    -------
    dict with band assignments, guarantee, and verified largest band.
    """
    errors: list[str] = []
    if not building_solars:
        errors.append("No buildings provided.")
        return {"bands": {}, "guaranteed": 0, "actual_max": 0, "errors": errors}
    if not isinstance(n_bands, int) or n_bands < 1:
        errors.append("n_bands must be a positive integer.")
        return {"bands": {}, "guaranteed": 0, "actual_max": 0, "errors": errors}

    n = len(building_solars)
    guaranteed = math.ceil(n / n_bands)
    band_width = 100.0 / n_bands

    bands: dict[str, list[float]] = {}
    for i in range(n_bands):
        lo = i * band_width
        hi = (i + 1) * band_width
        label = f"{lo:.0f}–{hi:.0f}%"
        bands[label] = []

    for val in building_solars:
        idx = min(int(val / band_width), n_bands - 1)
        lo = idx * band_width
        hi = (idx + 1) * band_width
        label = f"{lo:.0f}–{hi:.0f}%"
        bands[label].append(val)

    actual_max = max(len(v) for v in bands.values()) if bands else 0
    largest_band = max(bands, key=lambda k: len(bands[k])) if bands else ""

    return {
        "n":            n,
        "n_bands":      n_bands,
        "guaranteed":   guaranteed,
        "actual_max":   actual_max,
        "largest_band": largest_band,
        "bands":        bands,
        "errors":       [],
    }


# ===========================================================================
# 2. Ramsey R(3,3) = 6  (brute force over K5 and K6)
# ===========================================================================

def _has_monochromatic_triangle(n: int, coloring: dict) -> bool:
    """
    Return True if the 2-coloring of K_n has a monochromatic triangle.
    coloring maps frozenset({u,v}) -> 0 or 1.
    """
    for a, b, c in itertools.combinations(range(n), 3):
        e1 = coloring.get(frozenset({a, b}), 0)
        e2 = coloring.get(frozenset({b, c}), 0)
        e3 = coloring.get(frozenset({a, c}), 0)
        if e1 == e2 == e3:
            return True
    return False


def ramsey_r33_brute_force() -> dict:
    """
    Verify R(3,3) = 6 by exhaustive search over all 2-colourings of K5 and K6.

    - K5: there EXISTS a 2-colouring with no monochromatic triangle → R(3,3) > 5
    - K6: EVERY 2-colouring has a monochromatic triangle → R(3,3) ≤ 6

    Returns
    -------
    dict with:
        'k5_counterexample_coloring'   : dict  — one coloring of K5 with no mono-triangle
        'k5_has_good_coloring'         : bool
        'k6_all_have_mono_triangle'    : bool
        'k6_colorings_checked'         : int
        'conclusion'                   : str
        'errors'                       : list[str]
    """
    # K5 check — find a coloring with no monochromatic triangle
    edges5 = [frozenset({u, v}) for u, v in itertools.combinations(range(5), 2)]
    k5_good: dict | None = None
    for bits in range(2 ** len(edges5)):
        coloring = {e: (bits >> i) & 1 for i, e in enumerate(edges5)}
        if not _has_monochromatic_triangle(5, coloring):
            k5_good = {f"{min(e)}-{max(e)}": coloring[e] for e in edges5}
            break

    # K6 check — all colorings must have a monochromatic triangle
    edges6 = [frozenset({u, v}) for u, v in itertools.combinations(range(6), 2)]
    k6_all = True
    k6_count = 0
    # 2^15 = 32768 colorings — feasible
    for bits in range(2 ** len(edges6)):
        coloring = {e: (bits >> i) & 1 for i, e in enumerate(edges6)}
        k6_count += 1
        if not _has_monochromatic_triangle(6, coloring):
            k6_all = False
            break

    conclusion = (
        "R(3,3) = 6: K₅ has a valid 2-colouring with no monochromatic triangle, "
        "but every 2-colouring of K₆ contains one."
    )

    return {
        "k5_counterexample_coloring": k5_good,
        "k5_has_good_coloring":       k5_good is not None,
        "k6_all_have_mono_triangle":  k6_all,
        "k6_colorings_checked":       k6_count,
        "conclusion":                 conclusion,
        "errors":                     [],
    }


# ===========================================================================
# 3. Mantel's theorem: max edges in triangle-free graph on n vertices = ⌊n²/4⌋
# ===========================================================================

def _is_triangle_free(n: int, edges: set) -> bool:
    adj = {v: set() for v in range(n)}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    for u in range(n):
        for v in adj[u]:
            if adj[u] & adj[v]:
                return False
    return True


def mantel_theorem(n: int) -> dict:
    """
    Verify Mantel's theorem: the maximum number of edges in a triangle-free
    graph on n vertices is ⌊n²/4⌋, achieved by the complete bipartite graph K_{⌊n/2⌋,⌈n/2⌉}.

    Brute-force verification for n ≤ 6.

    Parameters
    ----------
    n : int in [2, 6]
    """
    errors: list[str] = []
    if not isinstance(n, int) or n < 2 or n > 6:
        errors.append("n must be an integer between 2 and 6 for brute-force verification.")
        return {"n": n, "mantel_bound": 0, "brute_force_max": 0, "match": False, "errors": errors}

    mantel_bound = n * n // 4
    all_edges = list(itertools.combinations(range(n), 2))
    brute_force_max = 0

    # Enumerate all subsets of edges
    for r in range(len(all_edges) + 1):
        found = False
        for edge_subset in itertools.combinations(all_edges, r):
            if _is_triangle_free(n, set(edge_subset)):
                brute_force_max = r
                found = True
        if not found:
            break

    # Re-scan correctly: find the actual max
    brute_force_max = 0
    for r in range(len(all_edges), -1, -1):
        for edge_subset in itertools.combinations(all_edges, r):
            if _is_triangle_free(n, set(edge_subset)):
                brute_force_max = r
                break
        else:
            continue
        break

    return {
        "n":               n,
        "mantel_bound":    mantel_bound,
        "brute_force_max": brute_force_max,
        "match":           mantel_bound == brute_force_max,
        "formula":         f"⌊{n}²/4⌋ = ⌊{n*n}/4⌋ = {mantel_bound}",
        "errors":          [],
    }


# ===========================================================================
# 4. Erdos-Szekeres monotone subsequence theorem
# ===========================================================================

def _longest_increasing(seq: list) -> list:
    """Return one longest increasing subsequence (patience sorting)."""
    if not seq:
        return []
    n = len(seq)
    parent = [-1] * n
    tails = []   # tails[i] = index of smallest tail for IS of length i+1
    for i, val in enumerate(seq):
        lo, hi = 0, len(tails)
        while lo < hi:
            mid = (lo + hi) // 2
            if seq[tails[mid]] < val:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(tails):
            tails.append(i)
        else:
            tails[lo] = i
        parent[i] = tails[lo - 1] if lo > 0 else -1
    # Reconstruct
    path = []
    idx = tails[-1]
    while idx != -1:
        path.append(seq[idx])
        idx = parent[idx]
    return list(reversed(path))


def _longest_decreasing(seq: list) -> list:
    return _longest_increasing([-x for x in seq])


def erdos_szekeres_demo(sequence: list[int]) -> dict:
    """
    Erdos-Szekeres theorem: any sequence of more than k² distinct integers
    has a monotone subsequence of length > k.

    For an input of length n = k²+1, there must be a monotone subsequence
    of length ≥ k+1 = ⌈√n⌉.

    Parameters
    ----------
    sequence : list of distinct integers, length 2–30.

    Returns
    -------
    dict with LIS length, LDS length, theorem guarantee, and errors.
    """
    errors: list[str] = []
    if not isinstance(sequence, list):
        errors.append("sequence must be a list of integers.")
        return {"lis": [], "lds": [], "guarantee": 0, "errors": errors}
    n = len(sequence)
    if n < 2 or n > 30:
        errors.append("Sequence must have 2 to 30 elements.")
        return {"lis": [], "lds": [], "guarantee": 0, "errors": errors}
    if len(set(sequence)) != n:
        errors.append("All elements of the sequence must be distinct.")
        return {"lis": [], "lds": [], "guarantee": 0, "errors": errors}

    lis = _longest_increasing(sequence)
    lds = _longest_decreasing(sequence)
    guarantee = math.ceil(math.sqrt(n))   # guaranteed length ≥ ceil(sqrt(n))
    actual_max = max(len(lis), len(lds))

    return {
        "n":         n,
        "lis":       lis,
        "lds":       lds,
        "guarantee": guarantee,
        "actual_max": actual_max,
        "theorem_satisfied": actual_max >= guarantee,
        "statement": (
            f"A sequence of {n} distinct integers must have a monotone "
            f"subsequence of length ≥ ⌈√{n}⌉ = {guarantee}."
        ),
        "errors": [],
    }


# ===========================================================================
# 5. Pigeons and holes — the campus buildings dropped into m holes
# ===========================================================================

def holes_overview(labels, values, n_holes: int, mode: str = "bands") -> dict:
    """
    Sort the campus buildings into *n_holes* groups and report the fullest.

    Parameters
    ----------
    labels  : building names, in the order they should be shown.
    values  : one number per building (the solar potential, 0–100, when
              ``mode == "bands"``); ignored when ``mode == "crews"``.
    n_holes : number of holes (bands in "bands" mode, crews in "crews" mode).
    mode    : "bands" — equal-width solar-potential bands over 0–100%;
              "crews" — surviving crews, filled round-robin in label order.

    Returns
    -------
    dict with 'n', 'm', 'mode', 'holes', 'fullest', 'guaranteed', 'actual_max',
    'statement', 'errors'.
    """
    names = [str(x) for x in (labels or [])]
    errors: list[str] = []
    if not names:
        errors.append("No buildings provided.")
    if not isinstance(n_holes, int) or isinstance(n_holes, bool) or n_holes < 1:
        errors.append("n_holes must be a positive integer.")
    if mode not in ("bands", "crews"):
        errors.append("mode must be 'bands' or 'crews'.")
    if errors:
        return {"n": len(names), "m": n_holes, "mode": mode, "holes": [],
                "fullest": None, "guaranteed": 0, "actual_max": 0,
                "statement": "", "errors": errors}

    values = list(values or [])
    n = len(names)
    holes: list = []

    if mode == "bands":
        if len(values) < n:
            return {"n": n, "m": n_holes, "mode": mode, "holes": [],
                    "fullest": None, "guaranteed": 0, "actual_max": 0,
                    "statement": "", "errors": ["one solar value per building is required."]}
        width = 100.0 / n_holes
        for i in range(n_holes):
            lo, hi = i * width, (i + 1) * width
            holes.append({"label": f"{lo:.0f}–{hi:.0f}%", "members": [],
                          "lo": round(lo, 1), "hi": round(hi, 1)})
        for name, val in zip(names, values):
            idx = min(int(float(val) / width), n_holes - 1)
            idx = max(idx, 0)
            holes[idx]["members"].append(name)
    else:
        for i in range(n_holes):
            holes.append({"label": f"Crew {i + 1}", "members": []})
        for i, name in enumerate(names):
            holes[i % n_holes]["members"].append(name)

    for hole in holes:
        hole["count"] = len(hole["members"])

    guaranteed = math.ceil(n / n_holes)
    actual_max = max((h["count"] for h in holes), default=0)
    fullest = max(range(n_holes), key=lambda i: holes[i]["count"])
    fullest_label = holes[fullest]["label"]

    if mode == "bands":
        statement = (
            f"{n} buildings spread over {n_holes} solar-potential bands: at least one "
            f"band holds ⌈{n}/{n_holes}⌉ = {guaranteed} building(s)."
        )
    else:
        statement = (
            f"{n} buildings allotted to {n_holes} crews: at least one crew takes "
            f"⌈{n}/{n_holes}⌉ = {guaranteed} building(s)."
        )

    return {
        "n": n,
        "m": n_holes,
        "mode": mode,
        "holes": holes,
        "fullest": fullest,
        "fullest_label": fullest_label,
        "guaranteed": guaranteed,
        "actual_max": actual_max,
        "statement": statement,
        "errors": [],
    }


# ===========================================================================
# 6. Ramsey R(3,3) — a two-colouring of the campus ring
# ===========================================================================

def _find_mono_triangle(n: int, coloring: dict):
    """Return ``((a, b, c), colour)`` for a monochromatic triangle, else (None, None)."""
    for a, b, c in itertools.combinations(range(n), 3):
        c1 = coloring.get(frozenset({a, b}), 0)
        c2 = coloring.get(frozenset({b, c}), 0)
        c3 = coloring.get(frozenset({a, c}), 0)
        if c1 == c2 == c3:
            return (a, b, c), c1
    return None, None


# The table below answers "which triple is joined in one colour?" for every
# two-colouring of K_n, so the page never has to search in the browser.
MONO_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
NO_TRIANGLE = "."


@lru_cache(maxsize=8)
def mono_triangle_table(n: int) -> str:
    """
    One character per two-colouring of the complete graph on *n* vertices.

    Bit *i* of the mask colours the *i*-th pair of ``combinations(range(n), 2)``
    (0 = first colour, 1 = second).  A character of ``.`` marks a colouring with
    no monochromatic triangle; otherwise the character is
    ``MONO_ALPHABET[2 * position + colour]`` where *position* indexes the
    triangle in ``combinations(range(n), 3)``.

    Every possible colouring is answered once, in Python, so the browser only
    reads the answer out of this string.
    """
    pairs = list(itertools.combinations(range(n), 2))
    triples = list(itertools.combinations(range(n), 3))
    edge_index = {pair: i for i, pair in enumerate(pairs)}
    triple_edges = [
        (edge_index[(a, b)], edge_index[(a, c)], edge_index[(b, c)])
        for a, b, c in triples
    ]
    chars = []
    for mask in range(1 << len(pairs)):
        code = NO_TRIANGLE
        for position, (e1, e2, e3) in enumerate(triple_edges):
            c1 = (mask >> e1) & 1
            c2 = (mask >> e2) & 1
            c3 = (mask >> e3) & 1
            if c1 == c2 == c3:
                code = MONO_ALPHABET[2 * position + c1]
                break
        chars.append(code)
    return "".join(chars)


def mono_triangle_from_mask(n: int, mask: int):
    """
    Read :func:`mono_triangle_table` for one colouring mask.

    Returns ``(triangle, colour)`` where *triangle* is a list of three vertex
    indices and *colour* is 0 or 1, or ``(None, None)`` when the colouring has
    no monochromatic triangle.
    """
    table = mono_triangle_table(n)
    if not isinstance(mask, int) or mask < 0 or mask >= len(table):
        return None, None
    char = table[mask]
    if char == NO_TRIANGLE:
        return None, None
    code = MONO_ALPHABET.index(char)
    triangles = list(itertools.combinations(range(n), 3))
    return list(triangles[code // 2]), code % 2


def k5_counterexample_coloring() -> dict | None:
    """
    Search all 2^10 colourings of K5 for one with no monochromatic triangle.

    Returns the first such colouring as ``{"0-1": 0, "0-2": 1, ...}`` or None.
    """
    edges = [frozenset({u, v}) for u, v in itertools.combinations(range(5), 2)]
    for bits in range(2 ** len(edges)):
        coloring = {e: (bits >> i) & 1 for i, e in enumerate(edges)}
        if not _has_monochromatic_triangle(5, coloring):
            return {f"{min(e)}-{max(e)}": coloring[e] for e in edges}
    return None


@lru_cache(maxsize=1)
def ramsey_k6_all_colourings() -> dict:
    """
    Check every one of the 2^15 two-colourings of K6 for a monochromatic triangle.

    Returns
    -------
    dict with 'colourings_checked', 'without_mono_triangle',
    'all_have_mono_triangle', 'conclusion'.
    """
    table = mono_triangle_table(6)
    without = table.count(NO_TRIANGLE)
    checked = len(table)
    return {
        "colourings_checked":      checked,
        "without_mono_triangle":   without,
        "all_have_mono_triangle":  without == 0,
        "conclusion": (
            f"All {checked:,} two-colourings of six buildings (K6) contain a "
            f"triple joined in one colour, so R(3,3) ≤ 6; five buildings do not, "
            f"so R(3,3) > 5. Therefore R(3,3) = 6."
        ),
    }


def ramsey_ring(n: int, vertices, edges=None):
    """
    Two-colour the complete graph on the first *n* vertices and find a
    monochromatic triangle.

    For ``n == 6`` the colour follows the campus connection list ("can be
    connected" versus "cannot"); for ``n == 5`` a colouring with no
    monochromatic triangle is used, which is why R(3,3) is not 5.

    Returns
    -------
    dict with 'n', 'vertices', 'colour_labels', 'edges' (``{a, b, colour}``),
    'mono_triangle', 'mono_colour', 'from_data', 'note', 'result_line',
    'mask' (the colouring as a bit mask), 'pairs' (the pair order the mask
    follows), 'mono_table' (see :func:`mono_triangle_table`), 'triples',
    'alphabet', 'no_triangle', 'errors'.
    """
    names = [str(v) for v in (vertices or [])][:n]
    if len(names) < n:
        return {"n": n, "vertices": [], "edges": [], "mono_triangle": None,
                "mono_colour": None, "from_data": False, "note": "",
                "result_line": "", "errors": ["not enough buildings for this ring."]}

    pairs = [(a, b) for a, b in itertools.combinations(range(n), 2)]
    table = mono_triangle_table(n)
    check = ramsey_k6_all_colourings()

    if n == 6:
        connected = set()
        for edge in (edges or []):
            try:
                u, v = str(edge[0]), str(edge[1])
            except (TypeError, IndexError, KeyError):
                continue
            if u in names and v in names and u != v:
                connected.add(frozenset({u, v}))
        mask = 0
        for i, (a, b) in enumerate(pairs):
            if frozenset({names[a], names[b]}) not in connected:
                mask |= 1 << i
        from_data = True
        note = ("Each pair is coloured by the campus connections: green means the "
                "two buildings can be connected, grey means they cannot.")
    else:
        mask = table.index(NO_TRIANGLE)
        from_data = False
        note = ("This is one searched colouring of five buildings; it has no triple "
                "joined in a single colour, which is why five buildings are not enough.")

    tri, colour = mono_triangle_from_mask(n, mask)

    colour_names = {0: "can be connected", 1: "cannot be connected"}
    edge_list = [{"a": a, "b": b, "colour": (mask >> i) & 1}
                 for i, (a, b) in enumerate(pairs)]

    if tri is None:
        result_line = (f"This colouring of {n} buildings has no triple joined in one "
                       f"colour.")
    else:
        result_line = (
            f"Triple all in one colour: {names[tri[0]]}, {names[tri[1]]} and "
            f"{names[tri[2]]} — all '{colour_names[colour]}'."
        )

    return {
        "n": n,
        "vertices": names,
        "colour_labels": {"can": colour_names[0], "cannot": colour_names[1]},
        "edges": edge_list,
        "mono_triangle": list(tri) if tri else None,
        "mono_colour": colour,
        "from_data": from_data,
        "note": note,
        "result_line": result_line,
        "k6_check": check,
        "mask": mask,
        "pairs": [list(pair) for pair in pairs],
        "mono_table": table,
        "triples": [list(t) for t in itertools.combinations(range(n), 3)],
        "alphabet": MONO_ALPHABET,
        "no_triangle": NO_TRIANGLE,
        "errors": [],
    }


# ===========================================================================
# 7. Mantel's theorem on the campus connection list
# ===========================================================================

def _triangles(n: int, edge_set) -> list:
    """Return every triangle of the graph on *n* vertices with edges *edge_set*."""
    adj = {v: set() for v in range(n)}
    for u, v in edge_set:
        adj[u].add(v)
        adj[v].add(u)
    out = []
    for a, b, c in itertools.combinations(range(n), 3):
        if b in adj[a] and c in adj[a] and c in adj[b]:
            out.append((a, b, c))
    return out


def mantel_playground(vertices, edges) -> dict:
    """
    Mantel's theorem on the campus graph, prepared for interactive removal.

    Every subset of the campus connection list is scored once, in Python, so
    the browser only has to look a state up:

        * how many connections are left,
        * whether any triangle remains,
        * whether the count is within ⌊n²/4⌋.

    Parameters
    ----------
    vertices : building names (the first six are used).
    edges    : campus connection pairs.

    Returns
    -------
    dict with 'n', 'vertices', 'edges', 'states', 'bound', 'bounds',
    'k33', 'campus_triangles', 'errors'.
    """
    names = [str(v) for v in (vertices or [])][:6]
    n = len(names)
    errors: list[str] = []
    if n < 2:
        return {"n": n, "vertices": names, "edges": [], "states": [], "bound": 0,
                "bounds": {5: 6, 6: 9}, "k33": None, "campus_triangles": [],
                "errors": ["at least two buildings are needed."]}

    index = {name: i for i, name in enumerate(names)}
    campus: list = []
    for edge in (edges or []):
        try:
            u, v = str(edge[0]), str(edge[1])
        except (TypeError, IndexError, KeyError):
            continue
        if u in index and v in index and u != v:
            a, b = index[u], index[v]
            pair = (a, b) if a < b else (b, a)
            if pair not in campus:
                campus.append(pair)
    campus.sort()

    bound = n * n // 4

    states = []
    for mask in range(1 << len(campus)):
        subset = {campus[i] for i in range(len(campus)) if (mask >> i) & 1}
        tri = _triangles(n, subset)
        states.append({
            "mask":          mask,
            "count":         len(subset),
            "triangles":     [list(t) for t in tri],
            "triangle_free": len(tri) == 0,
            "within_bound":  len(subset) <= bound,
        })

    k33 = None
    if n == 6:
        left, right = [0, 1, 2], [3, 4, 5]
        k_edges = [[a, b] for a in left for b in right]
        k33 = {
            "left":          left,
            "right":         right,
            "edges":         k_edges,
            "count":         len(k_edges),
            "triangle_free": True,
            "bound":         bound,
        }

    return {
        "n": n,
        "vertices": names,
        "edges": [[a, b] for a, b in campus],
        "states": states,
        "bound": bound,
        "bounds": {5: 6, 6: 9},
        "k33": k33,
        "campus_triangles": [list(t) for t in _triangles(n, set(campus))],
        "errors": errors,
    }


# ===========================================================================
# 8. Erdos-Szekeres — longest monotone run in the campus demands
# ===========================================================================

def _longest_nondecreasing(seq: list) -> list:
    """Longest non-decreasing subsequence of *seq* (O(n²), fine for ≤ 30)."""
    if not seq:
        return []
    best = [1] * len(seq)
    parent = [-1] * len(seq)
    for i in range(len(seq)):
        for j in range(i):
            if seq[j] <= seq[i] and best[j] + 1 > best[i]:
                best[i] = best[j] + 1
                parent[i] = j
    end = max(range(len(seq)), key=lambda i: best[i])
    path = []
    while end != -1:
        path.append(seq[end])
        end = parent[end]
    return list(reversed(path))


def _longest_nonincreasing(seq: list) -> list:
    """Longest non-increasing subsequence of *seq* (values, in order)."""
    return [-x for x in _longest_nondecreasing([-x for x in seq])]


def monotone_runs(sequence) -> dict:
    """
    Longest non-decreasing and non-increasing runs in *sequence*.

    Equal neighbours are allowed, so repeated demands do not break the
    theorem (which holds for ≤ as well as <).

    Parameters
    ----------
    sequence : list of numbers, length 2–30.

    Returns
    -------
    dict with 'n', 'increase' (indices), 'decrease' (indices), 'increase_values',
    'decrease_values', 'guarantee', 'actual_max', 'theorem_satisfied',
    'statement', 'errors'.
    """
    errors: list[str] = []
    if not isinstance(sequence, (list, tuple)) or len(sequence) < 2:
        errors.append("the sequence must hold at least two numbers.")
        return {"n": 0, "increase": [], "decrease": [], "guarantee": 0,
                "actual_max": 0, "theorem_satisfied": False, "statement": "",
                "errors": errors}
    n = len(sequence)
    if n > 30:
        errors.append("the sequence must hold at most 30 numbers.")
        return {"n": n, "increase": [], "decrease": [], "guarantee": 0,
                "actual_max": 0, "theorem_satisfied": False, "statement": "",
                "errors": errors}

    inc_vals = _longest_nondecreasing(list(sequence))
    dec_vals = _longest_nonincreasing(list(sequence))

    def _indices(values, prefer_forward=True):
        """Match the values back to positions, first unused match each time."""
        used = [False] * n
        out = []
        for v in values:
            for i, item in enumerate(sequence):
                if not used[i] and item == v:
                    used[i] = True
                    out.append(i)
                    break
        return out

    inc_idx = _indices(inc_vals)
    dec_idx = _indices(dec_vals)

    guarantee = math.ceil(math.sqrt(n))
    actual_max = max(len(inc_vals), len(dec_vals))

    return {
        "n":               n,
        "increase":        inc_idx,
        "decrease":        dec_idx,
        "increase_values": inc_vals,
        "decrease_values": dec_vals,
        "guarantee":       guarantee,
        "actual_max":      actual_max,
        "theorem_satisfied": actual_max >= guarantee,
        "statement": (
            f"With {n} numbers there is always a monotone run of at least "
            f"⌈√{n}⌉ = {guarantee}: more than k² numbers force a run longer than k."
        ),
        "errors": [],
    }
