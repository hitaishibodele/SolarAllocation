"""
charts.py — one shared matplotlib look for every figure in the app.

Every chart (Venn diagram, dashboard bars, graph drawing) is drawn through
top of it) so that colours, fonts, grid, spines and figure sizes stay identical.

Rules applied here:

  * white (or transparent) background, no top/right spines,
  * light horizontal grid behind the data,
  * consistent font sizes and left-aligned titles in the forest green,
  * value labels above bars, axis labels that carry their unit,
  * figures built from the shared palette in ``components/style.py``.

Nothing here computes a value; callers pass the numbers (derived from
``algorithms/``) and the helpers only draw them.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # non-interactive backend; safe for Streamlit
import matplotlib.pyplot as plt

from components.style import (
    AMBER,
    BACKGROUND,
    BORDER,
    CARD,
    DANGER,
    FOREST,
    GREEN,
    INFO,
    INK,
    LEAF,
    MUTED,
    fmt_int,
)

# ── shared typography / geometry ────────────────────────────────────────────
FONT_STACK = ["Inter", "-apple-system", "Segoe UI", "DejaVu Sans", "sans-serif"]
BASE_FONT_SIZE = 9.0
TITLE_FONT_SIZE = 11.5
LABEL_FONT_SIZE = 9.0
TICK_FONT_SIZE = 8.5
VALUE_FONT_SIZE = 8.5
LEGEND_FONT_SIZE = 8.5

# Standard figure sizes, so every chart on a page has the same footprint.
FIG_WIDE = (8.4, 4.3)     # full-width chart
FIG_HALF = (6.6, 4.1)     # chart inside a column
FIG_TALL = (8.0, 6.8)     # Venn diagram

_BAR_LINE = 0.8


def setup_matplotlib() -> None:
    """Install the shared matplotlib defaults (called once from app.py)."""
    plt.rcParams.update({
        "figure.facecolor": CARD,
        "savefig.facecolor": CARD,
        "axes.facecolor": CARD,
        "axes.edgecolor": BORDER,
        "axes.labelcolor": MUTED,
        "axes.titlecolor": FOREST,
        "axes.titlesize": TITLE_FONT_SIZE,
        "axes.titleweight": "bold",
        "axes.labelsize": LABEL_FONT_SIZE,
        "xtick.labelsize": TICK_FONT_SIZE,
        "ytick.labelsize": TICK_FONT_SIZE,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "text.color": INK,
        "legend.fontsize": LEGEND_FONT_SIZE,
        "legend.framealpha": 0.95,
        "legend.edgecolor": BORDER,
        "legend.facecolor": CARD,
        "font.size": BASE_FONT_SIZE,
        "font.family": "sans-serif",
        "font.sans-serif": FONT_STACK,
        "axes.grid": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def apply_chart_style(ax, title: str = None, xlabel: str = None, ylabel: str = None,
                      *, grid_axis: str = "y", facecolor: str = CARD,
                      transparent: bool = False, title_loc: str = "left"):
    """
    Apply the shared chart style to a single Axes and return it.

    title/xlabel/ylabel : set (and styled) when not ``None``
    grid_axis           : "y" (default), "x", "both" or "none"
    facecolor           : axes/figure background ("white" by default)
    transparent         : draw on a transparent canvas instead
    title_loc           : left-aligned titles, as on every page of the app
    """
    fig = ax.figure
    if transparent:
        fig.patch.set_alpha(0.0)
        ax.set_facecolor("none")
    else:
        fig.patch.set_facecolor(facecolor)
        ax.set_facecolor(facecolor)

    if title is not None:
        ax.set_title(title, loc=title_loc, fontsize=TITLE_FONT_SIZE,
                     fontweight="bold", color=FOREST, pad=10)
    if xlabel is not None:
        ax.set_xlabel(xlabel, fontsize=LABEL_FONT_SIZE, color=MUTED, labelpad=6)
    if ylabel is not None:
        ax.set_ylabel(ylabel, fontsize=LABEL_FONT_SIZE, color=MUTED, labelpad=6)

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        if side in ax.spines:
            ax.spines[side].set_color(BORDER)
            ax.spines[side].set_linewidth(0.9)

    axis = (grid_axis or "none").lower()
    ax.grid(False)
    if axis in ("y", "both"):
        ax.grid(axis="y", color=BORDER, linewidth=0.7, alpha=0.95)
    if axis in ("x", "both"):
        ax.grid(axis="x", color=BORDER, linewidth=0.7, alpha=0.95)
    ax.set_axisbelow(True)

    ax.tick_params(labelsize=TICK_FONT_SIZE, colors=MUTED, length=0)
    return ax


def finish_layout(fig, **kwargs):
    """
    Run ``tight_layout`` on *fig* when every Axes supports it, and return *fig*.

    Figures that place an Axes by hand (``fig.add_axes``) have no subplotspec,
    so matplotlib cannot lay them out and warns "This figure includes Axes that
    are not compatible with tight_layout, so results might be incorrect.".
    Those figures carry their own explicit geometry, so the call is skipped for
    them — no warning, and nothing about what is plotted changes.
    """
    if fig.axes and all(ax.get_subplotspec() is not None for ax in fig.axes):
        fig.tight_layout(**kwargs)
    return fig


def tilt_xlabels(ax, rotation: float = 30, fontsize: float = None) -> None:
    """
    Rotate the x tick labels so long category names (building names, edge names)
    cannot run into their neighbour. Labels are right-aligned against their tick
    below 90°, and hang straight down at 90°.

    ``rotation_mode`` stays at matplotlib's default: with ``"anchor"`` the
    rotated label is measured without the room it really needs, so
    ``tight_layout`` sizes the axes as if the labels were tiny and they end up
    drawn *inside* the plotting area, over the bars.
    """
    ax.tick_params(axis="x", rotation=rotation, labelsize=fontsize)
    horizontal = "right" if rotation < 90 else "center"
    for label in ax.get_xticklabels():
        label.set_horizontalalignment(horizontal)
        label.set_rotation_mode("default")


def tilt_xlabels_for(ax, categories, *, fontsize: float = None,
                     wide_limit: int = 6, name_limit: int = 9) -> float:
    """
    Rotate the x tick labels by an angle read off the category names: a gentle
    30° when there are only a few short names, straight down (90°) as soon as
    there are many of them or one is long. Longer names need the vertical form
    or they run into their neighbour. Returns the angle used.
    """
    names = [str(c) for c in categories]
    crowded = len(names) > wide_limit or max(map(len, names), default=0) > name_limit
    rotation = 90 if crowded else 30
    tilt_xlabels(ax, rotation, fontsize=fontsize)
    return rotation


def headroom(ax, factor: float = 1.24, floor: float = 0.0) -> None:
    """
    Grow the y limit so the value label above the tallest bar stays inside the
    axes (and clear of the title). The new limit is derived from the data
    already plotted, so nothing is hardcoded.
    """
    lo, hi = ax.get_ylim()
    ax.set_ylim(lo, max(hi * factor, floor))


# A graph figure is laid out for the circular layout's vertex count. Past that
# the spring layout spreads more nodes over the same area, and the node/edge
# labels — sized in points, so they do not grow with the canvas — would start
# to touch: the canvas grows with the graph and their font steps down one step
# for every extra vertex, so every label keeps its own room.
GRAPH_BASE_VERTICES = 8
GRAPH_CANVAS_GROWTH = (0.45, 0.38)
GRAPH_FONT_STEP = 0.45


def graph_canvas(n_vertices: int, base=(8.4, 5.0)) -> tuple:
    """Figure size (inches) whose canvas grows with the number of vertices."""
    extra = max(0, int(n_vertices) - GRAPH_BASE_VERTICES)
    return (base[0] + GRAPH_CANVAS_GROWTH[0] * extra,
            base[1] + GRAPH_CANVAS_GROWTH[1] * extra)


def graph_font(n_vertices: int, base: float, floor: float = 6.0) -> float:
    """Label font size that steps down as the graph fills up, never past *floor*."""
    extra = max(0, int(n_vertices) - GRAPH_BASE_VERTICES)
    return max(floor, base - GRAPH_FONT_STEP * extra)


def legend_above(ax, handles=None, *, ncol: int = 3, **kwargs):
    """
    Draw the shared legend in one row just above the axes, right-aligned.

    The chart title is left-aligned, so a legend in the top-right band cannot
    collide with it, with the bars, or with their value labels. A legend is
    part of the Axes' tight bbox, so ``finish_layout`` reserves that band.
    """
    return style_legend(ax, loc="lower right", ncol=ncol,
                        bbox_to_anchor=(1.0, 1.0), borderaxespad=0.0,
                        handles=handles, **kwargs)


def legend_below(ax, handles=None, *, ncol: int = 3, gap: float = 0.015,
                 pad: float = 0.02, **kwargs):
    """
    Draw the shared legend in its own band *under* the axes, for figures whose
    plotting area is fully occupied by nodes (graphs) or points (scatters).

    The band is reserved, not guessed: ``tight_layout`` sizes the axes for
    their tick labels and axis label but knows nothing about a legend anchored
    outside the axes, so the legend is measured first and the axes are then
    laid out inside the rectangle left above it. Re-running a plain
    ``tight_layout`` after this call would grow the axes back over the legend.

    Returns the created legend.
    """
    fig = ax.figure
    legend = ax.legend(loc="lower center", ncol=ncol, fontsize=LEGEND_FONT_SIZE,
                       frameon=True, framealpha=0.95, facecolor=CARD,
                       edgecolor=BORDER, borderaxespad=0.0, handles=handles,
                       bbox_to_anchor=(0.5, 0.0), bbox_transform=fig.transFigure,
                       **kwargs)

    fig.canvas.draw()
    height = legend.get_window_extent(fig.canvas.get_renderer()).height
    band = height / fig.bbox.height + gap + pad
    if fig.axes and all(a.get_subplotspec() is not None for a in fig.axes):
        fig.tight_layout(rect=(0.0, band, 1.0, 1.0))
    legend.set_bbox_to_anchor((0.5, pad), transform=fig.transFigure)
    return legend


def add_bar_values(ax, bars, value_fmt=fmt_int, *, fontsize: float = VALUE_FONT_SIZE,
                   color: str = MUTED, **kwargs) -> None:
    """Write a formatted value label above each bar in *bars*."""
    for bar in bars:
        height = bar.get_height()
        if height is None:
            continue
        ax.text(bar.get_x() + bar.get_width() / 2.0, height,
                value_fmt(height), ha="center", va="bottom",
                fontsize=fontsize, color=color, zorder=5, **kwargs)


def add_note(ax, text: str, **kwargs) -> None:
    """Place a small note in the upper-left corner of the axes."""
    ax.text(0.01, 1.02, text, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=VALUE_FONT_SIZE, color=MUTED, **kwargs)


def style_legend(ax, *, loc: str = "upper right", ncol: int = 1, **kwargs):
    """Draw the shared legend style on *ax*."""
    legend = ax.legend(loc=loc, ncol=ncol, fontsize=LEGEND_FONT_SIZE,
                       frameon=True, framealpha=0.95, facecolor=CARD,
                       edgecolor=BORDER, **kwargs)
    return legend


def bar_chart(labels, values, *, colors=None, title: str = "", xlabel: str = "",
              ylabel: str = "", value_fmt=fmt_int, figsize=None,
              grid_axis: str = "y", rotation: int = 0, horizontal: bool = False):
    """
    Draw a simple bar chart with the shared style and value labels.

    Returns ``(fig, ax)``; the caller is responsible for ``plt.close(fig)``.
    """
    fig, ax = plt.subplots(figsize=figsize or FIG_WIDE)
    values = list(values)
    colors = list(colors) if colors is not None else [GREEN] * len(values)

    if horizontal:
        bars = ax.barh(list(labels), values, color=colors,
                       edgecolor=CARD, linewidth=_BAR_LINE, zorder=3)
        apply_chart_style(ax, title=title, xlabel=xlabel or ylabel,
                          ylabel=ylabel, grid_axis="x", facecolor=CARD)
        for bar, value in zip(bars, values):
            ax.text(value, bar.get_y() + bar.get_height() / 2.0,
                    f" {value_fmt(value)}", ha="left", va="center",
                    fontsize=VALUE_FONT_SIZE, color=MUTED, zorder=5)
    else:
        bars = ax.bar(list(labels), values, color=colors,
                      edgecolor=CARD, linewidth=_BAR_LINE, zorder=3)
        apply_chart_style(ax, title=title, xlabel=xlabel, ylabel=ylabel,
                          grid_axis=grid_axis, facecolor=CARD)
        add_bar_values(ax, bars, value_fmt)

    if rotation:
        ax.tick_params(axis="x", rotation=rotation)
        for label in ax.get_xticklabels():
            label.set_horizontalalignment("right")
    finish_layout(fig, pad=1.1)
    return fig, ax
