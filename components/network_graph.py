"""
network_graph.py — NetworkX + matplotlib graph visualizer.

Renders the eligible-building graph as a plain node-and-edge diagram.
Returns a matplotlib Figure; the caller is responsible for
st.pyplot(fig) and plt.close(fig). No Streamlit imports in this module.

Only the vertices and edges passed in are drawn — nothing is hardcoded and no
pair of buildings is ever auto-connected. The look comes from the shared
helpers in ``components/charts.py``.
"""

import matplotlib
matplotlib.use("Agg")  # non-interactive backend; safe for Streamlit
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx

from components.charts import (
    apply_chart_style,
    finish_layout,
    graph_canvas,
    graph_font,
    legend_below,
)
from components.style import (
    BORDER,
    CARD,
    INK,
    MUTED,
    NODE_EDGE,
    NODE_FILL,
)

# ── colour / style palette (shared constants, so colours match every page) ────
_NODE_FACE  = NODE_FILL   # leaf-tinted node fill
_NODE_EDGE  = NODE_EDGE   # forest node border
_EDGE_COLOR = MUTED       # neutral edge colour

_NODE_SIZE = 1500
_LABEL_FS  = 9

_EDGE_W = 1.5

_FIGSIZE = (8.4, 5.0)

_CIRCULAR_MAX = 8   # <= this many vertices uses circular_layout


def _key(u, v):
    """Undirected pair key, independent of endpoint order."""
    u, v = str(u), str(v)
    return (u, v) if u <= v else (v, u)


def _unique_names(vertices):
    """Return a de-duplicated list of str names, preserving first-seen order."""
    out = []
    for v in (vertices or []):
        s = str(v)
        if s not in out:
            out.append(s)
    return out


def compute_layout(vertices, edges) -> dict:
    """
    Deterministic node layout for the given graph.

    Uses nx.circular_layout for up to 8 vertices and nx.spring_layout(seed=42)
    for larger graphs, so repeated calls return identical coordinates.

    Returns
    -------
    dict[str, tuple[float, float]]  mapping building name -> (x, y)
    """
    verts = _unique_names(vertices)
    if not verts:
        return {}
    if len(verts) == 1:
        return {verts[0]: (0.0, 0.0)}

    g = nx.Graph()
    g.add_nodes_from(verts)
    for e in (edges or []):
        g.add_edge(str(e[0]), str(e[1]))

    if len(verts) <= _CIRCULAR_MAX:
        pos = nx.circular_layout(g)
    else:
        pos = nx.spring_layout(g, seed=42)

    return {k: (float(p[0]), float(p[1])) for k, p in pos.items()}


def draw_network(vertices, edges, title=None) -> plt.Figure:
    """
    Draw the campus connection graph (plain undirected).

    Parameters
    ----------
    vertices : iterable of str
        Building names to draw (eligible buildings).
    edges : iterable of (u, v) or (u, v, *) pairs — any third field is ignored.
    title : str | None
        Optional figure title.

    Returns
    -------
    matplotlib.figure.Figure  (caller must call plt.close(fig) after use)
    """
    verts = _unique_names(vertices)
    edge_list = [(str(e[0]), str(e[1])) for e in (edges or [])]

    # The canvas grows with the graph and the labels step down one notch per
    # extra vertex, so a 10-building network still keeps every name readable
    # instead of piling them on top of each other.
    n_vertices = len(verts)
    node_fs = graph_font(n_vertices, _LABEL_FS)

    fig, ax = plt.subplots(figsize=graph_canvas(n_vertices, base=_FIGSIZE))
    apply_chart_style(ax, title=title, grid_axis="none", facecolor=CARD)

    # ── empty graph ───────────────────────────────────────────────────────────
    if not verts:
        ax.axis("off")
        ax.text(0.5, 0.5, "No buildings in the network",
                ha="center", va="center", fontsize=12, color=MUTED,
                style="italic", transform=ax.transAxes)
        return finish_layout(fig, pad=1.1)

    pos = compute_layout(verts, edge_list)

    # ── edges ────────────────────────────────────────────────────────────────
    for (u, v) in edge_list:
        if u not in pos or v not in pos:
            continue
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        ax.plot([x1, x2], [y1, y2], color=_EDGE_COLOR, linewidth=_EDGE_W,
                linestyle="-", zorder=2, solid_capstyle="round")

    # ── nodes (leaf fill, forest border) ─────────────────────────────────────
    ax.scatter([pos[v][0] for v in verts], [pos[v][1] for v in verts],
               s=_NODE_SIZE, c=_NODE_FACE, edgecolors=_NODE_EDGE,
               linewidths=1.6, zorder=6)

    # ── node labels: dark ink text on a white pill ───────────────────────────
    for v in verts:
        x, y = pos[v]
        ax.text(x, y, v, ha="center", va="center", fontsize=node_fs,
                color=INK, fontweight="bold", zorder=7,
                bbox=dict(boxstyle="round,pad=0.28", facecolor="white",
                          edgecolor=BORDER, linewidth=0.8, alpha=1.0))

    # ── notes for trivial graphs ─────────────────────────────────────────────
    if len(verts) == 1:
        ax.text(0.5, 0.03, "Single building: no connections needed",
                ha="center", va="bottom", fontsize=9, color=MUTED,
                style="italic", transform=ax.transAxes)
    elif not edge_list:
        ax.text(0.5, 0.03, "No candidate connections defined",
                ha="center", va="bottom", fontsize=9, color=MUTED,
                style="italic", transform=ax.transAxes)

    # ── legend ───────────────────────────────────────────────────────────────
    handles = [
        Line2D([0], [0], color=_EDGE_COLOR, lw=_EDGE_W,
               label="Candidate connection"),
    ]
    ax.axis("off")
    # The nodes fill the whole canvas, so the legend takes a band of its own
    # under the axes: inside the axes it ended up on a node label (it did,
    # for "Guest House"). ``legend_below`` reserves that band *and* lays the
    # axes out, so no ``finish_layout`` afterwards — that would grow the
    # axes back over the legend.
    legend_below(ax, handles, ncol=len(handles))
    return fig
