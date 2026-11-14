"""
relations_page.py — "Which buildings can share a cable route?"

A cable route between two buildings is a pair, and a collection of pairs is a
relation.  Two relations run through this page:

  * "can be connected to" — built from the candidate connections;
  * "has at least as much demand as" — a comparison of daily demand.

The last part of the page reads the same campus as three functions: the demand
of a building, the yes/no answer of the eligibility rule, and the position of an
eligible building in the demand order.

Every number comes from algorithms/; this module only formats what they return.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from algorithms.relations import (
    domain_of,
    ranking,
)
from algorithms.functions import function_overview
from algorithms.validation import COL_NAME, DEFAULT_THRESHOLDS
from algorithms.visual_data import (
    function_data,
    ranking_data,
    relation_diagram_data,
)

from components.style import (
    AMBER,
    FOREST,
    GREEN,
    callout,
    card_grid,
    concept_card,
    empty_buildings_notice,
    esc,
    kpi_row,
    math_box,
    page_header,
    section_card,
    section_title,
    show_visual,
)
from components.visuals import function_maps, ranking_ladder, relation_diagram


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

def _connection_chooser(edges) -> list:
    """
    Let the reader switch candidate connections on and off.

    The connections in the data are selected by default, so the picture starts
    from the current campus and only changes when a connection is removed.
    """
    pairs = sorted({tuple(sorted((str(u), str(v)))) for u, v in (edges or [])})
    if not pairs:
        return []

    labels = {f"{u} — {v}": (u, v) for u, v in pairs}

    with st.expander("Try different numbers — switch candidate connections on and off",
                     expanded=False):
        st.caption(
            "Every connection you keep stays in the relation. Dropping one can "
            "turn a property of the relation from true to false, and the badges "
            "in the picture below follow it immediately."
        )
        picked = st.multiselect(
            "Candidate connections in play",
            options=list(labels),
            default=list(labels),
            help="The current campus connections are the default selection.",
        )
    return [labels[name] for name in picked]


def _equal_pair_control(df: pd.DataFrame):
    """
    Optional: give two buildings the same daily demand to show a tie.

    Returns ``(a, b)`` when the switch is on, otherwise ``None``.
    """
    order = ranking(df)
    if len(order) < 2:
        return None

    with st.expander("Try different numbers — give two buildings the same demand",
                     expanded=False):
        st.caption(
            "With distinct demands, comparing demand orders every building from "
            "first to last with no ties. Flatten two of the values and the "
            "ladder shows what a tie does to that order."
        )
        on = st.toggle("Give two buildings the same demand",
                       value=False, key="rel_equal_on")
        c1, c2 = st.columns(2)
        with c1:
            first = st.selectbox("First building", options=order, index=0,
                                 key="rel_equal_a", disabled=not on)
        with c2:
            second = st.selectbox("Second building", options=order, index=1,
                                  key="rel_equal_b", disabled=not on)

    if not on or first == second:
        return None
    return (first, second)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

def render_relations_page() -> None:
    """Render the Relations & Functions page."""
    page_header(
        "Which buildings can share a cable route, and how do their demands compare?",
        "Two buildings that could share a cable route form a pair. Collecting "
        "those pairs gives a relation on the campus, and the same idea — a rule "
        "that pairs each building with an answer — gives the three functions at "
        "the bottom of this page.",
    )

    df = st.session_state.get("buildings", pd.DataFrame())
    thresholds = st.session_state.get("thresholds", DEFAULT_THRESHOLDS.copy())
    edges = st.session_state.get("edges", [])

    if df is None or df.empty:
        empty_buildings_notice()
        return

    chosen_edges = _connection_chooser(edges)
    relation = relation_diagram_data(df, chosen_edges, thresholds)
    domain = domain_of(df)

    kpi_row([
        {"label": "Buildings", "value": str(len(domain)),
         "sublabel": "the set the relation lives on", "accent": FOREST},
        {"label": "Candidate connections", "value": str(len(chosen_edges)),
         "sublabel": "pairs kept from the data", "accent": GREEN},
        {"label": "Ordered pairs", "value": str(relation["pair_count"]),
         "sublabel": "each connection counts twice", "accent": AMBER},
        {"label": "Properties true",
         "value": f"{sum(1 for b in relation['badges'] if b['passed'])}"
                  f" of {len(relation['badges'])}",
         "sublabel": "reflexive, symmetric, antisymmetric, transitive, equivalence",
         "accent": GREEN},
    ], per_row=4)

    # ── 1. The connection relation ───────────────────────────────────────────
    with section_card(
        "Connections between buildings",
        "Buildings sit on a ring and a line joins two buildings that could share "
        "a cable route. Press a badge to see the pair that makes the property "
        "hold or fail; the grid on the right marks every ordered pair.",
    ):
        show_visual(relation_diagram(relation), height=480)

    # ── 2. The demand relation ───────────────────────────────────────────────
    equal_pair = _equal_pair_control(df)
    ladder = ranking_data(df, thresholds, equal_pair)
    with section_card(
        "How the demands compare",
        "Read “is at least as much as” as a relation: the pair (x, y) is in it "
        "when x uses at least as much energy per day as y. The ladder lists the "
        "buildings from the largest demand to the smallest.",
    ):
        show_visual(ranking_ladder(ladder), height=380)

    # ── 3. Three functions on the same campus ────────────────────────────────
    overview = function_overview(df, thresholds)
    with section_card(
        "Three functions on the same buildings",
        "A function gives every building in its domain exactly one answer. "
        "Switch between the three below; an arrow runs from each building to its "
        "answer, and a red dot marks an answer that nothing reaches.",
    ):
        show_visual(function_maps(function_data(df, thresholds)), height=470)

    # ── 4. How it works ──────────────────────────────────────────────────────
    section_title("How it works")

    st.markdown(
        "**Relations.** A *relation* on the campus is a set of ordered pairs (x, y) "
        "drawn from U × U. The connection relation pairs buildings that could share a "
        "cable route; each undirected link adds both (x, y) and (y, x)."
    )
    _pair_count = relation["pair_count"]
    _n_edges = len(chosen_edges)
    _n_domain = len(domain)
    math_box(
        r"R = \{(x, y) \in U \times U : x \text{ can be connected to } y\}",
        f"{_pair_count} ordered pairs from {_n_edges} connection(s) on {_n_domain} buildings.",
    )

    badge_lines = []
    for badge in relation["badges"]:
        state = "holds" if badge["passed"] else "fails"
        _label = badge["label"]
        badge_lines.append(f"- **{_label} — {state}.**")
    st.markdown("\n".join(badge_lines))

    tie_text = (
        "No ties — every pair is comparable."
        if ladder["total_order"] else
        "Some buildings share a demand value, creating ties in the order."
    )
    _note = ladder["note"]
    st.markdown(
        f"**Demand order.** (x, y) is in this relation when demand(x) ≥ demand(y). "
        f"It is reflexive, antisymmetric and transitive — making it an order. {tie_text}"
        + (f" {_note}" if _note else "")
    )

    st.markdown(
        "**Functions.** A relation is a *function* when every element of its domain "
        "maps to exactly one answer. The three functions on this campus:"
    )
    demand_info = overview["demand"]
    elig_info = overview["eligible"]
    rank_info = overview["rank"]

    _d_dom = len(demand_info["domain"])
    demand_text = (
        f"{_d_dom} buildings → their daily demand. "
        + ("One-to-one and onto (bijection)." if demand_info["bijective"] else
           "Not one-to-one — two or more buildings share a demand value.")
    )
    _e_dom = len(elig_info["domain"])
    elig_text = (
        f"{_e_dom} buildings → 0 or 1. "
        + ("Onto but not one-to-one."
           if elig_info["surjective"] and not elig_info["injective"] else
           "Shows which buildings qualify.")
    )
    _r_dom = len(rank_info["domain"])
    _r_cod = len(rank_info["codomain"])
    rank_text = (
        f"{_r_dom} eligible buildings → ranks 1…{_r_cod}. "
        + ("Bijection." if rank_info["bijective"] else
           "Eligible group is empty or contains a tie.")
    )

    card_grid([
        concept_card("demand : U → demand values", demand_text),
        concept_card("eligible : U → {0, 1}", elig_text),
        concept_card("rank : E → {1, …, |E|}", rank_text),
    ], per_row=3)

    # ── 5. Ordered pairs grid ─────────────────────────────────────────────────
    section_title("Ordered pairs")
    st.caption(
        "The relation written out as a grid. A 1 means the pair "
        "(row building, column building) is in the relation."
    )
    matrix = relation["matrix"]
    if matrix["labels"]:
        grid = pd.DataFrame(
            matrix["grid"],
            index=matrix["labels"],
            columns=[name[:3] for name in matrix["labels"]],
        )
        st.dataframe(grid, width="stretch")
    else:
        callout("No buildings are loaded, so the grid is empty.", "info")
