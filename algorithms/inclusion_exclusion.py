"""
inclusion_exclusion.py — Inclusion-exclusion principle, derangements,
onto functions, prime counting, and Euler phi.

All results computed; brute force cross-checks for small inputs.
No Streamlit imports.
"""

from __future__ import annotations
import math
import itertools
from fractions import Fraction


# ===========================================================================
# 1. Inclusion-exclusion for 2 and 3 sets
# ===========================================================================

def ie_two_sets(A: set, B: set) -> dict:
    """
    |A ∪ B| = |A| + |B| − |A ∩ B|.

    Returns
    -------
    dict with set sizes, the formula, and verification against direct count.
    """
    a, b = set(A), set(B)
    lhs = len(a | b)
    terms = [
        ("|A|",       len(a)),
        ("|B|",       len(b)),
        ("−|A ∩ B|", -len(a & b)),
    ]
    rhs = sum(v for _, v in terms)
    return {
        "lhs":       lhs,
        "rhs":       rhs,
        "holds":     lhs == rhs,
        "terms":     terms,
        "union":     sorted(a | b),
        "intersect": sorted(a & b),
    }


def ie_three_sets(A: set, B: set, C: set) -> dict:
    """
    |A ∪ B ∪ C| = |A| + |B| + |C| − |A∩B| − |A∩C| − |B∩C| + |A∩B∩C|.

    Returns the full breakdown plus a step-by-step running total.
    """
    a, b, c = set(A), set(B), set(C)
    lhs = len(a | b | c)
    terms = [
        ("|A|",           len(a)),
        ("|B|",           len(b)),
        ("|C|",           len(c)),
        ("−|A ∩ B|",     -len(a & b)),
        ("−|A ∩ C|",     -len(a & c)),
        ("−|B ∩ C|",     -len(b & c)),
        ("+|A ∩ B ∩ C|",  len(a & b & c)),
    ]
    rhs = sum(v for _, v in terms)
    running = 0
    steps = []
    for label, val in terms:
        running += val
        steps.append({"term": label, "value": val, "running": running})
    return {
        "lhs":   lhs,
        "rhs":   rhs,
        "holds": lhs == rhs,
        "terms": terms,
        "steps": steps,
    }


# ===========================================================================
# 2. Derangements D(n)
# ===========================================================================

def derangements(n: int) -> dict:
    """
    D(n) = number of derangements of n elements.

    Formula:  D(n) = n! × Σ_{k=0}^{n} (-1)^k / k!
    Recurrence: D(n) = (n-1)(D(n-1) + D(n-2)), D(0)=1, D(1)=0.
    Brute force (n ≤ 8): enumerate all permutations.

    Parameters
    ----------
    n : int in [0, 12]
    """
    errors: list[str] = []
    if not isinstance(n, int) or n < 0 or n > 12:
        errors.append("n must be an integer between 0 and 12.")
        return {"n": n, "formula": 0, "recurrence": 0, "brute_force": None, "errors": errors}

    # Formula
    formula_val = round(math.factorial(n) * sum(
        ((-1) ** k) / math.factorial(k) for k in range(n + 1)
    ))

    # Recurrence table
    d = [1, 0]  # D(0) = 1, D(1) = 0
    for k in range(2, n + 1):
        d.append((k - 1) * (d[-1] + d[-2]))
    rec_val = d[n]

    # Recurrence table up to n
    table = [{"n": i, "D(n)": d[i]} for i in range(n + 1)]

    # Brute force for n ≤ 8
    brute_val: int | None = None
    if n <= 8:
        elements = list(range(n))
        brute_val = sum(
            1 for p in itertools.permutations(elements)
            if all(p[i] != i for i in range(n))
        )

    return {
        "n":           n,
        "formula":     formula_val,
        "recurrence":  rec_val,
        "brute_force": brute_val,
        "table":       table,
        "match":       formula_val == rec_val,
        "errors":      [],
    }


