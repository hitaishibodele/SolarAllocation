"""
set_theory.py — Set computations for the campus buildings.

Implements the universal set, the predicate-defined subsets A/B/C, the
eligible set E, and the standard set operations (union, intersection,
difference, complement). Also provides a per-building explanation, a
classification table, a Venn region decomposition, the power set and the
filter funnel used by the visuals.

No Streamlit imports allowed in this module.
"""

import pandas as pd

from algorithms.validation import (
    COL_NAME,
    COL_DEMAND,
    COL_AREA,
    COL_SOLAR,
    DEFAULT_THRESHOLDS,
)

# ---------------------------------------------------------------------------
# 1. Universal set
# ---------------------------------------------------------------------------

def universal_set(df: pd.DataFrame) -> set:
    """
    Return the set of all building names in *df*.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain a 'name' column.  Empty DataFrame → empty set.

    Returns
    -------
    set[str]
    """
    if df is None or df.empty:
        return set()
    return set(df[COL_NAME].astype(str).tolist())


# ---------------------------------------------------------------------------
# 2. Predicate-defined subsets A, B, C
# ---------------------------------------------------------------------------

def build_sets(df: pd.DataFrame, thresholds: dict) -> dict:
    """
    Build the three predicate-defined subsets using inclusive (>=) comparisons.

        A = {b : energy_demand_kwh_day  >= min_demand}
        B = {b : rooftop_area_m2        >= min_area}
        C = {b : solar_potential_pct    >= min_solar}

    Parameters
    ----------
    df         : pd.DataFrame with canonical columns.
    thresholds : dict with keys 'min_demand', 'min_area', 'min_solar'.
                 Missing keys fall back to DEFAULT_THRESHOLDS.

    Returns
    -------
    dict with keys "U", "A", "B", "C" — all values are set[str].
    """
    min_demand = float(thresholds.get("min_demand", DEFAULT_THRESHOLDS["min_demand"]))
    min_area   = float(thresholds.get("min_area",   DEFAULT_THRESHOLDS["min_area"]))
    min_solar  = float(thresholds.get("min_solar",  DEFAULT_THRESHOLDS["min_solar"]))

    if df is None or df.empty:
        return {"U": set(), "A": set(), "B": set(), "C": set()}

    U: set = {str(row[COL_NAME]) for _, row in df.iterrows()}

    A: set = {
        str(row[COL_NAME])
        for _, row in df.iterrows()
        if float(row[COL_DEMAND]) >= min_demand
    }
    B: set = {
        str(row[COL_NAME])
        for _, row in df.iterrows()
        if float(row[COL_AREA]) >= min_area
    }
    C: set = {
        str(row[COL_NAME])
        for _, row in df.iterrows()
        if float(row[COL_SOLAR]) >= min_solar
    }

    return {"U": U, "A": A, "B": B, "C": C}


# ---------------------------------------------------------------------------
# 3-6. Core set operations
# ---------------------------------------------------------------------------

def eligible_set(A: set, B: set, C: set) -> set:
    """Return E = A ∩ B ∩ C."""
    return A & B & C


def ineligible_set(U: set, E: set) -> set:
    """Return U − E (buildings that are NOT eligible)."""
    return U - E


def union_all(A: set, B: set, C: set) -> set:
    """Return A ∪ B ∪ C."""
    return A | B | C


def complement(S: set, U: set) -> set:
    """Return U − S (complement of S with respect to universal set U)."""
    return U - S


# ---------------------------------------------------------------------------
# 7. Pairwise set differences
# ---------------------------------------------------------------------------

def set_differences(A: set, B: set, C: set) -> dict:
    """
    Return a dict of all six ordered pairwise differences:
        "A-B", "A-C", "B-A", "B-C", "C-A", "C-B"
    Each value is a set[str].
    """
    return {
        "A-B": A - B,
        "A-C": A - C,
        "B-A": B - A,
        "B-C": B - C,
        "C-A": C - A,
        "C-B": C - B,
    }


