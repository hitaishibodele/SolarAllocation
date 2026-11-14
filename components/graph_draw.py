"""Drawing helpers for the Graph Theory page."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from components.charts import apply_chart_style, finish_layout, graph_canvas, graph_font, legend_below
from components.network_graph import compute_layout
from components.style import AMBER, BORDER, CARD, INK, MUTED, NODE_EDGE, NODE_FILL

PALETTE = ["#EF4444", "#3B82F6", "#22C55E", "#EAB308", "#A855F7", "#F97316", "#EC4899", "#92400E"]
COLOUR_NAMES = ["red", "blue", "green", "yellow", "purple", "orange", "pink", "brown"]


def two_column_positions(left, right):
    def col(names, x):
        n = len(names)
        return {nm: (x, 0.0 if n == 1 else 1 - 2 * i / (n - 1)) for i, nm in enumerate(names)}
    pos = col(list(left), -1.0)
    pos.update(col(list(right), 1.0))
    return pos


def draw_graph(vertices, edges, colours=None, highlight=None, highlight_label="Highlighted",
               positions=None, directed=False, title=None):
    verts = [str(v) for v in vertices]
    edge_list = [(str(e[0]), str(e[1])) for e in edges]
    hl = highlight or set()
    fig, ax = plt.subplots(figsize=graph_canvas(len(verts), base=(8.4, 5.0)))
    apply_chart_style(ax, title=title, grid_axis="none", facecolor=CARD)
    if not verts:
        ax.axis("off")
        ax.text(0.5, 0.5, "No vertices", ha="center", va="center", fontsize=12,
                color=MUTED, style="italic", transform=ax.transAxes)
        return finish_layout(fig, pad=1.1)
    pos = positions or compute_layout(verts, edge_list)
    fs = graph_font(len(verts), 9)
    for u, v in edge_list:
        if u not in pos or v not in pos:
            continue
        hot = frozenset((u, v)) in hl
        col, lw = (AMBER, 3.6) if hot else (MUTED, 1.5)
        if directed:
            ax.annotate("", xy=pos[v], xytext=pos[u], zorder=2,
                        arrowprops=dict(arrowstyle="-|>", color=col, lw=lw, shrinkA=24, shrinkB=24))
        else:
            ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], color=col,
                    linewidth=lw, zorder=2, solid_capstyle="round")
    faces = [PALETTE[colours[v] % len(PALETTE)] if colours and v in colours else NODE_FILL
             for v in verts]
    ax.scatter([pos[v][0] for v in verts], [pos[v][1] for v in verts], s=1500, c=faces,
               edgecolors=NODE_EDGE, linewidths=1.6, zorder=6)
    for v in verts:
        ax.text(pos[v][0], pos[v][1], v, ha="center", va="center", fontsize=fs, color=INK,
                fontweight="bold", zorder=7,
                bbox=dict(boxstyle="round,pad=0.28", facecolor="white", edgecolor=BORDER, linewidth=0.8))
    ax.axis("off")
    ax.margins(0.2)
    handles = []
    if colours:
        for c in sorted({colours[v] for v in verts if v in colours}):
            handles.append(Line2D([0], [0], marker="o", color="w", markerfacecolor=PALETTE[c % len(PALETTE)],
                                  markeredgecolor=NODE_EDGE, markersize=10,
                                  label=COLOUR_NAMES[c] if c < len(COLOUR_NAMES) else f"colour {c}"))
    if hl:
        handles.append(Line2D([0], [0], color=AMBER, lw=3.6, label=highlight_label))
    if handles:
        legend_below(ax, handles, ncol=min(len(handles), 4))
        return fig
    return finish_layout(fig, pad=1.1)