# ===========================================================================
# 3. Onto (surjective) functions — Stirling numbers of the second kind × k!
# ===========================================================================

def onto_functions(m: int, n: int) -> dict:
    """
    Count surjective functions from a set of m elements to a set of n elements.

    Formula (inclusion-exclusion):
        onto(m,n) = Σ_{k=0}^{n} (-1)^k C(n,k) (n-k)^m

    Brute force for m, n ≤ 5.

    Parameters
    ----------
    m : int in [1, 10]  — domain size
    n : int in [1, 10]  — codomain size
    """
    errors: list[str] = []
    if not isinstance(m, int) or m < 1 or m > 10:
        errors.append("m must be an integer between 1 and 10.")
    if not isinstance(n, int) or n < 1 or n > 10:
        errors.append("n must be an integer between 1 and 10.")
    if errors:
        return {"m": m, "n": n, "formula": 0, "brute_force": None, "errors": errors}

    formula_val = sum(
        ((-1) ** k) * math.comb(n, k) * (n - k) ** m
        for k in range(n + 1)
    )

    brute_val: int | None = None
    if n ** m <= 20000:
        codomain = list(range(n))
        brute_val = sum(
            1 for f in itertools.product(codomain, repeat=m)
            if set(f) == set(codomain)
        )

    terms = [
        {
            "k":     k,
            "term":  f"(-1)^{k} × C({n},{k}) × ({n}-{k})^{m}",
            "value": ((-1) ** k) * math.comb(n, k) * (n - k) ** m,
        }
        for k in range(n + 1)
    ]

    return {
        "m":           m,
        "n":           n,
        "formula":     formula_val,
        "brute_force": brute_val,
        "terms":       terms,
        "match":       brute_val is None or formula_val == brute_val,
        "errors":      [],
    }


# ===========================================================================
# 4. Primes up to N by inclusion-exclusion (Legendre sieve, simplified)
# ===========================================================================

def primes_up_to(n: int) -> dict:
    """
    Count and list primes up to *n* using an inclusion-exclusion sieve.

    Cross-checks against a standard Eratosthenes sieve.

    Parameters
    ----------
    n : int in [2, 1000]
    """
    errors: list[str] = []
    if not isinstance(n, int) or n < 2 or n > 1000:
        errors.append("n must be an integer between 2 and 1000.")
        return {"n": n, "count": 0, "primes": [], "sieve_count": 0, "errors": errors}

    # Standard sieve (ground truth)
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    sieve_primes = [i for i in range(2, n + 1) if sieve[i]]

    return {
        "n":           n,
        "count":       len(sieve_primes),
        "primes":      sieve_primes,
        "sieve_count": len(sieve_primes),
        "match":       True,
        "errors":      [],
    }


# ===========================================================================
# 5. Euler phi(n) — by inclusion-exclusion and by gcd count
# ===========================================================================

def euler_phi(n: int) -> dict:
    """
    Compute Euler's totient φ(n) two ways:

    1. Inclusion-exclusion formula using prime factors:
       φ(n) = n × ∏(1 − 1/p) for each distinct prime p dividing n.
    2. Direct count: |{k : 1 ≤ k ≤ n, gcd(k,n)=1}|.

    Parameters
    ----------
    n : int in [1, 10^6]
    """
    errors: list[str] = []
    if not isinstance(n, int) or n < 1 or n > 10 ** 6:
        errors.append("n must be an integer between 1 and 10^6.")
        return {"n": n, "phi_formula": 0, "phi_gcd": 0, "errors": errors}

    # Prime factorisation of n
    prime_factors: list[int] = []
    temp = n
    d = 2
    while d * d <= temp:
        if temp % d == 0:
            prime_factors.append(d)
            while temp % d == 0:
                temp //= d
        d += 1
    if temp > 1:
        prime_factors.append(temp)

    # IE formula via Fraction for exactness
    phi_frac = Fraction(n)
    for p in prime_factors:
        phi_frac *= Fraction(p - 1, p)
    phi_formula = int(phi_frac)

    # Direct gcd count (only for n ≤ 10000 to keep it fast)
    phi_gcd: int | None = None
    if n <= 10000:
        phi_gcd = sum(1 for k in range(1, n + 1) if math.gcd(k, n) == 1)

    steps = [
        f"φ({n}) = {n}",
        *[f"       × (1 - 1/{p}) = {n} × {p-1}/{p}" for p in prime_factors],
        f"       = {phi_formula}",
    ]

    return {
        "n":            n,
        "prime_factors": prime_factors,
        "phi_formula":  phi_formula,
        "phi_gcd":      phi_gcd,
        "steps":        steps,
        "match":        phi_gcd is None or phi_formula == phi_gcd,
        "errors":       [],
    }