# ---------------------------------------------------------------------------
# 8. Full summary
# ---------------------------------------------------------------------------

def set_operations_summary(df: pd.DataFrame, thresholds: dict) -> dict:
    """
    Compute and return every set-theory result in one call.

    Returns
    -------
    dict with keys:
        "U"            : set[str]  — universal set
        "A"            : set[str]  — high-demand buildings
        "B"            : set[str]  — sufficient-area buildings
        "C"            : set[str]  — good-solar buildings
        "E"            : set[str]  — eligible = A ∩ B ∩ C
        "ineligible"   : set[str]  — U − E
        "union"        : set[str]  — A ∪ B ∪ C
        "A'"           : set[str]  — complement of A w.r.t. U
        "B'"           : set[str]  — complement of B w.r.t. U
        "C'"           : set[str]  — complement of C w.r.t. U
        "differences"  : dict      — output of set_differences(A, B, C)
        "count_U"      : int
        "count_A"      : int
        "count_B"      : int
        "count_C"      : int
        "count_E"      : int
    """
    sets = build_sets(df, thresholds)
    U, A, B, C = sets["U"], sets["A"], sets["B"], sets["C"]
    E = eligible_set(A, B, C)

    return {
        "U":           U,
        "A":           A,
        "B":           B,
        "C":           C,
        "E":           E,
        "ineligible":  ineligible_set(U, E),
        "union":       union_all(A, B, C),
        "A'":          complement(A, U),
        "B'":          complement(B, U),
        "C'":          complement(C, U),
        "differences": set_differences(A, B, C),
        "count_U":     len(U),
        "count_A":     len(A),
        "count_B":     len(B),
        "count_C":     len(C),
        "count_E":     len(E),
    }


# ---------------------------------------------------------------------------
# 9. Per-building explanation
# ---------------------------------------------------------------------------

def explain_building(name: str, df: pd.DataFrame, thresholds: dict) -> dict:
    """
    Explain why a specific building is or is not eligible.

    Parameters
    ----------
    name       : str  — exact building name (must exist in df).
    df         : pd.DataFrame with canonical columns.
    thresholds : dict with threshold values.

    Returns
    -------
    dict:
        "name"     : str
        "in_A"     : bool
        "in_B"     : bool
        "in_C"     : bool
        "eligible" : bool
        "checks"   : list of dicts, each with keys:
                         "criterion", "value", "threshold", "passed", "message"
        "reason"   : str  — one-sentence summary

    Raises
    ------
    ValueError if *name* is not found in df (programmer error).
    """
    min_demand = float(thresholds.get("min_demand", DEFAULT_THRESHOLDS["min_demand"]))
    min_area   = float(thresholds.get("min_area",   DEFAULT_THRESHOLDS["min_area"]))
    min_solar  = float(thresholds.get("min_solar",  DEFAULT_THRESHOLDS["min_solar"]))

    # Locate the row — raise ValueError on unknown name (programmer error)
    mask = df[COL_NAME].astype(str) == name
    if not mask.any():
        available = ", ".join(sorted(df[COL_NAME].astype(str).tolist()))
        raise ValueError(
            f"Building '{name}' not found in the DataFrame. "
            f"Available buildings: [{available}]"
        )

    row = df[mask].iloc[0]
    demand = float(row[COL_DEMAND])
    area   = float(row[COL_AREA])
    solar  = float(row[COL_SOLAR])

    # Build per-criterion checks
    checks = [
        {
            "criterion": "Energy Demand",
            "value":     demand,
            "threshold": min_demand,
            "passed":    demand >= min_demand,
            "message": (
                f"Energy demand {demand:.1f} kWh/day meets the required "
                f"{min_demand:.1f} kWh/day"
                if demand >= min_demand
                else
                f"Energy demand {demand:.1f} kWh/day is below the required "
                f"{min_demand:.1f} kWh/day"
            ),
        },
        {
            "criterion": "Rooftop Area",
            "value":     area,
            "threshold": min_area,
            "passed":    area >= min_area,
            "message": (
                f"Rooftop area {area:.0f} m\u00b2 meets the required {min_area:.0f} m\u00b2"
                if area >= min_area
                else
                f"Rooftop area {area:.0f} m\u00b2 is below the required {min_area:.0f} m\u00b2"
            ),
        },
        {
            "criterion": "Solar Potential",
            "value":     solar,
            "threshold": min_solar,
            "passed":    solar >= min_solar,
            "message": (
                f"Solar potential {solar:.1f}% meets the required {min_solar:.1f}%"
                if solar >= min_solar
                else
                f"Solar potential {solar:.1f}% is below the required {min_solar:.1f}%"
            ),
        },
    ]

    in_A = checks[0]["passed"]
    in_B = checks[1]["passed"]
    in_C = checks[2]["passed"]
    eligible = in_A and in_B and in_C

    if eligible:
        reason = "Meets all three criteria (demand, area, and solar potential)."
    else:
        failed = [c["message"] for c in checks if not c["passed"]]
        reason = "; ".join(failed) + "."

    return {
        "name":     name,
        "in_A":     in_A,
        "in_B":     in_B,
        "in_C":     in_C,
        "eligible": eligible,
        "checks":   checks,
        "reason":   reason,
    }


