"""
counting.py — Combinatorics: permutations, combinations, Pascal's triangle,
              balls-and-bins, and campus-building selection counts.

All results use Python's arbitrary-precision integers — no floating-point
approximations. Inputs are validated; n, k ≤ 30 for exact display.

No Streamlit imports. No eval().
"""

from __future__ import annotations
import math
import itertools
from fractions import Fraction


# ===========================================================================
# 1. Core combinatorial functions
# ===========================================================================

def factorial(n: int) -> int:
    """Return n! for non-negative integer n."""
    if not isinstance(n, int) or n < 0:
        raise ValueError(f"factorial requires a non-negative integer, got {n!r}.")
    return math.factorial(n)


def permutations(n: int, k: int) -> dict:
    """
    P(n, k) = n! / (n-k)! — ordered selections of k from n without repetition.

    Parameters
    ----------
    n, k : integers; 0 ≤ k ≤ n ≤ 30.

    Returns
    -------
    dict with 'value' (int), 'formula' (str), 'errors' (list[str]).
    """
    errors = _validate_nk(n, k, max_n=30, allow_k_gt_n=False)
    if errors:
        return {"value": 0, "formula": "", "errors": errors}
    val = math.factorial(n) // math.factorial(n - k)
    formula = f"P({n},{k}) = {n}! / ({n}-{k})! = {math.factorial(n)} / {math.factorial(n-k)} = {val}"
    return {"value": val, "formula": formula, "errors": []}


def combinations(n: int, k: int) -> dict:
    """
    C(n, k) = n! / (k! (n-k)!) — unordered selections of k from n without repetition.

    Parameters
    ----------
    n, k : integers; 0 ≤ k ≤ n ≤ 30.
    """
    errors = _validate_nk(n, k, max_n=30, allow_k_gt_n=False)
    if errors:
        return {"value": 0, "formula": "", "errors": errors}
    val = math.comb(n, k)
    formula = (f"C({n},{k}) = {n}! / ({k}! × {n-k}!) "
               f"= {math.factorial(n)} / ({math.factorial(k)} × {math.factorial(n-k)}) = {val}")
    return {"value": val, "formula": formula, "errors": []}


def permutations_with_repetition(n: int, k: int) -> dict:
    """
    n^k — ordered selections of k from n WITH repetition allowed.
    """
    errors = _validate_nk(n, k, max_n=30, allow_k_gt_n=True)
    if errors:
        return {"value": 0, "formula": "", "errors": errors}
    val = n ** k
    formula = f"Ordered selections with repetition = {n}^{k} = {val}"
    return {"value": val, "formula": formula, "errors": []}


def combinations_with_repetition(n: int, k: int) -> dict:
    """
    C(n+k-1, k) — unordered selections of k from n WITH repetition (multisets).
    """
    errors = _validate_nk(n, k, max_n=30, allow_k_gt_n=True)
    if errors:
        return {"value": 0, "formula": "", "errors": errors}
    if n == 0 and k > 0:
        return {"value": 0, "formula": "0 types, k>0: 0 multisets", "errors": []}
    val = math.comb(n + k - 1, k)
    formula = (f"Multisets of size {k} from {n} types = "
               f"C({n}+{k}-1, {k}) = C({n+k-1},{k}) = {val}")
    return {"value": val, "formula": formula, "errors": []}


def stars_and_bars(n: int, k: int) -> dict:
    """
    Number of ways to distribute *n* identical items into *k* distinct bins
    (bins may be empty): C(n+k-1, k-1).
    """
    errors = []
    if not isinstance(n, int) or n < 0:
        errors.append(f"n must be a non-negative integer (got {n!r}).")
    if not isinstance(k, int) or k < 1:
        errors.append(f"k must be a positive integer (got {k!r}).")
    if n > 30 or k > 30:
        errors.append("n and k must each be ≤ 30.")
    if errors:
        return {"value": 0, "formula": "", "errors": errors}
    val = math.comb(n + k - 1, k - 1)
    formula = (f"C({n}+{k}-1, {k}-1) = C({n+k-1},{k-1}) = {val} "
               f"ways to put {n} identical items in {k} distinct bins")
    return {"value": val, "formula": formula, "errors": []}


# ===========================================================================
# 2. Pascal's triangle
# ===========================================================================

