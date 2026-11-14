"""
sets_page.py — "Which buildings clear all three requirements?"

The three requirements (demand, rooftop area, solar potential) are three sets
A, B and C over the same campus.  This page draws the campus as tiles, drops it
through the three requirements one at a time, and shows the overlap as a
three-set diagram.

The sliders on this page write straight into the shared thresholds, so every
count here — and every page and picture in the planner — follows them at once.

All numbers come from algorithms/; this module only formats what they return.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from algorithms.set_theory import (
    build_sets,
    eligible_set,
    ineligible_set,
    classification_table,
)
from algorithms.validation import DEFAULT_THRESHOLDS, validate_thresholds
from algorithms.visual_data import (
    campus_map_data,
    funnel_data,
    power_set_data,
    venn_data,
)

from components.style import (
    AMBER,
    FOREST,
    GREEN,
    INELIGIBLE,
    callout,
    card_grid,
    concept_card,
    empty_buildings_notice,
    esc,
    kpi_row,
    math_box,
    page_header,
    pill_row,
    section_card,
    section_title,
    show_visual,
)
from components.visuals import campus_map, filter_funnel, venn_diagram


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _names(values) -> str:
    """A sorted, escaped, comma-separated rendering of a set of names."""
    items = sorted(str(n) for n in (values or []))
    return ", ".join(esc(n) for n in items) if items else "the empty set"


def _limits(thresholds) -> dict:
    t = thresholds or {}
    return {
        "min_demand": float(t.get("min_demand", DEFAULT_THRESHOLDS["min_demand"])),
        "min_area":   float(t.get("min_area",   DEFAULT_THRESHOLDS["min_area"])),
        "min_solar":  float(t.get("min_solar",  DEFAULT_THRESHOLDS["min_solar"])),
    }


# ---------------------------------------------------------------------------
# Live threshold controls
# ---------------------------------------------------------------------------

def _threshold_controls(thresholds) -> dict:
    """
    Three live sliders over the shared eligibility thresholds.

    Moving a slider validates the new values and stores them at once, so the
    pictures below — and every other page — recompute immediately.  If a value
    fails validation the previous thresholds are kept and the reason is shown.
    """
    values = _limits(thresholds)

    with section_card(
        "Set the three thresholds",
        "Each slider is one requirement. They apply together: a building is "
        "eligible only when it clears all three.",
    ):
        c1, c2, c3 = st.columns(3)
        with c1:
            new_demand = st.slider(
                "Demand of at least (kWh/day)",
                min_value=0.0, max_value=2000.0, step=50.0,
                value=values["min_demand"],
                help="Set A collects the buildings whose daily demand reaches "
                     "this value.",
            )
        with c2:
            new_area = st.slider(
                "Rooftop area of at least (m²)",
                min_value=0.0, max_value=2000.0, step=50.0,
                value=values["min_area"],
                help="Set B collects the buildings whose rooftop area reaches "
                     "this value.",
            )
        with c3:
            new_solar = st.slider(
                "Solar potential of at least (%)",
                min_value=0.0, max_value=100.0, step=5.0,
                value=values["min_solar"],
                help="Set C collects the buildings whose solar potential "
                     "reaches this percentage.",
            )

    candidate = {"min_demand": new_demand,
                 "min_area":   new_area,
                 "min_solar":  new_solar}
    if candidate == values:
        return values

    clean, errors = validate_thresholds(candidate)
    if errors:
        for message in errors:
            callout(message, "error")
        callout("The previous thresholds are kept.", "warning")
        return values

    st.session_state["thresholds"] = clean
    return clean


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

def render_sets_page() -> None:
    """Render the Sets page."""
    page_header(
        "Which buildings clear all three requirements?",
        "Every building is measured three ways: how much energy it uses each "
        "day, how much rooftop it offers, and how much sun that roof catches. "
        "A building that clears all three joins the eligible group.",
    )

    df = st.session_state.get("buildings", pd.DataFrame())
    thresholds = st.session_state.get("thresholds", DEFAULT_THRESHOLDS.copy())

    if df is None or df.empty:
        empty_buildings_notice()
        return

    thresholds = _threshold_controls(thresholds)
    limits = _limits(thresholds)

    sets = build_sets(df, thresholds)
    U, A, B, C = sets["U"], sets["A"], sets["B"], sets["C"]
    E = eligible_set(A, B, C)
    outside = ineligible_set(U, E)

    kpi_row([
        {"label": "Buildings", "value": str(len(U)),
         "sublabel": "universal set U", "accent": FOREST},
        {"label": "Meet demand", "value": str(len(A)),
         "sublabel": f"set A · ≥ {limits['min_demand']:g} kWh/day",
         "accent": GREEN},
        {"label": "Meet area", "value": str(len(B)),
         "sublabel": f"set B · ≥ {limits['min_area']:g} m²", "accent": GREEN},
        {"label": "Meet solar", "value": str(len(C)),
         "sublabel": f"set C · ≥ {limits['min_solar']:g}%", "accent": AMBER},
        {"label": "Eligible", "value": str(len(E)),
         "sublabel": "E = A ∩ B ∩ C", "accent": GREEN},
    ], per_row=5)

    # ── 1. Campus map ────────────────────────────────────────────────────────
    with section_card(
        "The campus building by building",
        "Tile size follows rooftop area, the sun icon follows solar potential "
        "and the bar is daily demand. A green tile clears all three "
        "requirements; a grey tile names the one it misses.",
    ):
        show_visual(campus_map(campus_map_data(df, thresholds)), height=430)

        # ── 2. Three-set Venn diagram ────────────────────────────────────────────
    with section_card(
        "The three sets and the buildings in the middle",
        "Hover a region for its size, click it to list its buildings.",
    ):
        show_visual(venn_diagram(venn_data(df, thresholds)), height=500)

    # ── 3. How it works ──────────────────────────────────────────────────────
    section_title("How it works")
    st.markdown(
        f"A building is eligible when it is in **A** (demand ≥ {limits['min_demand']:g} kWh/day), "
        f"**B** (roof ≥ {limits['min_area']:g} m²) and **C** (solar ≥ {limits['min_solar']:g}%) "
        f"at the same time."
    )
    math_box(r"E = A \cap B \cap C", "Eligible now: " + (", ".join(sorted(E)) or "none"))
    pill_row([(name, "eligible") for name in sorted(E)]
             + [(name, "ineligible") for name in sorted(outside)])

    with st.expander("Building by building"):
        st.dataframe(
            classification_table(df, thresholds),
            width="stretch",
            hide_index=True,
        )