# ---------------------------------------------------------------------------
# 10. Classification table
# ---------------------------------------------------------------------------

def classification_table(df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    """
    Return a DataFrame summarising eligibility for every building.

    Columns: Building, In A, In B, In C, Eligible, Reason
        - 'In A', 'In B', 'In C', 'Eligible' are bool dtype.
        - 'Reason' lists ALL failed criteria joined by "; ".
          For eligible buildings: "Meets all three criteria".
        - Sorted ascending by 'Building'.

    Parameters
    ----------
    df         : pd.DataFrame with canonical columns.
    thresholds : dict.

    Returns
    -------
    pd.DataFrame
    """
    if df is None or df.empty:
        return pd.DataFrame(
            columns=["Building", "In A", "In B", "In C", "Eligible", "Reason"]
        )

    rows = []
    for name in sorted(df[COL_NAME].astype(str).tolist()):
        info = explain_building(name, df, thresholds)
        if info["eligible"]:
            reason = "Meets all three criteria"
        else:
            failed = [c["message"] for c in info["checks"] if not c["passed"]]
            reason = "; ".join(failed)
        rows.append(
            {
                "Building": name,
                "In A":     bool(info["in_A"]),
                "In B":     bool(info["in_B"]),
                "In C":     bool(info["in_C"]),
                "Eligible": bool(info["eligible"]),
                "Reason":   reason,
            }
        )

    result = pd.DataFrame(rows)
    # Enforce bool dtype explicitly
    for col in ("In A", "In B", "In C", "Eligible"):
        result[col] = result[col].astype(bool)
    return result


# ---------------------------------------------------------------------------
# 11. Venn regions (7 exclusive regions + "none")
# ---------------------------------------------------------------------------

def venn_regions(A: set, B: set, C: set, U: set) -> dict:
    """
    Decompose U into 8 mutually exclusive Venn regions.

    Keys and their set-theory meaning:
        "A_only"  : A − (B ∪ C)         — exclusively in A
        "B_only"  : B − (A ∪ C)         — exclusively in B
        "C_only"  : C − (A ∪ B)         — exclusively in C
        "A_B"     : (A ∩ B) − C         — in A and B but not C
        "A_C"     : (A ∩ C) − B         — in A and C but not B
        "B_C"     : (B ∩ C) − A         — in B and C but not A
        "A_B_C"   : A ∩ B ∩ C           — in all three (eligible set E)
        "none"    : U − (A ∪ B ∪ C)     — in U but in none of A, B, C

    Guarantee: the eight regions are pairwise disjoint and their union == U.

    Parameters
    ----------
    A, B, C : set[str] — the three predicate subsets.
    U       : set[str] — the universal set.

    Returns
    -------
    dict[str, set[str]]
    """
    A_only  = A - (B | C)
    B_only  = B - (A | C)
    C_only  = C - (A | B)
    A_B     = (A & B) - C
    A_C     = (A & C) - B
    B_C     = (B & C) - A
    A_B_C   = A & B & C
    none    = U - (A | B | C)

    return {
        "A_only": A_only,
        "B_only": B_only,
        "C_only": C_only,
        "A_B":    A_B,
        "A_C":    A_C,
        "B_C":    B_C,
        "A_B_C":  A_B_C,
        "none":   none,
    }


# ---------------------------------------------------------------------------
# 12. Power set
# ---------------------------------------------------------------------------

def power_set(s) -> list:
    """
    Return every subset of *s* as a sorted tuple.

    The order is deterministic: the empty set first, then each new element is
    used to extend the subsets found so far.

    Parameters
    ----------
    s : iterable of str

    Returns
    -------
    list[tuple[str, ...]]  — 2 ** |s| entries.
    """
    items = sorted(str(x) for x in (s or []))
    subsets: list = [()]
    for item in items:
        subsets += [subset + (item,) for subset in subsets]
    return subsets


# ---------------------------------------------------------------------------
# 13. Filter funnel — the three criteria applied one after another
# ---------------------------------------------------------------------------

def funnel_stages(df: pd.DataFrame, thresholds: dict) -> dict:
    """
    Drop the buildings through the three criteria in turn.

    Stage 1 keeps the buildings in A, stage 2 keeps those also in B, stage 3
    keeps those also in C, so the final group is E = A ∩ B ∩ C.

    Returns
    -------
    dict with keys:
        "start"       : list[str]  — every building
        "stages"      : list of dicts, each with ``criterion`` (A/B/C),
                        ``label``, ``count_in``, ``count_out``, ``kept`` and
                        ``removed`` (a list of ``{name, reason}``)
        "final"       : list[str]  — the buildings still left
        "final_label" : str        — "E = A ∩ B ∩ C"
        "counts"      : list[int]  — sizes of the start group and after each stage
    """
    min_demand = float(thresholds.get("min_demand", DEFAULT_THRESHOLDS["min_demand"]))
    min_area   = float(thresholds.get("min_area",   DEFAULT_THRESHOLDS["min_area"]))
    min_solar  = float(thresholds.get("min_solar",  DEFAULT_THRESHOLDS["min_solar"]))

    if df is None or df.empty:
        return {
            "start": [], "stages": [], "final": [],
            "final_label": "E = A ∩ B ∩ C", "counts": [0],
        }

    values = {
        str(row[COL_NAME]): (
            float(row[COL_DEMAND]),
            float(row[COL_AREA]),
            float(row[COL_SOLAR]),
        )
        for _, row in df.iterrows()
    }
    order = sorted(values)

    criteria = [
        ("A", "demand", f"demand ≥ {min_demand:g} kWh/day",
         lambda v: v[0] >= min_demand,
         lambda v: f"demand {v[0]:g} kWh/day is below {min_demand:g}"),
        ("B", "area", f"area ≥ {min_area:g} m²",
         lambda v: v[1] >= min_area,
         lambda v: f"area {v[1]:g} m² is below {min_area:g}"),
        ("C", "solar", f"solar ≥ {min_solar:g}%",
         lambda v: v[2] >= min_solar,
         lambda v: f"solar {v[2]:g}% is below {min_solar:g}"),
    ]

    current = list(order)
    stages = []
    counts = [len(current)]
    for key, field, label, test, reason in criteria:
        kept, removed = [], []
        for name in current:
            if test(values[name]):
                kept.append(name)
            else:
                removed.append({"name": name, "reason": reason(values[name])})
        stages.append({
            "criterion": key,
            "field":     field,
            "label":     label,
            "count_in":  len(current),
            "count_out": len(kept),
            "kept":      kept,
            "removed":   removed,
        })
        current = kept
        counts.append(len(current))

    return {
        "start":       order,
        "stages":      stages,
        "final":       current,
        "final_label": "E = A ∩ B ∩ C",
        "counts":      counts,
    }
