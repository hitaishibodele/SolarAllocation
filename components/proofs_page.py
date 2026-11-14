"""
proofs_page.py — "How do we know the eligibility rule is right?"

Five proofs about the campus rule, each revealed a step at a time with a live
check on the current data, followed by the two induction pictures and the
loop invariant of the routine that builds the eligible list.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from algorithms.proofs import PROOF_ORDER
from algorithms.validation import DEFAULT_THRESHOLDS
from algorithms.visual_data import (
    all_proofs_data,
    conveyor_data,
    induction_data,
    strong_induction_data,
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
    section_card,
    section_title,
    show_visual,
)
from components.visuals import (
    induction_dominoes,
    loop_invariant_conveyor,
    proof_stepper,
    strong_induction_tiles,
)


def _induction_controls(n_buildings: int) -> tuple:
    with st.expander("Try different numbers — choose how many buildings",
                     expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            small_n = st.number_input(
                "Buildings in the row of dominoes",
                min_value=1, max_value=24,
                value=max(1, min(24, n_buildings)), step=1, key="prf_domino_n",
            )
        with c2:
            strong_n = st.number_input(
                "Buildings to group for strong induction",
                min_value=2, max_value=24,
                value=max(2, min(24, n_buildings)), step=1, key="prf_tile_n",
            )
    return int(small_n), int(strong_n)


def render_proofs_page() -> None:
    """Render the Proofs page."""
    page_header(
        "How do we know the eligibility rule is right?",
        "A rule that decides which buildings get panels has to be argued, not "
        "assumed. Each argument below is shown one step at a time and checked "
        "against the buildings loaded right now.",
    )

    df = st.session_state.get("buildings", pd.DataFrame())
    thresholds = st.session_state.get("thresholds", DEFAULT_THRESHOLDS.copy())

    if df is None or df.empty:
        empty_buildings_notice()
        return

    proofs = all_proofs_data(df, thresholds)
    passing = sum(1 for proof in proofs.values() if proof["check"]["passed"])

    kpi_row([
        {"label": "Arguments", "value": str(len(PROOF_ORDER)),
         "sublabel": "direct, contraposition, contradiction, counterexample, correctness",
         "accent": FOREST},
        {"label": "Checks standing", "value": f"{passing} of {len(PROOF_ORDER)}",
         "sublabel": "recomputed from the current buildings", "accent": GREEN},
        {"label": "Buildings examined", "value": str(len(df)),
         "sublabel": "every argument looks at all of them", "accent": AMBER},
        {"label": "Loop steps", "value": str(len(df)),
         "sublabel": "one per building in the invariant trace",
         "accent": INELIGIBLE},
    ], per_row=4)

    # ── 1. Proof stepper ───────────────────────────────────────────────────
    key = st.selectbox(
        "Which argument would you like to see?",
        options=list(PROOF_ORDER),
        format_func=lambda k: proofs[k]["title"],
        key="prf_key",
    )

    with section_card(
        "The argument, one step at a time",
        "Press Next step to reveal each piece of reasoning. Every step carries a "
        "label and the live check is recomputed from the current buildings.",
    ):
        show_visual(proof_stepper(proofs[key]), height=440)

    # ── 2. Induction ─────────────────────────────────────────────────────────
    small_n, strong_n = _induction_controls(len(df))

    with section_card(
        "Induction — the dominoes",
        "Claim: n buildings need at least n − 1 connections for full connectivity. "
        "The base case tips the first domino; the inductive step links each one to the next.",
    ):
        show_visual(induction_dominoes(induction_data(small_n)), height=320)

    with section_card(
        "Strong induction — grouping buildings",
        "The same claim proved by peeling off groups of two and three buildings.",
    ):
        show_visual(strong_induction_tiles(strong_induction_data(strong_n)), height=320)

    # ── 3. Loop invariant ─────────────────────────────────────────────────────
    trace = conveyor_data(df, thresholds)
    with section_card(
        "Program correctness — building the eligible list",
        "One building is examined per iteration. After each step the tray must hold "
        "exactly the qualifying buildings seen so far.",
    ):
        show_visual(loop_invariant_conveyor(trace), height=360)

    # ── 4. How it works ──────────────────────────────────────────────────────
    section_title("How it works")

    math_box(
        r"E = A \cap B \cap C \quad\Longrightarrow\quad E \subseteq A",
        "The statement the direct proof establishes.",
    )

    card_grid([
        concept_card("Direct", "Assume a building is eligible; apply the definition to reach the conclusion."),
        concept_card("Contraposition", "Prove ¬a → ¬b, which is logically equivalent to b → a."),
        concept_card("Contradiction", "Assume the negation, derive an impossibility."),
        concept_card("Counterexample", "One building that is high-demand but not eligible refutes the converse."),
        concept_card("Induction", "Base case + inductive step → the claim holds for every campus size."),
        concept_card("Program correctness", "An invariant true before, during and after the loop proves the routine correct."),
    ], per_row=3)

    check = proofs[key]["check"]
    callout(
        f"Live check for “{esc(proofs[key]['title'])}”: "
        f"{'passes' if check['passed'] else 'fails'}. {check['message']}",
        "success" if check["passed"] else "warning",
    )

    # ── 5. Data tables ───────────────────────────────────────────────────────────
    tab_all, tab_trace = st.tabs(["All arguments", "Invariant trace"])

    with tab_all:
        st.dataframe(
            pd.DataFrame([
                {"argument": proofs[k]["title"],
                 "claim": proofs[k]["claim"],
                 "steps": len(proofs[k]["steps"]),
                 "check": "passes" if proofs[k]["check"]["passed"] else "fails"}
                for k in PROOF_ORDER
            ]),
            width="stretch",
            hide_index=True,
        )

    with tab_trace:
        st.dataframe(
            pd.DataFrame([
                {"iteration": step["index"], "building": step["label"],
                 "answer": "kept" if step["accepted"] else "skipped",
                 "tray": ", ".join(m["label"] for m in step["tray"]) or "empty",
                 "invariant": "holds" if step["invariant_holds"] else "broken"}
                for step in trace["steps"]
            ]),
            width="stretch",
            hide_index=True,
        )