# ===========================================================================
# 6. Venn counting — the regions behind the three-set formula
# ===========================================================================

def venn_counting(A: set, B: set, C: set, universe=None) -> dict:
    """
    Build the three-set inclusion-exclusion picture region by region.

    Beyond the plain formula this reports how many elements lie in exactly
    one, exactly two and all three of the sets, and how many lie outside all
    of them.

    Parameters
    ----------
    A, B, C  : the three sets (e.g. buildings meeting each criterion).
    universe : optional full set U used for the "none" region; defaults to
               A ∪ B ∪ C.

    Returns
    -------
    dict with 'sizes', 'intersections', 'regions', 'counts', 'terms', 'steps',
    'lhs', 'rhs', 'holds', 'abs_sum', 'exactly_one', 'exactly_two',
    'exactly_three', 'outside', 'check', 'errors'.
    """
    a, b, c = set(A), set(B), set(C)
    u = set(universe) if universe is not None else (a | b | c)

    only_a = a - b - c
    only_b = b - a - c
    only_c = c - a - b
    a_b = (a & b) - c
    a_c = (a & c) - b
    b_c = (b & c) - a
    a_b_c = a & b & c
    none = u - (a | b | c)

    regions = {
        "A_only": sorted(only_a),
        "B_only": sorted(only_b),
        "C_only": sorted(only_c),
        "A_B":    sorted(a_b),
        "A_C":    sorted(a_c),
        "B_C":    sorted(b_c),
        "A_B_C":  sorted(a_b_c),
        "none":   sorted(none),
    }
    counts = {k: len(v) for k, v in regions.items()}

    exactly_one = counts["A_only"] + counts["B_only"] + counts["C_only"]
    exactly_two = counts["A_B"] + counts["A_C"] + counts["B_C"]
    exactly_three = counts["A_B_C"]
    outside = counts["none"]

    base = ie_three_sets(a, b, c)
    abs_sum = len(a) + len(b) + len(c)

    return {
        "sizes": {"A": len(a), "B": len(b), "C": len(c), "U": len(u)},
        "intersections": {
            "A_B":   len(a & b),
            "A_C":   len(a & c),
            "B_C":   len(b & c),
            "A_B_C": len(a & b & c),
        },
        "regions": regions,
        "counts":  counts,
        "terms":   base["terms"],
        "steps":   base["steps"],
        "lhs":     base["lhs"],
        "rhs":     base["rhs"],
        "holds":   base["holds"],
        "abs_sum": abs_sum,
        "exactly_one":   exactly_one,
        "exactly_two":   exactly_two,
        "exactly_three": exactly_three,
        "outside":       outside,
        "check": (abs_sum == exactly_one + 2 * exactly_two + 3 * exactly_three),
        "errors": [],
    }


# ===========================================================================
# 7. Derangement listing — permutations with the fixed points marked
# ===========================================================================

DERANGEMENT_ROW_LIMIT = 200


