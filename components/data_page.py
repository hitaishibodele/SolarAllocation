"""
data_page.py — the Campus Data page.

The one place to edit everything the rest of the app reads: the buildings, the
eligibility thresholds and the candidate connections.  Everything is validated
before it is stored, and the previous valid state is kept whenever an edit
fails, so no page can ever show a half-broken dataset.

All validation is delegated to algorithms/validation.py.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from algorithms.validation import (
    validate_buildings,
    validate_thresholds,
    validate_edges,
    COL_NAME, COL_DEMAND, COL_AREA, COL_SOLAR,
    REQUIRED_COLUMNS,
)
from algorithms.data_loader import (
    load_buildings,
    get_default_edges,
)

from components.style import (
    AMBER,
    GREEN,
    callout,
    fmt_num,
    kpi_row,
    page_header,
    section_card,
    math_box,
)


# ── Column config for the buildings editor ────────────────────────────────────
_BUILDING_COL_CONFIG = {
    COL_NAME:   st.column_config.TextColumn(
        "Building Name", required=True,
        help="A unique building name.",
    ),
    COL_DEMAND: st.column_config.NumberColumn(
        "Energy Demand (kWh/day)", min_value=0.0, format="%.1f",
        help="Average daily energy demand in kWh/day.",
    ),
    COL_AREA:   st.column_config.NumberColumn(
        "Rooftop Area (m²)", min_value=0.0, format="%.0f",
        help="Usable rooftop area in m².",
    ),
    COL_SOLAR:  st.column_config.NumberColumn(
        "Solar Potential (%)", min_value=0.0, max_value=100.0, format="%.1f",
        help="How much sunlight the roof receives, 0–100%.",
    ),
}


# ── helpers ───────────────────────────────────────────────────────────────────

def _current_building_names() -> list:
    df = st.session_state.get("buildings", pd.DataFrame())
    if df is None or df.empty:
        return []
    return sorted(df[COL_NAME].astype(str).tolist())


def _error_list(heading: str, errors) -> None:
    if not errors:
        return
    bullets = "\n".join(f"- {e}" for e in errors)
    callout(f"**{heading}**\n\n{bullets}", "error")


def _drop_invalid_edges(new_names: list) -> tuple:
    """Remove connections that touch a building no longer in *new_names*."""
    edges = st.session_state.get("edges", [])
    if not edges:
        return edges, []
    kept, dropped_msgs = [], []
    name_set = set(new_names)
    for u, v in edges:
        missing = [n for n in (u, v) if n not in name_set]
        if missing:
            dropped_msgs.append(
                f"Connection ({u} — {v}) removed: "
                f"{', '.join(missing)} is no longer in the buildings table."
            )
        else:
            kept.append((u, v))
    return kept, dropped_msgs


# ═══════════════════════════════════════════════════════════════════════════════
# Tab 1 — Buildings
# ═══════════════════════════════════════════════════════════════════════════════

def _render_buildings_tab() -> None:
    df: pd.DataFrame = st.session_state.get("buildings", pd.DataFrame())
    if df is None:
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)

    with section_card(
        "Buildings",
        "One row per building. Edit a cell or add a row, then press "
        "Apply changes to validate and save.",
    ):
        edited = st.data_editor(
            df.copy(),
            num_rows="dynamic",
            column_config=_BUILDING_COL_CONFIG,
            width="stretch",
            key="buildings_editor",
            hide_index=True,
        )

        col_apply, col_reset = st.columns([1, 1])

        with col_apply:
            if st.button("✅ Apply changes", key="apply_buildings", type="primary",
                         help="Validate the edited table and save the valid rows."):
                for col in REQUIRED_COLUMNS:
                    if col not in edited.columns:
                        edited[col] = None

                clean_df, errors = validate_buildings(edited)

                if errors:
                    _error_list("These rows could not be saved:", errors)
                    if clean_df.empty:
                        callout(
                            "**No valid rows remain**, so the previous buildings "
                            "are kept.\n\n"
                            "**What to do:** fix the errors above and apply again.",
                            "warning",
                        )
                        return

                new_names = clean_df[COL_NAME].astype(str).tolist()
                kept_edges, dropped_msgs = _drop_invalid_edges(new_names)
                for msg in dropped_msgs:
                    callout(msg, "warning")
                if dropped_msgs:
                    st.session_state["edges"] = kept_edges

                st.session_state["buildings"] = clean_df
                callout(f"Saved {len(clean_df)} valid building(s).", "success")

        with col_reset:
            if st.button("🔄 Reset buildings to defaults", key="reset_buildings",
                         help="Reload the original campus buildings and their "
                              "connections."):
                default_df, errors = load_buildings()
                if errors:
                    _error_list("Could not load the default buildings:", errors)
                else:
                    st.session_state["buildings"] = default_df
                    st.session_state["edges"]     = get_default_edges()
                    callout("Buildings reset to the original campus data.",
                            "success")
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# Tab 2 — Thresholds
# ═══════════════════════════════════════════════════════════════════════════════

def _render_thresholds_tab() -> None:
    t = st.session_state.get("thresholds", {})

    kpi_row([
        {"label": "Min. demand", "value": f"{fmt_num(t.get('min_demand', 400.0), 0)}",
         "sublabel": "kWh/day — set A", "accent": GREEN},
        {"label": "Min. rooftop area", "value": f"{fmt_num(t.get('min_area', 800.0), 0)}",
         "sublabel": "m² — set B", "accent": GREEN},
        {"label": "Min. solar potential", "value": f"{fmt_num(t.get('min_solar', 75.0), 1)}",
         "sublabel": "% — set C", "accent": AMBER},
    ], per_row=3)

    with section_card(
        "Eligibility thresholds",
        "The thresholds decide which buildings join the sets A, B and C. "
        "Nothing changes elsewhere until you press Apply.",
    ):
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            new_demand = st.number_input(
                "Min. demand (kWh/day)",
                min_value=0.0, max_value=100_000.0,
                value=float(t.get("min_demand", 400.0)),
                step=50.0, key="dm_min_demand",
                help="A building joins set A when its daily demand is at least "
                     "this value.",
            )
        with tc2:
            new_area = st.number_input(
                "Min. rooftop area (m²)",
                min_value=0.0, max_value=100_000.0,
                value=float(t.get("min_area", 800.0)),
                step=50.0, key="dm_min_area",
                help="A building joins set B when its rooftop area is at least "
                     "this value.",
            )
        with tc3:
            new_solar = st.number_input(
                "Min. solar potential (%)",
                min_value=0.0, max_value=100.0,
                value=float(t.get("min_solar", 75.0)),
                step=5.0, key="dm_min_solar",
                help="A building joins set C when its solar potential is at "
                     "least this percentage.",
            )

        if st.button("✅ Apply thresholds", key="apply_thresholds",
                     type="primary",
                     help="Validate and save the eligibility thresholds."):
            new_t = {"min_demand": new_demand, "min_area": new_area,
                     "min_solar": new_solar}
            clean_t, t_errs = validate_thresholds(new_t)
            _error_list("Thresholds could not be saved:", t_errs)

            if not t_errs:
                st.session_state["thresholds"] = clean_t
                callout("Thresholds saved.", "success")
            else:
                callout(
                    "Thresholds were not saved because of the errors above; the "
                    "previous thresholds are kept.",
                    "warning",
                )

    math_box(
        r"A = \{b : \text{demand}(b) \ge \text{min\_demand}\},\quad "
        r"B = \{b : \text{area}(b) \ge \text{min\_area}\},\quad "
        r"C = \{b : \text{solar}(b) \ge \text{min\_solar}\}",
        "The three thresholds define the three sets.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Tab 3 — Candidate Connections
# ═══════════════════════════════════════════════════════════════════════════════

def _render_edges_tab() -> None:
    building_names = _current_building_names()
    edges          = st.session_state.get("edges", [])

    edge_rows = [{"Building A": u, "Building B": v} for u, v in edges]
    edge_df = pd.DataFrame(
        edge_rows if edge_rows else [{"Building A": "", "Building B": ""}],
        columns=["Building A", "Building B"],
    )

    with section_card(
        "Candidate connections",
        "Each row is a pair of buildings that could share a cable route. The "
        "order does not matter: A—B is the same connection as B—A.",
    ):
        if not building_names:
            callout(
                "**There are no buildings to connect.** Add buildings on the "
                "**Buildings** tab first.",
                "info",
            )

        edited_edges = st.data_editor(
            edge_df,
            num_rows="dynamic",
            width="stretch",
            key="edges_editor",
            hide_index=True,
            column_config={
                "Building A": st.column_config.SelectboxColumn(
                    "Building A",
                    options=building_names if building_names else ["(no buildings)"],
                    required=True,
                    help="One end of the candidate connection.",
                ),
                "Building B": st.column_config.SelectboxColumn(
                    "Building B",
                    options=building_names if building_names else ["(no buildings)"],
                    required=True,
                    help="The other end (the pair is stored in alphabetical order).",
                ),
            },
        )

        if st.button("✅ Apply connections", key="apply_edges", type="primary",
                     help="Validate and save the candidate connections."):
            raw_edges = []
            for _, row in edited_edges.iterrows():
                u = str(row.get("Building A", "") or "").strip()
                v = str(row.get("Building B", "") or "").strip()
                if u and v:
                    raw_edges.append((u, v))

            clean_edges, errors = validate_edges(raw_edges, building_names)
            _error_list("These connections could not be saved:", errors)

            st.session_state["edges"] = clean_edges
            if errors:
                callout(
                    f"Saved {len(clean_edges)} valid connection(s): the "
                    f"{len(errors)} connection(s) listed above were skipped.",
                    "warning",
                )
            else:
                callout(f"Saved {len(clean_edges)} valid connection(s).", "success")


# ═══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════════════════════════════════════

def render_data_page() -> None:
    """Render the full Campus Data page."""
    page_header(
        "What are the campus numbers?",
        "Every other page reads from this one. Change the buildings, the "
        "thresholds or the candidate connections and the whole planner follows.",
    )

    tab_buildings, tab_thresholds, tab_edges = st.tabs(
        ["🏢 Buildings", "⚙️ Thresholds", "🔗 Candidate Connections"]
    )

    with tab_buildings:
        _render_buildings_tab()

    with tab_thresholds:
        _render_thresholds_tab()

    with tab_edges:
        _render_edges_tab()
