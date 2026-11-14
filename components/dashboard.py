"""dashboard.py — Sustainable Solar Energy Allocation front page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from algorithms.graph_algorithms import graph_colouring
from algorithms.network import build_network, connected_components
from algorithms.relations import ranking
from algorithms.set_theory import build_sets, eligible_set
from algorithms.stats import campus_stats
from algorithms.validation import (COL_DEMAND, COL_NAME, DEFAULT_THRESHOLDS)
from algorithms.visual_data import campus_map_data
from components.style import (
    AMBER, FOREST, GREEN, INELIGIBLE, INFO,
    callout, data_source_note, empty_buildings_notice, esc,
    hero_banner, kpi_row, page_header,
    pill_row, section_card, show_visual,
)
from components.visuals import campus_map


# ---------------------------------------------------------------------------
# Campus card — SVG building footprint map of the campus buildings
# ---------------------------------------------------------------------------

#  Fixed layout coordinates (x, y, w, h) in a 520×310 viewBox.
#  Arranged to look like a real campus plan — library top-right (large),
#  hostel bottom-left (large), lab + admin top-left cluster, 
#  auditorium center, canteen bottom-center.
_BUILDING_LAYOUT = {
    "Library":        {"x": 320, "y": 20,  "w": 170, "h": 110},
    "Laboratory":     {"x": 20,  "y": 20,  "w": 100, "h": 90},
    "Administration": {"x": 140, "y": 20,  "w": 80,  "h": 65},
    "Auditorium":     {"x": 140, "y": 110, "w": 160, "h": 80},
    "Hostel":         {"x": 20,  "y": 150, "w": 100, "h": 130},
    "Canteen":        {"x": 320, "y": 155, "w": 110, "h": 75},
}


def _build_campus_card(df, thresholds, ready: list) -> str:
    """Return HTML for the campus card — SVG building map + per-building legend."""
    from algorithms.validation import COL_NAME, COL_DEMAND, COL_AREA, COL_SOLAR
    from components.style import esc, FOREST, GREEN, AMBER, INELIGIBLE

    # Collect per-building data
    bdata = {}
    for _, row in df.iterrows():
        name = str(row[COL_NAME])
        bdata[name] = {
            "demand": float(row[COL_DEMAND]),
            "area":   float(row[COL_AREA]),
            "solar":  float(row[COL_SOLAR]),
            "ok":     name in ready,
        }

    # Build SVG
    SVG_W, SVG_H = 520, 310
    rects = []
    labels = []
    for name, pos in _BUILDING_LAYOUT.items():
        info = bdata.get(name, {"ok": False, "solar": 0, "demand": 0, "area": 0})
        ok = info["ok"]
        fill   = "#DCFCE7" if ok else "#F1F5F9"
        stroke = "#16A34A" if ok else "#CBD5E1"
        sw     = 2 if ok else 1

        cx = pos["x"] + pos["w"] / 2
        cy = pos["y"] + pos["h"] / 2

        rects.append(
            f'<rect x="{pos["x"]}" y="{pos["y"]}" width="{pos["w"]}" height="{pos["h"]}" '
            f'rx="6" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>' 
        )
        # building name
        labels.append(
            f'<text x="{cx:.0f}" y="{cy - 7:.0f}" text-anchor="middle" '
            f'font-size="10" font-weight="700" fill="{"#14532D" if ok else "#64748B"}" '
            f'font-family="Inter,-apple-system,sans-serif">{esc(name)}</text>'
        )
        # demand label
        labels.append(
            f'<text x="{cx:.0f}" y="{cy + 8:.0f}" text-anchor="middle" '
            f'font-size="8.5" fill="{"#15803D" if ok else "#94A3B8"}" '
            f'font-family="Inter,-apple-system,sans-serif">{info["demand"]:.0f} kWh/d · {info["area"]:.0f} m²</text>'
        )
        # eligible dot
        dot_col = "#16A34A" if ok else "#CBD5E1"
        labels.append(
            f'<circle cx="{pos["x"] + pos["w"] - 10:.0f}" cy="{pos["y"] + 10:.0f}" '
            f'r="4" fill="{dot_col}"/>' 
        )

    svg = (
        f'<svg viewBox="0 0 {SVG_W} {SVG_H}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;display:block;border-radius:0 0 14px 14px">'
        f'<rect width="{SVG_W}" height="{SVG_H}" fill="#F8FAFC"/>'
        # paths for roads (simple grid lines)
        f'<line x1="130" y1="0" x2="130" y2="{SVG_H}" stroke="#E2E8F0" stroke-width="10"/>'
        f'<line x1="310" y1="0" x2="310" y2="{SVG_H}" stroke="#E2E8F0" stroke-width="10"/>'
        f'<line x1="0" y1="135" x2="{SVG_W}" y2="135" stroke="#E2E8F0" stroke-width="10"/>'
        f'<line x1="0" y1="240" x2="{SVG_W}" y2="240" stroke="#E2E8F0" stroke-width="10"/>'
    )
    svg += "".join(rects) + "".join(labels)
    svg += "</svg>"

    # Legend row
    n_ok = len(ready)
    n_total = len(df)
    legend = (
        '<div style="display:flex;align-items:center;gap:1.2rem;padding:0.65rem 1.1rem;'
        'border-top:1px solid #E5E7EB;font-size:0.78rem;color:#6B7280">' 
        f'<span style="display:flex;align-items:center;gap:0.4rem">'
        f'<span style="width:10px;height:10px;border-radius:50%;background:#16A34A;display:inline-block"></span>'
        f'Solar-ready ({n_ok} of {n_total})</span>'
        f'<span style="display:flex;align-items:center;gap:0.4rem">'
        f'<span style="width:10px;height:10px;border-radius:50%;background:#CBD5E1;display:inline-block"></span>'
        f'Not eligible ({n_total - n_ok})</span>'
        f'<span style="margin-left:auto;font-size:0.72rem">Green dot = eligible</span>'
        '</div>'
    )

    card = (
        '<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:16px;'
        'overflow:hidden;margin-bottom:1.2rem;box-shadow:0 1px 4px rgba(0,0,0,0.05)">' 
        '<div style="padding:0.9rem 1.1rem 0.5rem;font-size:0.95rem;font-weight:700;'
        'color:#111827;border-bottom:1px solid #F1F5F9">Campus card</div>'
        + svg + legend +
        '</div>'
    )
    return card


def render_dashboard() -> None:
    """Render the Sustainable Solar Energy Allocation home page."""
    hero_banner(
        "Sustainable Solar Energy Allocation",
        "Using Set Theory and Graph Optimization — which buildings get solar "
        "panels, in what order, how to connect them, and how to schedule maintenance.",
    )

    df = st.session_state.get("buildings", pd.DataFrame())
    thresholds = st.session_state.get("thresholds", DEFAULT_THRESHOLDS.copy())
    edges = st.session_state.get("edges") or []

    if df is None or df.empty:
        empty_buildings_notice()
        return

    stats = campus_stats(df, thresholds)
    sets = build_sets(df, thresholds)
    ready = sorted(eligible_set(sets["A"], sets["B"], sets["C"]))
    total = stats["total_buildings"]

    # ── headline result ───────────────────────────────────────────────────────
    if ready:
        callout(
            f"**{len(ready)} of {total} buildings are ready for rooftop solar:** "
            f"{', '.join(esc(n) for n in ready)}. Together they use "
            f"{stats['eligible_demand_kwh_day']:,.0f} kWh/day "
            f"({stats['eligible_demand_share_pct']:.0f}% of campus demand) and "
            f"offer {stats['eligible_rooftop_area_m2']:,.0f} m² of roof.",
            "success",
        )
    else:
        callout(
            "**No building is ready yet.** No building passes all three "
            "requirements at once.\n\n**What to do:** open **Sets** and lower a "
            "threshold, or edit a building on **Campus Data**.",
            "warning",
        )

    # ── network and schedule numbers (only for the ready buildings) ──────────
    net = build_network(ready, edges)
    vertices, kept = net["vertices"], net["edges"]
    groups = connected_components(vertices, kept) if vertices else []
    needed = len(vertices) - len(groups)          # connections a connected network needs
    spare = len(kept) - needed
    slots = {}
    n_slots = 0
    if vertices:
        col = graph_colouring(vertices, kept)
        slots = col["exact_colouring"] or col["greedy_colouring"]
        n_slots = col["chromatic_number"]

    kpi_row([
        {"label": "Ready for panels", "value": f"{len(ready)} of {total}",
         "sublabel": "Pass all three requirements", "accent": GREEN},
        {"label": "Demand covered",
         "value": f"{stats['eligible_demand_share_pct']:.0f}%",
         "sublabel": f"{stats['eligible_demand_kwh_day']:,.0f} kWh/day", "accent": AMBER},
        {"label": "Roof available",
         "value": f"{stats['eligible_rooftop_area_m2']:,.0f} m²",
         "sublabel": "On the ready buildings", "accent": INFO},
        {"label": "Usable connections", "value": f"{len(kept)}",
         "sublabel": "Between ready buildings", "accent": FOREST},
        {"label": "Maintenance slots", "value": f"{n_slots}",
         "sublabel": "Neighbours never share one", "accent": INELIGIBLE},
    ], per_row=5)

    # ── Campus card ──────────────────────────────────────────────────────────
    _campus_card_html = _build_campus_card(df, thresholds, ready)
    st.markdown(_campus_card_html, unsafe_allow_html=True)

    if not ready:
        return

    # ── rollout plan: three cards side by side ────────────────────────────────
    import math

    demand = dict(zip(df[COL_NAME].astype(str), df[COL_DEMAND]))
    order = ranking(df, ready)
    top = max((demand.get(n, 0) for n in order), default=1) or 1

    def card(title: str, sub: str, body: str) -> str:
        return (
            f'<div class="sn-rollout-card" style="background:#fff;border:1px solid #dcebe1;'
            f'border-radius:14px;padding:16px 18px;min-height:310px;">'
            f'<div style="font-weight:700;font-size:16px;color:{FOREST};">{title}</div>'
            f'<div style="font-size:12.5px;color:#6b7c72;margin:2px 0 12px;">{sub}</div>'
            f'{body}</div>'
        )

    # 1. installation order: numbered rows with a demand bar
    rows = ""
    for i, name in enumerate(order, start=1):
        d = demand.get(name, 0)
        rows += (
            '<div style="display:flex;align-items:center;gap:10px;padding:9px 0;'
            'border-bottom:1px solid #eef4f0;">'
            f'<span style="width:26px;height:26px;border-radius:50%;background:{GREEN};'
            'color:#fff;font-weight:700;font-size:13px;display:flex;align-items:center;'
            f'justify-content:center;flex-shrink:0;">{i}</span>'
            '<div style="flex:1;min-width:0;">'
            f'<div style="font-weight:600;font-size:14px;">{esc(name)}</div>'
            '<div style="height:6px;background:#e8f0ea;border-radius:3px;margin-top:5px;">'
            f'<div style="height:6px;width:{d / top * 100:.0f}%;background:{AMBER};'
            'border-radius:3px;"></div></div></div>'
            f'<span style="font-size:12.5px;color:#55655b;white-space:nowrap;">'
            f'{d:,.0f} kWh/day</span></div>'
        )
    order_card = card("Installation order",
                      "Biggest demand first, so early panels offset the most.", rows)

    # 2. network: small diagram of ready buildings and usable connections
    n = len(vertices)
    cx, cy, r = 150, 95, 62
    pos = {}
    for k, v in enumerate(vertices):
        ang = -math.pi / 2 + 2 * math.pi * k / max(n, 1)
        pos[v] = (cx + (r * math.cos(ang) if n > 1 else 0),
                  cy + (r * math.sin(ang) if n > 1 else 0))
    svg = '<svg viewBox="0 0 300 195" style="width:100%;height:auto;">'
    for e in kept:
        a, b = e[0], e[1]
        if a in pos and b in pos:
            svg += (f'<line x1="{pos[a][0]:.0f}" y1="{pos[a][1]:.0f}" '
                    f'x2="{pos[b][0]:.0f}" y2="{pos[b][1]:.0f}" '
                    'stroke="#94a3b8" stroke-width="2.5"/>')
    for v, (x, y) in pos.items():
        dx, dy = x - cx, y - cy
        norm = math.hypot(dx, dy) or 1
        lx, ly = x + dx / norm * 24, y + dy / norm * 24 + 4
        if n == 1:
            lx, ly = x, y + 28
        svg += (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="10" fill="{GREEN}"/>'
                f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-size="12" '
                f'font-weight="600" fill="{FOREST}">{esc(v)}</text>')
    svg += "</svg>"

    if n == 1:
        status, colour = "Single building, no links needed", GREEN
    elif not kept:
        status, colour = "No usable links yet. Add some on Campus Data", "#b45309"
    elif len(groups) == 1:
        status = (f"One connected network · {len(kept)} links "
                  f"({needed} needed, {spare} spare)")
        colour = GREEN
    else:
        status = f"{len(groups)} separate groups. Add a link between them"
        colour = "#b45309"
    note = ""
    if net["dropped"]:
        note = (f'<div style="font-size:11.5px;color:#8a978f;margin-top:4px;">'
                f'{len(net["dropped"])} other link(s) skipped: they touch a '
                f'building that is not ready.</div>')
    net_card = card(
        "Connecting the buildings", "Only links between two ready buildings count.",
        f'{svg}<div style="font-weight:600;font-size:13.5px;color:{colour};">'
        f'{esc(status)}</div>{note}',
    )

    # 3. maintenance slots: one row per slot
    chip_colours = [GREEN, AMBER, INFO, FOREST, INELIGIBLE]
    slot_rows = ""
    for s in range(n_slots):
        members = [v for v in vertices if slots.get(v) == s]
        chips = "".join(
            f'<span style="display:inline-block;background:{chip_colours[s % 5]}1f;'
            f'color:#1f2d26;border:1px solid {chip_colours[s % 5]};border-radius:999px;'
            f'padding:3px 11px;font-size:13px;margin:2px 6px 2px 0;">{esc(m)}</span>'
            for m in members
        )
        slot_rows += (
            '<div style="display:flex;align-items:center;gap:12px;padding:9px 0;'
            'border-bottom:1px solid #eef4f0;">'
            f'<span style="font-weight:700;font-size:13px;color:{FOREST};width:52px;">'
            f'Slot {s + 1}</span><div>{chips}</div></div>'
        )
    slot_card = card("Maintenance slots",
                     "Linked buildings are never serviced in the same slot.", slot_rows)

    st.markdown("### Rollout plan")
    st.markdown(
        f'<div class="sn-rollout-grid">{order_card}{net_card}{slot_card}</div>',
        unsafe_allow_html=True,
    )