def pascal_triangle(rows: int) -> dict:
    """
    Compute Pascal's triangle up to row *rows* (0-indexed, so row 0 is [1]).

    Parameters
    ----------
    rows : int in [1, 16]  (rows=16 gives rows 0..15, i.e., 16 rows)

    Returns
    -------
    dict with:
        'triangle'       : list of lists of ints
        'identity_checks': dict of checked identities
        'errors'         : list[str]
    """
    if not isinstance(rows, int) or rows < 1 or rows > 16:
        return {
            "triangle": [], "identity_checks": {},
            "errors": ["rows must be an integer between 1 and 16."],
        }

    tri: list[list[int]] = []
    for n in range(rows):
        row = [math.comb(n, k) for k in range(n + 1)]
        tri.append(row)

    # Identity checks (verified algebraically)
    checks: dict = {}

    # Symmetry: C(n,k) = C(n,n-k)
    sym_ok = all(
        tri[n][k] == tri[n][n - k]
        for n in range(rows) for k in range(n + 1)
    )
    checks["symmetry"] = {
        "statement": "C(n,k) = C(n,n-k)",
        "holds": sym_ok,
    }

    # Pascal's rule: C(n,k) = C(n-1,k-1) + C(n-1,k)
    pascal_ok = all(
        tri[n][k] == tri[n - 1][k - 1] + tri[n - 1][k]
        for n in range(1, rows) for k in range(1, n)
    )
    checks["pascal_rule"] = {
        "statement": "C(n,k) = C(n-1,k-1) + C(n-1,k)",
        "holds": pascal_ok,
    }

    # Row sum = 2^n
    rowsum_ok = all(sum(tri[n]) == 2 ** n for n in range(rows))
    checks["row_sum"] = {
        "statement": "Σ C(n,k) = 2^n",
        "holds": rowsum_ok,
    }

    return {"triangle": tri, "identity_checks": checks, "errors": []}


# ===========================================================================
# 3. Campus building selection (live from eligible count)
# ===========================================================================

def campus_selections(eligible_count: int, k: int) -> dict:
    """
    Compute selection counts for choosing k buildings from *eligible_count*
    eligible campus buildings.

    Returns
    -------
    dict with:
        'n'             : int   — number of eligible buildings
        'k'             : int   — selection size
        'unordered'     : int   — C(n,k)
        'ordered'       : int   — P(n,k)
        'enumeration'   : list[tuple] | None  — actual tuples if n ≤ 8 and k ≤ 4
        'errors'        : list[str]
    """
    errors: list[str] = []
    n = eligible_count
    if not isinstance(n, int) or n < 0:
        errors.append(f"eligible_count must be a non-negative integer, got {n!r}.")
    if not isinstance(k, int) or k < 0:
        errors.append(f"k must be a non-negative integer, got {k!r}.")
    if not errors and k > n:
        errors.append(f"k ({k}) cannot exceed the number of eligible buildings ({n}).")
    if errors:
        return {
            "n": n, "k": k, "unordered": 0, "ordered": 0,
            "enumeration": None, "errors": errors,
        }

    unordered = math.comb(n, k)
    ordered   = math.factorial(n) // math.factorial(n - k)

    # Enumerate actual selections when small enough
    enumeration = None
    labels = [f"B{i+1}" for i in range(n)]
    if n <= 8 and k <= 4:
        enumeration = list(itertools.combinations(labels, k))

    return {
        "n":           n,
        "k":           k,
        "unordered":   unordered,
        "ordered":     ordered,
        "enumeration": enumeration,
        "errors":      [],
    }


# ===========================================================================
# 4. Verify by itertools enumeration (cross-check)
# ===========================================================================

def verify_by_enumeration(n: int, k: int) -> dict:
    """
    For small n, k (≤ 10), enumerate actual combinations/permutations with
    itertools and verify the formula values.

    Returns
    -------
    dict with 'comb_formula', 'comb_enum', 'perm_formula', 'perm_enum',
              'comb_match', 'perm_match', 'errors'.
    """
    errors: list[str] = []
    if not isinstance(n, int) or not isinstance(k, int):
        errors.append("n and k must be integers.")
    elif k < 0 or n < 0:
        errors.append("n and k must be non-negative.")
    elif k > n:
        errors.append(f"k ({k}) cannot exceed n ({n}).")
    elif n > 10:
        errors.append("n must be ≤ 10 for enumeration verification.")
    if errors:
        return {
            "comb_formula": 0, "comb_enum": 0,
            "perm_formula": 0, "perm_enum": 0,
            "comb_match": False, "perm_match": False,
            "errors": errors,
        }

    elements = list(range(1, n + 1))
    comb_enum = sum(1 for _ in itertools.combinations(elements, k))
    perm_enum = sum(1 for _ in itertools.permutations(elements, k))
    comb_formula = math.comb(n, k)
    perm_formula = math.factorial(n) // math.factorial(n - k)

    return {
        "comb_formula": comb_formula,
        "comb_enum":    comb_enum,
        "perm_formula": perm_formula,
        "perm_enum":    perm_enum,
        "comb_match":   comb_formula == comb_enum,
        "perm_match":   perm_formula == perm_enum,
        "errors":       [],
    }


