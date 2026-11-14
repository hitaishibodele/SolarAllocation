"""
style.py — Design system for Sustainable Solar Energy Allocation.

Single source of truth for:

  * the colour palette (used by every page and every visual),
  * the page chrome (banner, KPI cards, section cards, pills, callouts,
    math panels, concept cards, status messages),
  * the shared number formatters,
  * the global stylesheet.

Nothing here computes a stored value; this module only defines presentation.
All user-supplied text (building names, free text) is escaped with
``html.escape`` before it is interpolated into HTML or markdown.

Streamlit is imported lazily inside the functions that need it so this module
can be imported outside a Streamlit runtime.
"""

from __future__ import annotations

import contextlib
import hashlib
import html as _html


# ===========================================================================
# Palette — named constants, reused by the CSS *and* by every chart
# ===========================================================================

FOREST        = "#14532D"   # deep forest green — headings, sidebar
FOREST_DEEP   = "#0F3D21"
GREEN         = "#16A34A"   # solar green — eligible buildings, graph edges
GREEN_DARK    = "#15803D"
LEAF          = "#DCFCE7"   # leaf tint — soft green surface
LEAF_SOFT     = "#F0FDF4"
AMBER         = "#F59E0B"   # sun amber — highlights, path display, accents
AMBER_DEEP    = "#B45309"
AMBER_SOFT    = "#FEF3C7"
BACKGROUND    = "#FAFAF7"   # app background
CARD          = "#FFFFFF"   # card / chart background
INK           = "#1F2937"   # body text
MUTED         = "#6B7280"   # captions, secondary text, unselected edges
BORDER        = "#E5E7EB"   # hairlines, borders
DANGER        = "#DC2626"   # ineligible buildings, errors
DANGER_SOFT   = "#FEE2E2"
INFO          = "#2563EB"   # used sparingly (informational accents)
INFO_SOFT     = "#DBEAFE"

# ── semantic aliases (the words pages and charts should think in) ──────────
ELIGIBLE      = GREEN
INELIGIBLE    = DANGER



# Venn regions (A, B, C and the A ∩ B ∩ C highlight)
VENN_A        = "#86EFAC"
VENN_B        = "#BFDBFE"
VENN_C        = "#FDE68A"
VENN_E        = FOREST

# Network graph nodes
NODE_FILL     = LEAF
NODE_EDGE     = FOREST

# Pill colour pairs: kind -> (background, foreground)
PILL_COLORS = {
    "eligible":   (LEAF, GREEN_DARK),
    "accepted":   (LEAF, GREEN_DARK),
    "success":    (LEAF, GREEN_DARK),
    "ineligible": (DANGER_SOFT, DANGER),
    "rejected":   (DANGER_SOFT, DANGER),
    "error":      (DANGER_SOFT, DANGER),
    "skipped":    ("#F3F4F6", MUTED),
    "neutral":    ("#F3F4F6", MUTED),
    "warning":    (AMBER_SOFT, AMBER_DEEP),
    "info":       (INFO_SOFT, INFO),
}


# ===========================================================================
# Shared text / number helpers
# ===========================================================================

def esc(text) -> str:
    """Escape *text* for safe interpolation into HTML / markdown."""
    return _html.escape(str(text), quote=True)




def fmt_num(x, decimals: int = 2) -> str:
    """Format a plain number with a fixed number of decimals."""
    return f"{float(x):,.{decimals}f}"


def fmt_int(x) -> str:
    """Format a whole number with thousands separators."""
    return f"{float(x):,.0f}"


def fmt_pct(x, decimals: int = 1) -> str:
    """Format a percentage value that is already expressed in percent."""
    return f"{float(x):.{decimals}f}%"


def data_source_note() -> None:
    """The standard line under every page heading."""
    import streamlit as st
    st.caption(
        "Every figure on this page is computed live from the campus data and "
        "the thresholds you set."
    )


# ===========================================================================
# Page chrome — hero banner, KPI cards, section cards
# ===========================================================================

