"""
functions.py — Functions defined on the campus buildings.

Three functions are described, each as a domain, a codomain and a list of
arrows (one per domain element):

  * ``demand``   : every building -> its daily demand
  * ``eligible`` : every building -> 1 when it meets all three criteria, else 0
  * ``rank``     : each eligible building -> its 1..|E| position by demand

The analysis (one-to-one, onto, bijective and the reason) reuses the shared
routine in :mod:`algorithms.logic`, so nothing is duplicated.

No Streamlit imports.
"""

from __future__ import annotations

import pandas as pd

from algorithms.validation import COL_NAME, COL_DEMAND
from algorithms.set_theory import build_sets, eligible_set
from algorithms.relations import ranking
from algorithms.logic import function_properties


def _analyse(domain, codomain, arrows) -> dict:
    """
    Run the shared function analyser and add the unmatched codomain values.

    ``arrows`` is a list of ``(domain element, image)`` pairs.
    """
    result = function_properties(
        [[str(a), str(b)] for a, b in arrows],
        [str(d) for d in domain],
        [str(c) for c in codomain],
    )
    images = {str(b) for _a, b in arrows}
    result["missing"] = [str(c) for c in codomain if str(c) not in images]
    return result


def demand_function(df: pd.DataFrame) -> dict:
    """
    The daily-demand function: building -> demand in kWh/day.

    The codomain is the list of demand values the campus actually reports, so
    the function is onto by construction; it is one-to-one only when no two
    buildings share a demand value.
    """
    if df is None or df.empty:
        return {
            "name": "demand", "domain": [], "codomain": [], "arrows": [],
            "valid": True, "injective": True, "surjective": True,
            "bijective": True, "missing": [], "details": "",
        }

    names = sorted(str(n) for n in df[COL_NAME].tolist())
    values = {
        str(row[COL_NAME]): float(row[COL_DEMAND])
        for _, row in df.iterrows()
    }
    codomain = sorted({values[n] for n in names})
    arrows = [(n, values[n]) for n in names]
    info = _analyse(names, codomain, arrows)
    info["name"] = "demand"
    info["arrows"] = [[n, values[n]] for n in names]
    info["domain"] = names
    info["codomain"] = codomain
    return info


def eligible_function(df: pd.DataFrame, thresholds: dict) -> dict:
    """
    The eligibility function: building -> 1 when eligible, 0 otherwise.

    The codomain is ``{0, 1}``.
    """
    sets = build_sets(df, thresholds)
    U = sorted(sets["U"])
    if not U:
        return {
            "name": "eligible", "domain": [], "codomain": ["0", "1"],
            "arrows": [], "valid": True, "injective": True,
            "surjective": True, "bijective": True, "missing": [],
            "details": "",
        }

    E = eligible_set(sets["A"], sets["B"], sets["C"])
    arrows = [(n, "1" if n in E else "0") for n in U]
    info = _analyse(U, ["0", "1"], arrows)
    info["name"] = "eligible"
    info["domain"] = U
    info["codomain"] = ["0", "1"]
    info["arrows"] = [[n, ("1" if n in E else "0")] for n in U]
    return info


def rank_function(df: pd.DataFrame, thresholds: dict) -> dict:
    """
    The rank function: eligible building -> its position 1..|E| by demand.

    The codomain is ``{1, 2, ..., |E|}``; this map is a bijection.
    """
    sets = build_sets(df, thresholds)
    E = eligible_set(sets["A"], sets["B"], sets["C"])
    if not E:
        return {
            "name": "rank", "domain": [], "codomain": [],
            "arrows": [], "valid": True, "injective": True,
            "surjective": True, "bijective": True, "missing": [],
            "details": "",
        }

    order = ranking(df, E)                       # largest demand first
    ranks = {name: i + 1 for i, name in enumerate(order)}
    domain = sorted(E)
    codomain = list(range(1, len(E) + 1))
    arrows = [(n, ranks[n]) for n in domain]
    info = _analyse(domain, codomain, arrows)
    info["name"] = "rank"
    info["domain"] = domain
    info["codomain"] = codomain
    info["arrows"] = [[n, ranks[n]] for n in domain]
    return info


def function_overview(df: pd.DataFrame, thresholds: dict) -> dict:
    """Return all three function descriptions in one call."""
    return {
        "demand":   demand_function(df),
        "eligible": eligible_function(df, thresholds),
        "rank":     rank_function(df, thresholds),
    }
