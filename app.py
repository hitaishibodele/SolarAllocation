"""
app.py — entry point for Sustainable Solar Energy Allocation.

Thin routing layer: page config → shared style → state init → sidebar nav →
page dispatch. All logic lives in components/ and algorithms/.
"""

import streamlit as st

# Must be the very first Streamlit call
st.set_page_config(
    page_title="Sustainable Solar Energy Allocation Using Set Theory and Graph Optimization",
    layout="wide",
    page_icon=None,
    initial_sidebar_state="expanded",
)

from components.style import inject_css, status_badge            # noqa: E402
from components.charts import setup_matplotlib                   # noqa: E402
from components.state import init_state, reset_state             # noqa: E402
from components.dashboard import render_dashboard                # noqa: E402
from components.data_page import render_data_page                # noqa: E402
from components.sets_page import render_sets_page                # noqa: E402
from components.relations_page import render_relations_page      # noqa: E402
from components.logic_page import render_logic_page              # noqa: E402
from components.proofs_page import render_proofs_page            # noqa: E402
from components.counting_page import render_counting_page        # noqa: E402
from components.pigeonhole_page import render_pigeonhole_page    # noqa: E402
from components.graph_theory_page import render_graph_theory_page  # noqa: E402
from components.inclusion_exclusion_page import render_inclusion_exclusion_page  # noqa: E402

# ── Shared visual identity ────────────────────────────────────────────────────────────
inject_css()
setup_matplotlib()

# ── Session state ───────────────────────────────────────────────────────────────
init_state()

# ── Show data-load errors if any ──────────────────────────────────────────────────────
for err in st.session_state.get("load_errors", []):
    status_badge(f"Data load warning: {err}", "error")

# ── Pages ──────────────────────────────────────────────────────────────────────
_RENDERERS = {
    "Dashboard":             render_dashboard,
    "Campus Data":           render_data_page,
    "Sets":                  render_sets_page,
    "Relations & Functions": render_relations_page,
    "Logic":                 render_logic_page,
    "Proofs":                render_proofs_page,
    "Counting":              render_counting_page,
    "Pigeonhole":            render_pigeonhole_page,
    "Inclusion–Exclusion":   render_inclusion_exclusion_page,
    "Graph Theory":          render_graph_theory_page,
}
PAGES = list(_RENDERERS)

def _page_label(name: str) -> str:
    """Sidebar label: plain page name."""
    return name


def _reset_to_defaults() -> None:
    if not st.session_state.get("reset_confirm"):
        return
    reset_state()
    st.session_state["reset_confirm"] = False


with st.sidebar:
    st.markdown(
        '<div class="sn-brand">Sustainable Solar Energy Allocation</div>'
        '<div class="sn-brand-tag">Using Set Theory and Graph Optimization</div>'
        '<hr class="sn-brand-line">',
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigate to",
        options=PAGES,
        format_func=_page_label,
        key="nav_page",
        label_visibility="collapsed",
    )

    # ── Campus card ───────────────────────────────────────────────────────────
    _df  = st.session_state.get("buildings")
    _thr = st.session_state.get("thresholds", {})
    if _df is not None and not _df.empty:
        try:
            from algorithms.set_theory import build_sets, eligible_set
            _sets = build_sets(_df, _thr)
            _elig = sorted(eligible_set(_sets["A"], _sets["B"], _sets["C"]))
            _n    = len(_df)
            _e    = len(_elig)
            _edges = st.session_state.get("edges") or []
            _card = (
                '<div class="sn-campus-card">' +
                '<div class="sn-campus-card-title">Campus snapshot</div>' +
                '<div class="sn-campus-row">' +
                  '<span class="sn-campus-label">Buildings</span>' +
                  f'<span class="sn-campus-val">{_n}</span>' +
                '</div>' +
                '<div class="sn-campus-row">' +
                  '<span class="sn-campus-label">Solar-ready</span>' +
                  f'<span class="sn-campus-val green">{_e} of {_n}</span>' +
                '</div>' +
                '<div class="sn-campus-row">' +
                  '<span class="sn-campus-label">Connections</span>' +
                  f'<span class="sn-campus-val amber">{len(_edges)}</span>' +
                '</div>' +
                '</div>'
            )
            st.markdown(_card, unsafe_allow_html=True)
        except Exception:
            pass

    st.markdown('<hr class="sn-brand-line">', unsafe_allow_html=True)
    confirm = st.checkbox(
        "Confirm reset",
        key="reset_confirm",
        help="Tick to enable the reset button.",
    )
    st.button(
        "Reset to defaults",
        on_click=_reset_to_defaults,
        disabled=not confirm,
        help="Restore the original campus data.",
    )

# ── Page dispatch ──────────────────────────────────────────────────────────────────
_RENDERERS.get(page, lambda: status_badge("Select a page from the sidebar.", "info"))()