def hero_banner(title: str, subtitle: str = "",
                badge_text: str = "") -> None:
    """
    Light gradient banner at the top of every page with large left-aligned heading.

    title      : the page's heading
    subtitle   : one line describing what the reader will see
    badge_text : optional label above the title (hidden when empty)
    """
    import streamlit as st
    parts = ['<div class="sn-hero">']
    if badge_text:
        parts.append(f'<span class="sn-hero-badge">{esc(badge_text)}</span>')
    parts.append(f'<div class="sn-hero-title">{esc(title)}</div>')
    if subtitle:
        parts.append(f'<div class="sn-hero-sub">{esc(subtitle)}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    """
    Standard page top: the question-style heading banner followed by the
    standard data note.

    Every page starts with this so the header pattern is identical everywhere.
    """
    hero_banner(title, subtitle)
    data_source_note()


def kpi_card(label: str, value, sublabel: str = "", accent: str = None) -> str:
    """Return the HTML for a single KPI card (colored top border, big number)."""
    accent = accent or GREEN
    sub = f'<div class="sn-kpi-sub">{esc(sublabel)}</div>' if sublabel else ""
    return (
        f'<div class="sn-kpi" style="border-top-color:{accent}">'
        f'<div class="sn-kpi-label">{esc(label)}</div>'
        f'<div class="sn-kpi-value">{esc(value)}</div>'
        f"{sub}</div>"
    )


def _as_kpi(item) -> tuple:
    """Normalise a KPI description into ``(label, value, sublabel, accent)``."""
    if isinstance(item, dict):
        return (item.get("label", ""), item.get("value", ""),
                item.get("sublabel", ""), item.get("accent"))
    values = tuple(item)
    values = values + ("",) * (4 - len(values))
    return values[:4]


def kpi_row(cards, per_row: int = 4) -> None:
    """
    Render KPI cards in responsive rows of at most *per_row* cards.

    Each card is a dict (or 4-tuple): ``{label, value, sublabel, accent}``.
    """
    import streamlit as st
    cards = [_as_kpi(c) for c in cards]
    if not cards:
        return
    for start in range(0, len(cards), per_row):
        chunk = cards[start:start + per_row]
        html = ['<div class="sn-kpi-grid">']
        html.extend(kpi_card(*c) for c in chunk)
        html.append("</div>")
        st.markdown("".join(html), unsafe_allow_html=True)


@contextlib.contextmanager
def section_card(title: str, subtitle: str = ""):
    """
    White card with a soft shadow that wraps the content rendered inside it.

    Usage::

        with section_card("Campus at a glance", "Two views of the same data"):
            st.pyplot(fig)
    """
    import streamlit as st
    with st.container(border=True):
        head = [f'<div class="sn-card-title">{esc(title)}</div>']
        if subtitle:
            head.append(f'<div class="sn-card-sub">{esc(subtitle)}</div>')
        st.markdown(f'<div class="sn-card-head">{"".join(head)}</div>',
                    unsafe_allow_html=True)
        yield


def section_title(text: str) -> None:
    """A lightweight section heading (used inside cards and expanders)."""
    import streamlit as st
    st.markdown(f'<div class="sn-section-title">{esc(text)}</div>',
                unsafe_allow_html=True)


def card_grid(items, per_row: int = 3) -> None:
    """Render pre-built HTML cards (see :func:`concept_card`) in a responsive grid."""
    import streamlit as st
    items = list(items)
    if not items:
        return
    for start in range(0, len(items), per_row):
        chunk = items[start:start + per_row]
        st.markdown(
            '<div class="sn-card-grid">' + "".join(chunk) + "</div>",
            unsafe_allow_html=True,
        )


def concept_card(title: str, body: str) -> str:
    """Return the HTML for a small definition card."""
    return (
        f'<div class="sn-concept">'
        f'<div class="sn-concept-title">{esc(title)}</div>'
        f'<div class="sn-concept-body">{esc(body)}</div>'
        f"</div>"
    )


# ===========================================================================
# Pills, callouts, math panels
# ===========================================================================

def pill(text, kind: str = "neutral") -> str:
    """Return the HTML for a status chip (eligible / rejected / skipped / ...)."""
    background, foreground = PILL_COLORS.get((kind or "neutral").lower(),
                                             PILL_COLORS["neutral"])
    return (
        f'<span class="sn-pill" style="background:{background};color:{foreground}">'
        f"{esc(text)}</span>"
    )


def pill_row(items) -> None:
    """Render a row of pills; *items* is a list of ``(text, kind)`` pairs."""
    import streamlit as st
    html = "".join(pill(text, kind) for text, kind in items)
    st.markdown(f'<div class="sn-pill-row">{html}</div>', unsafe_allow_html=True)


def callout(text: str, kind: str = "info") -> None:
    """
    Render a guidance / warning / error message.

    kind : "info" | "success" | "warning" | "error"
        Uses Streamlit's native message boxes so the meaning stays unambiguous
        (and accessible); the stylesheet recolours them to the shared palette.
        Real input errors keep ``"error"``.
    """
    import streamlit as st
    kind = (kind or "info").lower()
    if kind in ("success", "ok"):
        st.success(text)
    elif kind in ("warning", "warn"):
        st.warning(text)
    elif kind in ("error", "danger"):
        st.error(text)
    else:
        st.info(text)


def status_badge(text: str, kind: str = "info") -> None:
    """Backwards-compatible name for :func:`callout`."""
    callout(text, kind)


def empty_buildings_notice() -> None:
    """The standard 'no data loaded' guidance, worded the same on every page."""
    callout(
        "No building data is loaded.\n\n"
        "**What happened:** the buildings table is empty, so no set, ranking or "
        "network can be computed.\n\n"
        "**What to do:** go to **Campus Data** and add at least two "
        "buildings (or press *Reset to defaults* in the sidebar).",
        "info",
    )


def show_visual(html: str, height: int = 420) -> None:
    """
    Render one self-contained interactive visual.

    *html* is the complete HTML document returned by a builder in
    :mod:`components.visuals`; *height* is the initial iframe height in pixels.
    The embedded document resizes its frame to fit the rendered content.
    """
    import streamlit as st
    import streamlit.components.v1 as components
    try:
        components.html(html, height=height, scrolling=False)
    except Exception as exc:                      # pragma: no cover - defensive
        st.error(f"This interactive view could not be drawn: {exc}")


def math_box(latex: str, caption: str = "") -> None:
    """
    Tinted panel containing ``st.latex`` and an optional caption underneath.

    The panel tint is applied through a deterministic container key so several
    math boxes can coexist on one page.
    """
    import streamlit as st
    digest = hashlib.md5(f"{latex}|{caption}".encode("utf-8")).hexdigest()[:10]
    with st.container(border=True, key=f"mb-{digest}"):
        st.latex(latex)
        if caption:
            st.markdown(f'<div class="sn-math-cap">{esc(caption)}</div>',
                        unsafe_allow_html=True)


# ===========================================================================
# Figures — the one place every matplotlib figure is rendered and closed
# ===========================================================================

def show_figure(fig, label: str = "This figure") -> None:
    """
    Render a matplotlib figure with the app's standard settings, then close it.

    Every figure on every page goes through here so the ``st.pyplot`` /
    ``plt.close`` pair can never be forgotten (a forgotten close leaks memory).
    A figure that fails to render shows an error message instead of breaking
    the page. Matplotlib is imported lazily so this module still imports
    outside a Streamlit / matplotlib runtime.
    """
    import matplotlib.pyplot as plt
    import streamlit as st
    try:
        st.pyplot(fig, width="stretch")
    except Exception as exc:                      # pragma: no cover - defensive
        st.error(f"{label} could not be drawn: {exc}")
    finally:
        plt.close(fig)


# ===========================================================================
# Global stylesheet — no external fonts, scripts or animations
# ===========================================================================

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --sn-forest: #14532D;
  --sn-forest-deep: #0F3D21;
  --sn-green: #16A34A;
  --sn-green-dark: #15803D;
  --sn-leaf: #DCFCE7;
  --sn-amber: #F59E0B;
  --sn-amber-deep: #B45309;
  --sn-bg: #F8F9FB;
  --sn-card: #FFFFFF;
  --sn-ink: #111827;
  --sn-muted: #6B7280;
  --sn-border: #E5E7EB;
  --sn-danger: #DC2626;
  --sn-info: #2563EB;
  --sn-sidebar-bg: #0F1C14;
}

/* ── typography & page frame ────────────────────────────────────────────── */
html, body, .stApp, [data-testid="stAppViewContainer"] {
  font-family: "Inter", -apple-system, "Segoe UI", sans-serif;
  color: var(--sn-ink);
}
[data-testid="stAppViewContainer"] { background: var(--sn-bg); }
.block-container {
  padding-top: 0.5rem;
  padding-bottom: 3rem;
  max-width: 1200px;
}
.stApp p, .stApp li { font-size: 0.94rem; line-height: 1.6; }
[data-testid="stCaptionContainer"] p { color: var(--sn-muted); font-size: 0.8rem; text-align: left; }
.katex-display {
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  text-align: left;
}
h1, h2, h3, h4 { color: var(--sn-ink); }
h1 { font-size: 2.4rem; font-weight: 700; letter-spacing: -0.03em; }
h2 { font-size: 1.5rem; font-weight: 600; letter-spacing: -0.02em; }
h3 { font-size: 1.15rem; font-weight: 600; }
hr { margin: 1.5rem 0; border-color: var(--sn-border); }
*, *::before, *::after { box-sizing: border-box; }
img, svg, canvas, iframe { max-width: 100%; }
.stApp { min-width: 0; }

/* ── hide Streamlit chrome ──────────────────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stToolbar"] [data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"] { visibility: visible !important; display: flex !important; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stStatusWidget"] { display: none; }
[data-testid="stAppDeployButton"] { display: none; }
header[data-testid="stHeader"] { background: transparent; }

/* ── sidebar collapse / expand toggle button ───────────────────────────── */
/* The button INSIDE the sidebar (collapse it) */
[data-testid="stSidebarCollapseButton"] {
  visibility: visible !important;
  opacity: 1 !important;
  position: absolute !important;
  top: 0.6rem !important;
  right: 0.6rem !important;
}
[data-testid="stSidebarCollapseButton"] button {
  background: rgba(255,255,255,0.1) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  border-radius: 7px !important;
  width: 28px !important;
  height: 28px !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  cursor: pointer !important;
  opacity: 1 !important;
  visibility: visible !important;
}
[data-testid="stSidebarCollapseButton"] button:hover {
  background: rgba(255,255,255,0.18) !important;
}
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapseButton"] path {
  color: #94A3B8 !important;
  fill: #94A3B8 !important;
  stroke: #94A3B8 !important;
}
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"] {
  color: #94A3B8 !important;
}

/* The button OUTSIDE the sidebar (expand it) */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"] {
  visibility: visible !important;
  opacity: 1 !important;
  display: flex !important;
}
[data-testid="stExpandSidebarButton"] {
  background: #111827 !important;
  border: 1px solid #374151 !important;
  border-radius: 8px !important;
  padding: 0.3rem !important;
}
[data-testid="stExpandSidebarButton"]:hover {
  background: #1F2937 !important;
}
[data-testid="stExpandSidebarButton"] svg,
[data-testid="stExpandSidebarButton"] path {
  color: #9CA3AF !important;
  fill: #9CA3AF !important;
  stroke: #9CA3AF !important;
}
[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {
  color: #9CA3AF !important;
}

/* ── hero banner — large left-aligned heading on light gradient ─────────── */
.sn-hero {
  background: linear-gradient(130deg, #A8D3FF 0%, #D3E3EF 45%, #FFF4DF 100%);
  border-radius: 20px;
  padding: 2.6rem 2.2rem 2.2rem 2.2rem;
  margin-bottom: 1rem;
  margin-top: 1rem;
  color: var(--sn-ink);
  text-align: left;
}
.sn-hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(0,0,0,0.06);
  border: 1px solid rgba(0,0,0,0.1);
  color: #374151;
  font-size: 0.6rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 700;
  padding: 0.25rem 0.8rem;
  border-radius: 999px;
  margin-bottom: 1rem;
  font-family: ui-monospace, "Geist Mono", "SF Mono", Consolas, monospace;
}
.sn-hero-title {
  font-size: 3rem;
  font-weight: 800;
  line-height: 1.08;
  letter-spacing: -0.045em;
  color: #0A1628;
  max-width: 20ch;
  font-family: "Inter", -apple-system, sans-serif;
}
.sn-hero-sub {
  color: #4B5563;
  font-size: 0.95rem;
  margin-top: 0.75rem;
  max-width: 55ch;
  line-height: 1.6;
}

/* ── KPI cards ──────────────────────────────────────────────────────────── */
.sn-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  margin: 1rem 0 1.4rem 0;
  align-items: stretch;
}
.sn-kpi {
  background: var(--sn-card);
  border: 1px solid var(--sn-border);
  border-top: 3px solid var(--sn-green);
  border-radius: 12px;
  padding: 0.9rem 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  transition: box-shadow 0.15s;
  height: 100%;
  min-width: 0;
  text-align: left;
}
.sn-kpi:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.sn-kpi-label { font-size: 0.72rem; color: var(--sn-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }
.sn-kpi-value { font-size: 1.75rem; font-weight: 700; color: var(--sn-forest); line-height: 1.2; margin-top: 0.1rem; }
.sn-kpi-sub { font-size: 0.72rem; color: var(--sn-muted); margin-top: 0.1rem; }

/* ── section cards ──────────────────────────────────────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"] {
  border: 1px solid var(--sn-border) !important;
  border-radius: 16px !important;
  background: var(--sn-card) !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  transition: box-shadow 0.18s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  box-shadow: 0 6px 18px rgba(0,0,0,0.07);
}
.sn-card-head { margin-bottom: 0.35rem; }
.sn-card-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--sn-ink);
  letter-spacing: -0.015em;
}
.sn-card-sub { font-size: 0.83rem; color: var(--sn-muted); margin-top: 0.1rem; }
.sn-section-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--sn-ink);
  letter-spacing: -0.01em;
  margin: 0.4rem 0 0.5rem 0;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid var(--sn-border);
}
.sn-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 0.75rem;
  margin: 0.4rem 0 1.2rem 0;
  align-items: stretch;
}
.sn-concept {
  background: #F9FAFB;
  border: 1px solid var(--sn-border);
  border-radius: 12px;
  padding: 0.85rem 1rem;
  height: 100%;
  text-align: left;
}
.sn-concept-title { font-weight: 700; color: var(--sn-forest); font-size: 0.9rem; letter-spacing: -0.01em; }
.sn-concept-body { color: var(--sn-muted); font-size: 0.84rem; margin-top: 0.25rem; line-height: 1.5; }

/* ── pills ──────────────────────────────────────────────────────────────── */
.sn-pill {
  display: inline-block;
  padding: 0.13rem 0.6rem;
  border-radius: 6px;
  font-size: 0.74rem;
  font-weight: 600;
  margin: 0.1rem 0.2rem 0.1rem 0;
  border: 1px solid transparent;
  white-space: nowrap;
  text-align: left;
}
.sn-pill-row { margin: 0.2rem 0 0.9rem 0; text-align: left; }

/* ── math panels ────────────────────────────────────────────────────────── */
div[class*="st-key-mb-"] {
  background: #F0FDF4 !important;
  border: 1px solid #BBF7D0 !important;
  border-left: 3px solid var(--sn-green) !important;
  border-radius: 10px !important;
  padding: 0.4rem 1rem 1.25rem 1rem !important;
  margin-bottom: 1rem !important;
  box-shadow: none;
  text-align: left !important;
}
.sn-math-cap {
  color: var(--sn-muted);
  font-size: 0.78rem;
  text-align: left;
  margin: 0;
}
div[class*="st-key-mb-"] .katex-display {
  overflow-x: auto;
  overflow-y: hidden;
  max-width: 100%;
  padding-bottom: 0.1rem;
  text-align: left;
}

/* ── message boxes ──────────────────────────────────────────────────────── */
div[data-testid="stAlert"] { border-radius: 10px; }
div[data-testid="stAlertContentInfo"] p { color: #1E3A8A; }
div[data-testid="stAlertContentWarning"] p { color: var(--sn-amber-deep); }

/* ── buttons ────────────────────────────────────────────────────────────── */
button[data-testid="stBaseButton-primary"],
button[data-testid="baseButton-primary"] {
  background: var(--sn-green) !important;
  border: none !important;
  color: #FFFFFF !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  letter-spacing: -0.01em !important;
}
button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="baseButton-primary"]:hover { background: var(--sn-green-dark) !important; }
button[data-testid="stBaseButton-secondary"],
button[data-testid="baseButton-secondary"] {
  border-radius: 8px !important;
  border: 1px solid var(--sn-border) !important;
  color: var(--sn-ink) !important;
  font-weight: 500 !important;
  background: var(--sn-card) !important;
}
button[data-testid="stBaseButton-secondary"]:hover,
button[data-testid="baseButton-secondary"]:hover {
  background: #F3F4F6 !important;
}

/* ── tabs ───────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  gap: 0;
  border-bottom: 1px solid var(--sn-border);
  background: transparent;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border-radius: 0 !important;
  padding: 0.5rem 1rem 0.6rem 1rem !important;
  color: var(--sn-muted);
  font-weight: 500;
  font-size: 0.88rem;
}
.stTabs [aria-selected="true"] {
  color: var(--sn-ink) !important;
  font-weight: 700;
  border-bottom: 2px solid var(--sn-forest);
}
.stTabs [data-baseweb="tab-highlight"] { background-color: transparent !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── tables ─────────────────────────────────────────────────────────────── */
div[data-testid="stDataFrame"],
div[data-testid="stDataFrameResizable"],
div[data-testid="stDataEditor"] {
  border: 1px solid var(--sn-border);
  border-radius: 10px;
  overflow: hidden;
}
div[data-testid="stDataFrame"] * { font-size: 0.84rem; }
div[data-testid="stDataFrame"] [role="gridcell"],
div[data-testid="stDataFrame"] [role="columnheader"],
div[data-testid="stDataEditor"] [role="gridcell"],
div[data-testid="stDataEditor"] [role="columnheader"] {
  justify-content: flex-start !important;
  text-align: left !important;
}

/* ── expanders ──────────────────────────────────────────────────────────── */
div[data-testid="stExpander"] {
  border: 1px solid var(--sn-border) !important;
  border-radius: 10px !important;
  background: var(--sn-card) !important;
  margin-bottom: 0.5rem;
}
div[data-testid="stExpander"] summary { font-weight: 600; color: var(--sn-ink); }
div[data-testid="stExpander"] summary:hover { color: var(--sn-green-dark); }

/* ── inputs ─────────────────────────────────────────────────────────────── */
div[data-baseweb="input"],
div[data-baseweb="select"] > div,
div[data-testid="stNumberInput"] input,
div[data-baseweb="textarea"] { border-radius: 8px !important; }

/* ── sidebar ────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] { background: var(--sn-sidebar-bg) !important; }
section[data-testid="stSidebar"] > div { background: var(--sn-sidebar-bg) !important; }
section[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }
section[data-testid="stSidebar"] { font-family: "Inter", -apple-system, sans-serif !important; }
span[class*="material"],
[data-testid="stIconMaterial"] {
  font-family: "Material Symbols Rounded", "Material Symbols Outlined" !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
  color: #CBD5E1 !important;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  color: #64748B !important;
  font-size: 0.72rem !important;
}

/* sidebar brand */
.sn-brand {
  color: #F8FAFC !important;
  font-size: 0.88rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  line-height: 1.4;
}
.sn-brand-tag {
  color: #475569;
  font-size: 0.65rem;
  margin: 0.08rem 0 0 0;
  line-height: 1.5;
  letter-spacing: 0.01em;
}
.sn-brand-line {
  border: none;
  border-top: 1px solid rgba(255,255,255,0.07);
  margin: 0.65rem 0 0.5rem 0;
}

/* ── hide radio dots entirely ───────────────────────────────────────────── */
section[data-testid="stSidebar"] div[data-baseweb="radio"] { display: none !important; }
section[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child { display: none !important; }
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] { display: none !important; }

/* sidebar nav items */
section[data-testid="stSidebar"] label[data-baseweb="radio"] {
  border-radius: 7px !important;
  padding: 0.38rem 0.75rem !important;
  margin: 1px 0 !important;
  cursor: pointer;
  transition: background 0.1s ease;
  display: flex !important;
  align-items: center !important;
  width: 100% !important;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
  background: rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {
  background: rgba(22,163,74,0.15) !important;
  border-left: 2px solid #22C55E !important;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"] p,
section[data-testid="stSidebar"] label[data-baseweb="radio"] span {
  font-size: 0.82rem !important;
  font-weight: 400 !important;
  color: #94A3B8 !important;
  line-height: 1.4 !important;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover p,
section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover span {
  color: #E2E8F0 !important;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) p,
section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) span {
  color: #FFFFFF !important;
  font-weight: 600 !important;
}

/* group headings bold part */
section[data-testid="stSidebar"] label[data-baseweb="radio"] p strong {
  display: block;
  font-size: 0.58rem !important;
  letter-spacing: 0.11em !important;
  text-transform: uppercase !important;
  color: #334155 !important;
  font-weight: 700 !important;
  margin-bottom: 0.08rem !important;
}
.sn-nav-group {
  color: #334155;
  font-size: 0.58rem;
  letter-spacing: 0.11em;
  text-transform: uppercase;
  font-weight: 700;
  padding: 0.5rem 0.75rem 0.15rem;
}

/* campus card in sidebar */
.sn-campus-card {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 0.75rem 0.85rem;
  margin-top: 0.5rem;
}
.sn-campus-card-title {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #475569 !important;
  margin-bottom: 0.5rem;
}
.sn-campus-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.22rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.sn-campus-row:last-child { border-bottom: none; }
.sn-campus-label { font-size: 0.72rem; color: #64748B; }
.sn-campus-val { font-size: 0.8rem; font-weight: 600; color: #E2E8F0; }
.sn-campus-val.green { color: #22C55E; }
.sn-campus-val.amber { color: #F59E0B; }

/* ── responsive dashboard cards ─────────────────────────────────────────── */
.sn-rollout-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: stretch;
  gap: 0.75rem;
  margin-bottom: 1.2rem;
}
.sn-rollout-card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow-wrap: anywhere;
  text-align: left;
}

/* sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {
  width: 100% !important;
  background: rgba(255,255,255,0.05) !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
  color: #64748B !important;
  border-radius: 7px !important;
  font-size: 0.78rem !important;
  font-weight: 500 !important;
  padding: 0.3rem 0.75rem !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(255,255,255,0.09) !important;
  color: #CBD5E1 !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] {
  background: rgba(255,255,255,0.03) !important;
  border-color: rgba(255,255,255,0.08) !important;
}
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.07) !important; margin: 0.6rem 0 !important; }
section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255,255,255,0.04) !important;
  border-color: rgba(255,255,255,0.08) !important;
  box-shadow: none !important;
}
section[data-testid="stSidebar"] label[data-baseweb="checkbox"] span {
  color: #64748B !important;
  font-size: 0.75rem !important;
}
section[data-testid="stSidebar"] label[data-baseweb="checkbox"] div[data-checked="true"] {
  background: var(--sn-green) !important;
  border-color: var(--sn-green) !important;
}
@media (max-width: 760px) {
  .block-container {
    padding-left: 1rem;
    padding-right: 1rem;
  }
  .sn-hero {
    padding: 1.5rem 1.25rem;
    border-radius: 14px;
  }
  .sn-hero-title { font-size: clamp(1.7rem, 8vw, 2.4rem); }
  .sn-rollout-grid { grid-template-columns: minmax(0, 1fr); }
  .sn-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .stTabs [data-baseweb="tab-list"] {
    flex-wrap: wrap;
    overflow: visible;
  }
  .stTabs [data-baseweb="tab"] {
    flex: 0 1 auto;
    max-width: 100%;
    white-space: normal;
  }
  .stTabs [data-baseweb="tab"] p { white-space: normal; overflow-wrap: anywhere; }
  .katex-display .katex { font-size: 0.9em; }
}
</style>
"""


def inject_css() -> None:
    """
    Inject the global stylesheet + Google Fonts link.

    Called exactly once, from app.py, immediately after st.set_page_config.
    """
    import streamlit as st
    # Inject font link tags FIRST (must be separate from style block to load)
    st.markdown(
        '<link rel="preconnect" href="https://fonts.googleapis.com">' +
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' +
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    st.markdown(_CSS, unsafe_allow_html=True)