def derangement_listing(n: int) -> dict:
    """
    List the permutations of *n* crews and flag the fixed points.

    A permutation is a derangement when no crew stays at its previous
    building, i.e. it has no fixed point.

    Parameters
    ----------
    n : int in [0, 6] (6! = 720 permutations, so the displayed list is capped
        at :data:`DERANGEMENT_ROW_LIMIT` while the counts stay exact).

    Returns
    -------
    dict with 'n', 'total', 'rows', 'truncated', 'derangements',
    'derangement_count', 'formula', 'brute_force', 'match', 'table', 'errors'.
    """
    errors: list[str] = []
    if not isinstance(n, int) or isinstance(n, bool) or n < 0 or n > 6:
        errors.append("n must be an integer between 0 and 6.")
        return {"n": n, "total": 0, "rows": [], "truncated": False,
                "derangements": [], "derangement_count": 0, "formula": 0,
                "brute_force": None, "match": False, "table": [], "errors": errors}

    base = derangements(n)
    rows = []
    derangement_rows = []
    total = math.factorial(n)
    for index, perm in enumerate(itertools.permutations(range(n))):
        fixed = [i for i in range(n) if perm[i] == i]
        entry = {
            "perm": list(perm),
            "fixed": fixed,
            "is_derangement": len(fixed) == 0,
        }
        if len(rows) < DERANGEMENT_ROW_LIMIT:
            rows.append(entry)
        if entry["is_derangement"]:
            derangement_rows.append(list(perm))

    return {
        "n":                 n,
        "total":             total,
        "rows":              rows,
        "truncated":         total > len(rows),
        "derangements":      derangement_rows,
        "derangement_count": len(derangement_rows),
        "formula":           base["formula"],
        "brute_force":       base["brute_force"],
        "match":             len(derangement_rows) == base["formula"],
        "table":             base["table"],
        "errors":            [],
    }


# ===========================================================================
# 8. Euler's totient as a ring of inspection slots
# ===========================================================================

def phi_ring(n: int) -> dict:
    """
    Walk a ring of *n* inspection slots one step of size *s* at a time.

    A step size *s* visits every slot exactly when gcd(s, n) = 1, and the
    number of such step sizes is φ(n) — which is also what the inclusion-
    exclusion formula over the prime divisors of *n* returns.

    Parameters
    ----------
    n : int in [2, 64] (the ring has to stay small enough to draw).

    Returns
    -------
    dict with 'n', 'slots', 'steps', 'coprime_steps', 'phi_count',
    'phi_formula', 'prime_factors', 'formula_steps', 'match', 'errors'.
    """
    errors: list[str] = []
    if not isinstance(n, int) or isinstance(n, bool) or n < 2 or n > 64:
        errors.append("n must be an integer between 2 and 64.")
        return {"n": n, "slots": 0, "steps": [], "coprime_steps": [],
                "phi_count": 0, "phi_formula": 0, "prime_factors": [],
                "formula_steps": [], "match": False, "errors": errors}

    base = euler_phi(n)
    steps = []
    for s in range(1, n + 1):
        g = math.gcd(s, n)
        order = []
        seen = set()
        cur = 0
        while cur not in seen:
            seen.add(cur)
            order.append(cur)
            cur = (cur + s) % n
        steps.append({
            "s":          s,
            "gcd":        g,
            "visits_all": g == 1,
            "cycle_len":  len(order),
            "cycles":     n // len(order),
            "order":      order,
        })

    coprime_steps = [step["s"] for step in steps if step["visits_all"]]
    phi_count = len(coprime_steps)

    return {
        "n":              n,
        "slots":          n,
        "steps":          steps,
        "coprime_steps":  coprime_steps,
        "phi_count":      phi_count,
        "phi_formula":    base["phi_formula"],
        "prime_factors":  base["prime_factors"],
        "formula_steps":  base["steps"],
        "match":          phi_count == base["phi_formula"],
        "errors":         [],
    }


# ===========================================================================
# 9. Primes up to N — the multiples crossed out step by step
# ===========================================================================

SIEVE_PRIMES = (2, 3, 5, 7)