# ===========================================================================
# 5. Multinomial arrangements of indistinguishable objects
# ===========================================================================

def multinomial(counts) -> dict:
    """
    Number of distinct arrangements of a multiset:
        (k1 + k2 + ... + kt)! / (k1! k2! ... kt!)

    This is the count of distinct sequences built from ``counts[i]``
    indistinguishable objects of type *i*.

    Parameters
    ----------
    counts : sequence of non-negative integers, total ≤ 30.

    Returns
    -------
    dict with 'value', 'total', 'numerator', 'denominator', 'formula', 'errors'.
    """
    errors: list[str] = []
    if not isinstance(counts, (list, tuple)) or not counts:
        errors.append("counts must be a non-empty list of non-negative integers.")
        return {"value": 0, "total": 0, "numerator": 0, "denominator": 0,
                "formula": "", "errors": errors}

    values: list[int] = []
    for c in counts:
        if not isinstance(c, int) or isinstance(c, bool) or c < 0:
            errors.append(f"every count must be a non-negative integer (got {c!r}).")
        else:
            values.append(c)
    if errors:
        return {"value": 0, "total": 0, "numerator": 0, "denominator": 0,
                "formula": "", "errors": errors}

    total = sum(values)
    if total > 30:
        errors.append("the counts must add up to ≤ 30.")
        return {"value": 0, "total": total, "numerator": 0, "denominator": 0,
                "formula": "", "errors": errors}

    numerator = math.factorial(total)
    denominator = 1
    for c in values:
        denominator *= math.factorial(c)
    val = numerator // denominator
    parts = " × ".join(f"{c}!" for c in values)
    formula = (f"{total}! / ({parts}) = {numerator} / {denominator} = {val}")
    return {
        "value": val,
        "total": total,
        "numerator": numerator,
        "denominator": denominator,
        "formula": formula,
        "errors": [],
    }


# ===========================================================================
# 6. Listing selections — every combination / permutation, with labels
# ===========================================================================

LIST_LIMIT = 2000


