"""
logic_page.py — "Which combinations of conditions make a building eligible?"

The eligibility rule is a conjunction of three campus-specific conditions:

    eligible  ≡  p ∧ q ∧ r

where p checks demand, q checks rooftop area, and r checks solar potential.
This page draws the rule as a circuit, shows all eight combinations in a
truth table, and verifies De Morgan's law on the same data.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from algorithms.validation import DEFAULT_THRESHOLDS
from algorithms.visual_data import (
    de_morgan_data,
    logic_gate_data,
    truth_table_data,
)

from components.style import (
    AMBER,
    FOREST,
    GREEN,
    callout,
    empty_buildings_notice,
    kpi_row,
    math_box,
    page_header,
    section_card,
    section_title,
    show_visual,
)
from components.visuals import (
    de_morgan,
    logic_gate,
    truth_table_grid,
)


def _limits(thresholds) -> dict:
    t = thresholds or {}
    return {
        "min_demand": float(t.get("min_demand", DEFAULT_THRESHOLDS["min_demand"])),
        "min_area":   float(t.get("min_area",   DEFAULT_THRESHOLDS["min_area"])),
        "min_solar":  float(t.get("min_solar",  DEFAULT_THRESHOLDS["min_solar"])),
    }


def render_logic_page() -> None:
    """Render the Logic page."""
    page_header(
        "Which combinations of conditions make a building eligible?",
        "Each requirement is a yes/no question. Three of them together give "
        "eight possible combinations, and only one — demand high, roof large, "
        "sun strong — makes a building eligible.",
    )

    df = st.session_state.get("buildings", pd.DataFrame())
    thresholds = st.session_state.get("thresholds", DEFAULT_THRESHOLDS.copy())

    if df is None or df.empty:
        empty_buildings_notice()
        return

    limits = _limits(thresholds)
    gate = logic_gate_data(df, thresholds)
    covered = [row for row in gate["rows"] if row["buildings"]]
    buildings_in_covered = sum(len(row["buildings"]) for row in covered)

    kpi_row([
        {"label": "Conditions in play", "value": "3",
         "sublabel": "p — demand, q — area, r — solar", "accent": FOREST},
        {"label": "Combinations", "value": "8",
         "sublabel": "2 × 2 × 2 rows of the truth table", "accent": GREEN},
        {"label": "Combinations used", "value": f"{len(covered)}",
         "sublabel": "rows that describe at least one building", "accent": AMBER},
        {"label": "Buildings covered", "value": f"{buildings_in_covered}",
         "sublabel": "every building sits in exactly one row", "accent": GREEN},
    ], per_row=4)

    _md = limits["min_demand"]
    _ma = limits["min_area"]
    _ms = limits["min_solar"]
    st.markdown(
        f"Reading p as **demand \u2265 {_md:g} kWh/day**, q as "
        f"**rooftop area \u2265 {_ma:g} m\u00b2** and r as "
        f"**solar potential \u2265 {_ms:g}%**, the rule is "
        f"*eligible \u2261 p \u2227 q \u2227 r*: all three conditions at once."
    )

    # \u2500\u2500 1. The circuit \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    with section_card(
        "Three conditions wired together",
        "Pick a building from the list, or flip the switches by hand. "
        "The lamp lights when all three switches are on. "
        "The highlighted row in the truth table shows which combination is active.",
    ):
        show_visual(logic_gate(gate), height=490)

    # \u2500\u2500 2. The truth table \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    with section_card(
        "All eight combinations",
        "Every combination of the three conditions is listed, with the campus "
        "buildings that fall into each row. Click a row to isolate it.",
    ):
        show_visual(truth_table_grid(truth_table_data(df, thresholds)), height=360)

    # \u2500\u2500 3. De Morgan's law \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    with section_card(
        "De Morgan's law on the campus",
        "A building is not eligible if and only if at least one condition fails. "
        "Step through all eight rows to see both sides always agree.",
    ):
        show_visual(de_morgan(de_morgan_data(df, thresholds)), height=280)

    # \u2500\u2500 4. How it works \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    section_title("How it works")

    st.markdown(
        "**Propositions on this campus.** Each condition is a yes/no statement "
        "that every building either satisfies or does not:"
    )
    st.markdown(
        f"- **p** \u2014 demand \u2265 {_md:g} kWh/day\n"
        f"- **q** \u2014 rooftop area \u2265 {_ma:g} m\u00b2\n"
        f"- **r** \u2014 solar potential \u2265 {_ms:g}%"
    )
    math_box(
        r"\text{eligible} \;\equiv\; p \land q \land r",
        "All three must hold simultaneously.",
    )

    st.markdown("**Each building on the current campus:**")
    for row in gate["rows"]:
        pv = "1" if row["p"] else "0"
        qv = "1" if row["q"] else "0"
        rv = "1" if row["r"] else "0"
        outcome = "eligible" if (row["p"] and row["q"] and row["r"]) else "not eligible"
        who = ", ".join(b["label"] for b in row["buildings"])
        if who:
            st.markdown(f"- p={pv}, q={qv}, r={rv} \u2192 **{outcome}** \u2014 {who}")

    st.markdown(
        "**De Morgan's law** connects the AND gate to the eligibility decision: "
        "a building *fails* eligibility (output 0 from the AND gate) exactly "
        "when at least one condition is false."
    )
    math_box(
        r"\neg(p \land q \land r) \;\equiv\; (\neg p) \lor (\neg q) \lor (\neg r)",
        "Not eligible \u21d4 demand too low, or area too small, or solar too weak.",
    )

    # \u2500\u2500 5. Campus data tables \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    tab_table, tab_buildings = st.tabs(["Truth table in full", "Building by building"])

    with tab_table:
        st.caption(
            "All eight combinations of the three conditions, with the campus "
            "buildings that fall into each row."
        )
        table = truth_table_data(df, thresholds)
        st.dataframe(
            pd.DataFrame([
                {"p (demand)": row["p"], "q (area)": row["q"], "r (solar)": row["r"],
                 "eligible": row["eligible"],
                 "buildings": ", ".join(b["label"] for b in row["buildings"]) or "\u2014"}
                for row in table["rows"]
            ]),
            width="stretch",
            hide_index=True,
        )

    with tab_buildings:
        st.caption(
            "One row per building showing which of the three conditions it meets."
        )
        st.dataframe(
            pd.DataFrame([
                {"building": b["label"],
                 "p (demand)": b["p"], "q (area)": b["q"], "r (solar)": b["r"],
                 "eligible": b["eligible"]}
                for b in gate["buildings"]
            ]),
            width="stretch",
            hide_index=True,
        )