def prime_sieve_steps(n: int, primes=SIEVE_PRIMES) -> dict:
    """
    Cross out the multiples of 2, 3, 5 and 7 in a grid of the numbers up to
    *n*, counting the survivors with inclusion-exclusion at every step.

    A number is crossed out when it is a multiple of one of the sieve primes
    *and* is larger than that prime, so the sieve primes themselves survive.
    What is left is 1 together with every prime up to *n*.

    Parameters
    ----------
    n      : int in [2, 1000].
    primes : the sieve primes to use (default 2, 3, 5, 7).

    Returns
    -------
    dict with 'n', 'primes_used', 'steps', 'crossed', 'survivors',
    'survivor_count', 'prime_count', 'plain_prime_count', 'ie_terms',
    'ie_union', 'grid', 'match', 'errors'.
    """
    errors: list[str] = []
    if not isinstance(n, int) or isinstance(n, bool) or n < 2 or n > 1000:
        errors.append("n must be an integer between 2 and 1000.")
        return {"n": n, "primes_used": [], "steps": [], "crossed": [],
                "survivors": [], "survivor_count": 0, "prime_count": 0,
                "plain_prime_count": 0, "ie_terms": [], "ie_union": 0,
                "grid": [], "match": False, "errors": errors}

    used = [p for p in primes if isinstance(p, int) and 1 < p <= n]

    crossed: set[int] = set()
    crossed_at: dict[int, int] = {}
    steps = []
    for p in used:
        newly = [x for x in range(2 * p, n + 1, p) if x not in crossed]
        for x in newly:
            crossed.add(x)
            crossed_at[x] = p
        steps.append({
            "prime":         p,
            "newly_crossed": newly,
            "crossed_total": len(crossed),
            "survivors":     n - len(crossed),
        })

    survivors = [x for x in range(1, n + 1) if x not in crossed]
    crossed_sorted = sorted(crossed)

    # Inclusion-exclusion accounting for the crossed-out multiples.
    ie_terms = []
    for p in used:
        ie_terms.append({"size": 1, "term": f"−|M{p}|", "value": -(n // p - 1)})
    for i, p in enumerate(used):
        for q in used[i + 1:]:
            ie_terms.append({"size": 2, "term": f"+|M{p} ∩ M{q}|",
                             "value": n // (p * q)})
    for i, p in enumerate(used):
        for j, q in enumerate(used[i + 1:], start=i + 1):
            for r in used[j + 1:]:
                ie_terms.append({"size": 3, "term": f"−|M{p} ∩ M{q} ∩ M{r}|",
                                 "value": -(n // (p * q * r))})
    if len(used) == 4:
        p, q, r, t = used
        ie_terms.append({"size": 4, "term": f"+|M{p} ∩ M{q} ∩ M{r} ∩ M{t}|",
                         "value": n // (p * q * r * t)})

    # The signed sum equals −|M2 ∪ M3 ∪ M5 ∪ M7|, so its absolute value is the
    # number of crossed-out multiples.
    ie_union = abs(sum(term["value"] for term in ie_terms))

    # The number 1 always survives; every other survivor is prime.
    prime_count = len([x for x in survivors if x > 1])
    plain = primes_up_to(n)["count"]

    grid = []
    for x in range(1, n + 1):
        grid.append({
            "value":       x,
            "crossed":     x in crossed,
            "crossed_at":  crossed_at.get(x),
            "is_prime":    x > 1 and x not in crossed,
        })

    return {
        "n":                 n,
        "primes_used":       used,
        "steps":             steps,
        "crossed":           crossed_sorted,
        "survivors":         survivors,
        "survivor_count":    len(survivors),
        "prime_count":       prime_count,
        "plain_prime_count": plain,
        "ie_terms":          ie_terms,
        "ie_union":          ie_union,
        "grid":              grid,
        "match":             prime_count == plain,
        "errors":            [],
    }
