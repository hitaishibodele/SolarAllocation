"""
stats.py — Summary-statistic functions for Sustainable Solar Energy Allocation.
All inputs are DataFrames / dicts; no Streamlit imports allowed.
"""

import pandas as pd

from algorithms.validation import (
    COL_NAME, COL_DEMAND, COL_AREA, COL_SOLAR,
)
from algorithms.set_theory import build_sets, eligible_set


def campus_stats(df: pd.DataFrame, thresholds: dict) -> dict:
    """
    Compute campus-level summary statistics.

    Returns
    -------
    dict with keys:
        total_buildings          int
        eligible_count           int
        excluded_count           int
        total_demand_kwh_day     float
        eligible_demand_kwh_day  float
        total_rooftop_area_m2    float
        eligible_rooftop_area_m2 float
        eligible_demand_share_pct float  (0.0 when total demand is 0)
        eligible_names           list[str] (sorted)
        excluded_names           list[str] (sorted)
    """
    if df is None or df.empty:
        return {
            "total_buildings":           0,
            "eligible_count":            0,
            "excluded_count":            0,
            "total_demand_kwh_day":      0.0,
            "eligible_demand_kwh_day":   0.0,
            "total_rooftop_area_m2":     0.0,
            "eligible_rooftop_area_m2":  0.0,
            "eligible_demand_share_pct": 0.0,
            "eligible_names":            [],
            "excluded_names":            [],
        }

    sets   = build_sets(df, thresholds)
    U      = sets["U"]
    E      = eligible_set(sets["A"], sets["B"], sets["C"])
    inelig = U - E

    eligible_names = sorted(E)
    excluded_names = sorted(inelig)

    total_demand = float(df[COL_DEMAND].sum())

    elig_mask = df[COL_NAME].isin(E)
    elig_df   = df[elig_mask]

    eligible_demand = float(elig_df[COL_DEMAND].sum())
    total_area      = float(df[COL_AREA].sum())
    eligible_area   = float(elig_df[COL_AREA].sum())

    if total_demand == 0.0:
        share_pct = 0.0
    else:
        share_pct = round(eligible_demand / total_demand * 100.0, 4)

    return {
        "total_buildings":           len(U),
        "eligible_count":            len(E),
        "excluded_count":            len(inelig),
        "total_demand_kwh_day":      total_demand,
        "eligible_demand_kwh_day":   eligible_demand,
        "total_rooftop_area_m2":     total_area,
        "eligible_rooftop_area_m2":  eligible_area,
        "eligible_demand_share_pct": share_pct,
        "eligible_names":            eligible_names,
        "excluded_names":            excluded_names,
    }


def chart_data(df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    """
    Return a tidy DataFrame for bar-chart rendering.

    Columns: name, energy_demand_kwh_day, rooftop_area_m2,
             solar_potential_pct, eligible
    Rows sorted by name.
    """
    _cols = [COL_NAME, COL_DEMAND, COL_AREA, COL_SOLAR, "eligible"]

    if df is None or df.empty:
        return pd.DataFrame(columns=_cols)

    sets  = build_sets(df, thresholds)
    E     = eligible_set(sets["A"], sets["B"], sets["C"])

    result = df[[COL_NAME, COL_DEMAND, COL_AREA, COL_SOLAR]].copy()
    result["eligible"] = result[COL_NAME].isin(E)
    result = result.sort_values(COL_NAME).reset_index(drop=True)
    return result
