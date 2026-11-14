"""
analysis.py — Pure analysis helpers for Sustainable Solar Energy Allocation.

Keeps only the functions used by the remaining pages:
  * truth_table        — 8-row membership table for (A, B, C)
  * threshold_sweep    — vary one threshold, record set sizes
  * de_morgan_checks   — verify De Morgan's laws live on data
  * inclusion_exclusion_check — verify the 3-set inclusion-exclusion identity

No Streamlit imports, and none of the excluded analysis methods are referenced.
"""

from __future__ import annotations

import pandas as pd

from algorithms.validation import (
    COL_NAME,
    COL_DEMAND,
    COL_AREA,
    COL_SOLAR,
)
from algorithms.set_theory import build_sets, eligible_set

# Keys of a threshold dict, in the order the sweep list uses them.
THRESHOLD_KEYS = ("min_demand", "min_area", "min_solar")

_SWEEP_COLUMNS  = ["value", "|A|", "|B|", "|C|", "|E|"]
_TRUTH_COLUMNS  = ["In A", "In B", "In C", "Eligible", "Count", "Buildings"]

# (T, T, T) first — the eligible combination — then the remaining seven.
_TRUTH_ORDER = [
    (True,  True,  True),
    (True,  True,  False),
    (True,  False, True),
    (False, True,  True),
    (True,  False, False),
    (False, True,  False),
    (False, False, True),
    (False, False, False),
]


# ===========================================================================
# 1. Threshold sweep
# ===========================================================================

def threshold_sweep(df, thresholds, which, values) -> pd.DataFrame:
    """
    Sweep ONE threshold while the other two stay fixed.

    Parameters
    ----------
    df         : buildings DataFrame.
    thresholds : current threshold dict.
    which      : "min_demand" | "min_area" | "min_solar".
    values     : iterable of threshold values to evaluate.

    Returns
    -------
    DataFrame with columns ``value, |A|, |B|, |C|, |E|``.

    Raises
    ------
    ValueError — if *which* is not one of the three threshold keys.
    """
    if which not in THRESHOLD_KEYS:
        raise ValueError(
            f"Unknown threshold '{which}'. Expected one of {THRESHOLD_KEYS}."
        )

    base = dict(thresholds or {})
    rows = []
    for value in values:
        probe      = dict(base)
        probe[which] = float(value)
        sets = build_sets(df, probe)
        rows.append({
            "value": float(value),
            "|A|":   len(sets["A"]),
            "|B|":   len(sets["B"]),
            "|C|":   len(sets["C"]),
            "|E|":   len(eligible_set(sets["A"], sets["B"], sets["C"])),
        })
    return pd.DataFrame(rows, columns=_SWEEP_COLUMNS)


# ===========================================================================
# 2. Truth table
# ===========================================================================

def truth_table(df, thresholds) -> pd.DataFrame:
    """
    The eight membership combinations of (in A, in B, in C).

    Returns
    -------
    DataFrame with columns ``In A, In B, In C, Eligible, Count, Buildings``.
    """
    sets = build_sets(df, thresholds)
    U, A, B, C = sets["U"], sets["A"], sets["B"], sets["C"]

    rows = []
    for in_a, in_b, in_c in _TRUTH_ORDER:
        members = {
            name for name in U
            if (name in A) == in_a
            and (name in B) == in_b
            and (name in C) == in_c
        }
        rows.append({
            "In A":     bool(in_a),
            "In B":     bool(in_b),
            "In C":     bool(in_c),
            "Eligible": bool(in_a and in_b and in_c),
            "Count":    len(members),
            "Buildings": sorted(members),
        })
    return pd.DataFrame(rows, columns=_TRUTH_COLUMNS)


# ===========================================================================
# 3. De Morgan checks
# ===========================================================================

def de_morgan_checks(A, B, C, U) -> list:
    """
    Verify the two De Morgan laws for A and B against the universal set *U*.

    Returns
    -------
    list of two dicts, each with keys ``name``, ``lhs``, ``rhs`` and ``holds``.
    """
    comp = lambda S: set(U) - set(S)          # noqa: E731
    a, b = set(A), set(B)

    cases = [
        ("(A ∪ B)′ = A′ ∩ B′", comp(a | b), comp(a) & comp(b)),
        ("(A ∩ B)′ = A′ ∪ B′", comp(a & b), comp(a) | comp(b)),
    ]
    return [
        {"name": name, "lhs": sorted(lhs), "rhs": sorted(rhs),
         "holds": lhs == rhs}
        for name, lhs, rhs in cases
    ]


# ===========================================================================
# 4. Inclusion–exclusion check
# ===========================================================================

def inclusion_exclusion_check(A, B, C) -> dict:
    """
    Verify the three-set inclusion–exclusion identity.

        |A ∪ B ∪ C| = |A| + |B| + |C| − |A ∩ B| − |A ∩ C| − |B ∩ C| + |A ∩ B ∩ C|

    Returns
    -------
    dict with keys ``lhs``, ``rhs`` (both ints), ``holds`` (bool) and
    ``terms`` — a list of ``(label, value)`` pairs.
    """
    a, b, c = set(A), set(B), set(C)
    lhs   = len(a | b | c)
    terms = [
        ("|A|",          len(a)),
        ("|B|",          len(b)),
        ("|C|",          len(c)),
        ("−|A ∩ B|",    -len(a & b)),
        ("−|A ∩ C|",    -len(a & c)),
        ("−|B ∩ C|",    -len(b & c)),
        ("+|A ∩ B ∩ C|", len(a & b & c)),
    ]
    rhs = sum(value for _label, value in terms)
    return {"lhs": lhs, "rhs": rhs, "holds": lhs == rhs, "terms": terms}