def list_selections(n: int, k: int, ordered: bool = False, labels=None) -> dict:
    """
    Enumerate every way to pick *k* items from *n*.

    Parameters
    ----------
    n, k    : integers, 0 ≤ k ≤ n ≤ 12 (a full listing of 12! orders would be
              far too large, so the returned list is capped at :data:`LIST_LIMIT`
              entries and 'truncated' is set when the cap bites).
    ordered : False → combinations (order does not matter);
              True  → permutations (order matters).
    labels  : optional list of *n* names used in place of the indices.

    Returns
    -------
    dict with 'n', 'k', 'ordered', 'count', 'items' (list of tuples),
    'truncated', 'errors'.
    """
    errors = _validate_nk(n, k, max_n=12, allow_k_gt_n=False)
    if errors:
        return {"n": n, "k": k, "ordered": bool(ordered), "count": 0,
                "items": [], "truncated": False, "errors": errors}

    names = list(labels) if labels is not None else list(range(n))
    if len(names) < n:
        return {"n": n, "k": k, "ordered": bool(ordered), "count": 0,
                "items": [], "truncated": False,
                "errors": [f"labels must supply at least {n} names."]}

    maker = itertools.permutations if ordered else itertools.combinations
    total = (math.factorial(n) // math.factorial(n - k)) if ordered else math.comb(n, k)

    items: list = []
    truncated = False
    for index, combo in enumerate(maker(names[:n], k)):
        if index >= LIST_LIMIT:
            truncated = True
            break
        items.append(tuple(combo))

    return {
        "n": n,
        "k": k,
        "ordered": bool(ordered),
        "count": total,
        "items": items,
        "truncated": truncated,
        "errors": [],
    }


# ===========================================================================
# 7. Stars and bars — every distribution of identical items into bins
# ===========================================================================

def stars_and_bars_distributions(m: int, n: int, min_each: int = 0,
                                 labels=None) -> dict:
    """
    List every way to put *m* identical items into *n* distinct bins, where
    each bin receives at least *min_each* items (0 lets a bin be empty).

    The number of distributions is C(m - min_each·n + n - 1, n - 1).

    Parameters
    ----------
    m, n     : integers; m ≤ 15 and n ≤ 6 so the whole list stays small.
    min_each : 0 or a positive integer.
    labels   : optional bin names.

    Returns
    -------
    dict with 'm', 'n', 'min_each', 'distributions', 'count', 'expected',
    'truncated', 'errors'.
    """
    errors: list[str] = []
    if not isinstance(m, int) or isinstance(m, bool) or m < 0:
        errors.append(f"m must be a non-negative integer (got {m!r}).")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        errors.append(f"n must be a positive integer (got {n!r}).")
    if not isinstance(min_each, int) or isinstance(min_each, bool) or min_each < 0:
        errors.append(f"min_each must be a non-negative integer (got {min_each!r}).")
    if errors:
        return {"m": m, "n": n, "min_each": min_each, "distributions": [],
                "count": 0, "expected": 0, "truncated": False, "errors": errors}

    if m > 15 or n > 6:
        return {"m": m, "n": n, "min_each": min_each, "distributions": [],
                "count": 0, "expected": 0, "truncated": False,
                "errors": ["m must be ≤ 15 and n ≤ 6 so every distribution can be listed."]}

    if min_each * n > m:
        return {"m": m, "n": n, "min_each": min_each, "distributions": [],
                "count": 0, "expected": 0, "truncated": False,
                "errors": [f"{m} items cannot give every one of {n} bins at least "
                           f"{min_each} item(s)."]}

    base = min_each
    remaining = m - base * n
    expected = math.comb(remaining + n - 1, n - 1)

    names = list(labels) if labels is not None else [f"bin {i + 1}" for i in range(n)]
    if len(names) < n:
        names = names + [f"bin {i + 1}" for i in range(len(names), n)]

    distributions: list = []

    def _walk(i: int, left: int, acc: list) -> None:
        if i == n - 1:
            distributions.append(tuple(acc + [left + base]))
            return
        for take in range(left + 1):
            _walk(i + 1, left - take, acc + [take + base])

    _walk(0, remaining, [])

    return {
        "m": m,
        "n": n,
        "min_each": min_each,
        "bins": names[:n],
        "distributions": distributions,
        "count": len(distributions),
        "expected": expected,
        "truncated": len(distributions) < expected,
        "errors": [],
    }


# ===========================================================================
# 8. Double counting across the campus connection list
# ===========================================================================

def double_counting(vertices, edges) -> dict:
    """
    Count the lines from buildings to connections two ways.

    Every connection has exactly two endpoints, so summing each building's
    number of connections and adding two for every connection give the same
    total.  With the default campus this is 12 either way.

    Parameters
    ----------
    vertices : iterable of building names.
    edges    : iterable of ``(u, v)`` name pairs (order does not matter).

    Returns
    -------
    dict with 'buildings', 'connections', 'lines', 'tally_buildings',
    'tally_connections', 'vertex_count', 'edge_count', 'check'.
    """
    names = [str(v) for v in (vertices or [])]
    valid = set(names)

    pairs: list = []
    for edge in (edges or []):
        try:
            u, v = str(edge[0]), str(edge[1])
        except (TypeError, IndexError, KeyError):
            continue
        if u not in valid or v not in valid or u == v:
            continue
        key = (u, v) if u < v else (v, u)
        if key not in pairs:
            pairs.append(key)
    pairs.sort()

    degree = {name: 0 for name in names}
    for a, b in pairs:
        degree[a] += 1
        degree[b] += 1

    lines = []
    for a, b in pairs:
        label = f"{a}–{b}"
        lines.append({"building": a, "connection": label})
        lines.append({"building": b, "connection": label})

    tally_buildings = sum(degree.values())
    tally_connections = 2 * len(pairs)

    return {
        "buildings": [{"key": name, "degree": degree[name]} for name in names],
        "connections": [{"key": f"{a}–{b}", "endpoints": 2} for a, b in pairs],
        "lines": lines,
        "tally_buildings": tally_buildings,
        "tally_connections": tally_connections,
        "vertex_count": len(names),
        "edge_count": len(pairs),
        "check": tally_buildings == tally_connections,
    }


# ===========================================================================
# Internal validation helper
# ===========================================================================

def _validate_nk(n, k, max_n: int = 30, allow_k_gt_n: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(n, int):
        errors.append(f"n must be an integer (got {n!r}).")
    if not isinstance(k, int):
        errors.append(f"k must be an integer (got {k!r}).")
    if errors:
        return errors
    if n < 0:
        errors.append(f"n must be ≥ 0 (got {n}).")
    if k < 0:
        errors.append(f"k must be ≥ 0 (got {k}).")
    if n > max_n:
        errors.append(f"n must be ≤ {max_n} (got {n}).")
    if k > max_n:
        errors.append(f"k must be ≤ {max_n} (got {k}).")
    if not allow_k_gt_n and not errors and k > n:
        errors.append(f"k ({k}) cannot exceed n ({n}) for this formula.")
    return errors
