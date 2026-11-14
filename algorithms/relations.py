"""
relations.py — Relations built from the campus data.

A relation is a set of ordered pairs (a, b) taken from a base set.  Two
relations are produced here:

  * "can be connected to" — from the candidate connections, a symmetric
    relation that is neither reflexive nor transitive on the default campus.
  * "has at least as much demand as" — a comparison of daily demand, which
    orders the buildings from the largest demand to the smallest.

Every result is computed from the caller's data.  No Streamlit imports.
"""

from __future__ import annotations

import pandas as pd

from algorithms.validation import (
    COL_NAME,
    COL_DEMAND,
    canonicalize_edge,
)


def demand_values(df: pd.DataFrame) -> dict:
    """Return {building name: daily demand} for every row of *df*."""
    if df is None or df.empty:
        return {}
    return {
        str(row[COL_NAME]): float(row[COL_DEMAND])
        for _, row in df.iterrows()
    }


def domain_of(df: pd.DataFrame) -> list:
    """Return the sorted list of building names in *df*."""
    if df is None or df.empty:
        return []
    return sorted(str(n) for n in df[COL_NAME].tolist())


# ---------------------------------------------------------------------------
# 1. "can be connected to"
# ---------------------------------------------------------------------------

def connect_relation(edges, domain) -> list:
    """
    Return the "can be connected to" relation on *domain*.

    A candidate connection is undirected, so the relation contains both
    ``(a, b)`` and ``(b, a)`` for every pair whose two ends are buildings in
    *domain*.  A building is never paired with itself.

    Returns
    -------
    list[tuple[str, str]]  — sorted, duplicate-free.
    """
    dom = {str(d) for d in (domain or [])}
    pairs = set()
    for raw in edges or []:
        u, v = raw[0], raw[1]
        cu, cv = canonicalize_edge(u, v)
        if cu in dom and cv in dom and cu != cv:
            pairs.add((cu, cv))
            pairs.add((cv, cu))
    return sorted(pairs)


def relation_matrix(relation, domain) -> dict:
    """
    Return the grid form of *relation* on *domain*.

    Returns
    -------
    dict with keys:
        "labels" : list[str]  — the domain in order (rows and columns)
        "grid"   : list[list[int]]  — 1 when (row, column) is in the relation
    """
    labels = sorted({str(d) for d in (domain or [])})
    index = {name: i for i, name in enumerate(labels)}
    n = len(labels)
    grid = [[0] * n for _ in range(n)]
    for a, b in relation or []:
        a, b = str(a), str(b)
        if a in index and b in index:
            grid[index[a]][index[b]] = 1
    return {"labels": labels, "grid": grid}


# ---------------------------------------------------------------------------
# 2. "has at least as much demand as"
# ---------------------------------------------------------------------------

def demand_relation(df: pd.DataFrame, subset=None) -> list:
    """
    Return the "has at least as much demand as" relation.

    ``(a, b)`` is in the relation exactly when demand(a) >= demand(b).

    Parameters
    ----------
    df     : buildings table.
    subset : optional collection of names; defaults to every building.

    Returns
    -------
    list[tuple[str, str]]  — sorted.
    """
    values = demand_values(df)
    names = sorted({str(n) for n in (subset if subset is not None else values)})
    pairs = [
        (a, b)
        for a in names
        for b in names
        if a in values and b in values and values[a] >= values[b]
    ]
    return sorted(pairs)


def ranking(df: pd.DataFrame, subset=None) -> list:
    """
    Order *subset* by daily demand, largest first.

    Buildings with equal demand are listed alphabetically, so the order is
    always the same for the same data.
    """
    values = demand_values(df)
    names = sorted({str(n) for n in (subset if subset is not None else values)})
    return sorted(names, key=lambda n: (-values.get(n, 0.0), n))


def rank_map(df: pd.DataFrame, subset=None) -> dict:
    """Map each building to its 1-based position in :func:`ranking`."""
    return {name: i + 1 for i, name in enumerate(ranking(df, subset))}


def ties(df: pd.DataFrame, subset=None) -> list:
    """Return groups of buildings that share the same demand (each sorted)."""
    values = demand_values(df)
    names = sorted({str(n) for n in (subset if subset is not None else values)})
    buckets: dict = {}
    for name in names:
        if name in values:
            buckets.setdefault(values[name], []).append(name)
    return [sorted(group) for _v, group in sorted(buckets.items()) if len(group) > 1]


def demand_order_summary(df: pd.DataFrame, subset=None) -> dict:
    """
    Summarise the demand comparison on *subset*.

    Returns
    -------
    dict with keys:
        "order"       : list[str]        — largest demand first
        "ranks"       : dict[str, int]   — 1-based position per building
        "pairs"       : list[tuple]      — the relation itself
        "ties"        : list[list[str]]  — buildings sharing a demand value
        "total_order" : bool             — True when no two demands are equal
    """
    groups = ties(df, subset)
    return {
        "order":       ranking(df, subset),
        "ranks":       rank_map(df, subset),
        "pairs":       demand_relation(df, subset),
        "ties":        groups,
        "total_order": not groups,
    }
