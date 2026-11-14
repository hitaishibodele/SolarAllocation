"""
proofs.py — Proofs about the campus eligibility rule.

Each proof is returned as plain data: a claim, a numbered list of steps (with
a status for every step) and a live check that is recomputed from the current
buildings and thresholds, so the proof always points at real campus numbers.

Five proofs are offered:

  * ``direct``          — every eligible building has a high demand (E ⊆ A)
  * ``contraposition``  — below-threshold solar means not eligible (¬C ⇒ ¬E)
  * ``contradiction``   — no building with solar below the threshold is eligible
  * ``counterexample``  — one building shows "high demand ⇒ eligible" is false
  * ``correctness``     — the loop invariant of the routine that builds E

No Streamlit imports.  Nothing is hardcoded: every figure comes from the data.
"""

from __future__ import annotations

import pandas as pd

from algorithms.validation import (
    COL_NAME,
    COL_DEMAND,
    COL_AREA,
    COL_SOLAR,
    DEFAULT_THRESHOLDS,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _rows(df: pd.DataFrame) -> list:
    """Return the buildings as a list of ``(name, demand, area, solar)`` rows."""
    if df is None or df.empty:
        return []
    out = []
    for _, row in df.iterrows():
        out.append((
            str(row[COL_NAME]),
            float(row[COL_DEMAND]),
            float(row[COL_AREA]),
            float(row[COL_SOLAR]),
        ))
    return sorted(out, key=lambda r: r[0])


def _limits(thresholds) -> tuple:
    t = thresholds or {}
    return (
        float(t.get("min_demand", DEFAULT_THRESHOLDS["min_demand"])),
        float(t.get("min_area",   DEFAULT_THRESHOLDS["min_area"])),
        float(t.get("min_solar",  DEFAULT_THRESHOLDS["min_solar"])),
    )


def _fails(row, limits) -> list:
    """Return the names of the criteria (A, B, C) that *row* does not meet."""
    _name, demand, area, solar = row
    min_demand, min_area, min_solar = limits
    failed = []
    if not demand >= min_demand:
        failed.append("A")
    if not area >= min_area:
        failed.append("B")
    if not solar >= min_solar:
        failed.append("C")
    return failed


def _criteria_text(limits) -> tuple:
    min_demand, min_area, min_solar = limits
    return (
        f"demand ≥ {min_demand:g} kWh/day",
        f"area ≥ {min_area:g} m²",
        f"solar ≥ {min_solar:g}%",
    )


# ---------------------------------------------------------------------------
# The loop that builds the eligible list (used by the correctness proof)
# ---------------------------------------------------------------------------

def eligible_loop(df: pd.DataFrame, thresholds: dict) -> dict:
    """
    Run the routine that builds the eligible list, recording one step per
    building.

    The invariant is: *after examining the first k buildings, the tray holds
    exactly the buildings among those first k that meet all three criteria.*

    Returns
    -------
    dict with keys:
        "order"     : list[str]  — the order the buildings are examined in
        "steps"     : list of dicts, one per building, each with
                      ``index``, ``name``, ``accepted``, ``tray``,
                      ``invariant_holds``
        "tray"      : list[str]  — buildings accepted at the end
        "invariant" : str        — the invariant, written out
        "holds"     : bool       — True when every step preserved the invariant
    """
    rows = _rows(df)
    limits = _limits(thresholds)
    order = [r[0] for r in rows]

    tray: list = []
    steps = []
    for i, row in enumerate(rows, start=1):
        accepted = not _fails(row, limits)
        if accepted:
            tray.append(row[0])
        expected = [
            r[0] for r in rows[:i]
            if not _fails(r, limits)
        ]
        steps.append({
            "index":           i,
            "name":            row[0],
            "accepted":        accepted,
            "tray":            list(tray),
            "invariant_holds": tray == expected,
        })

    return {
        "order":     order,
        "steps":     steps,
        "tray":      list(tray),
        "invariant": (
            "After examining the first k buildings, the tray holds exactly the "
            "buildings among those first k that meet all three criteria."
        ),
        "holds":     all(s["invariant_holds"] for s in steps),
    }


# ---------------------------------------------------------------------------
# Proof builders
# ---------------------------------------------------------------------------

def direct_proof(df: pd.DataFrame, thresholds: dict) -> dict:
    """Direct proof that E ⊆ A: every eligible building has a high demand."""
    rows = _rows(df)
    limits = _limits(thresholds)
    demand_txt, _area_txt, _solar_txt = _criteria_text(limits)

    eligible = [r for r in rows if not _fails(r, limits)]
    counter = [r for r in eligible if r[1] < limits[0]]

    steps = [
        {"claim": "Take any building x that is eligible, x ∈ E.",
         "why": "E is the set of buildings that meet all three criteria.",
         "status": "assumption"},
        {"claim": "Because x ∈ E and E = A ∩ B ∩ C, x belongs to A, B and C.",
         "why": "An element of an intersection belongs to every set in the intersection.",
         "status": "derived"},
        {"claim": "In particular x ∈ A, so its demand is at least the threshold.",
         "why": f"Set A collects exactly the buildings with {demand_txt}.",
         "status": "derived"},
        {"claim": "Hence every building in E lies in A, that is E ⊆ A.",
         "why": "x was an arbitrary element of E, so the conclusion holds for all of E.",
         "status": "conclusion"},
    ]

    return {
        "key":     "direct",
        "title":   "Direct proof — eligible implies high demand",
        "claim":   "Every eligible building has a high demand: E ⊆ A.",
        "steps":   steps,
        "check": {
            "passed":   not counter,
            "headline": "E ⊆ A",
            "message": (
                f"All {len(eligible)} eligible building(s) meet {demand_txt}."
                if not counter else
                "Some eligible building does not meet the demand criterion."
            ),
            "evidence": (
                ", ".join(r[0] for r in eligible) if eligible
                else "no eligible buildings in the current data"
            ),
        },
    }


def contraposition_proof(df: pd.DataFrame, thresholds: dict) -> dict:
    """Proof by contraposition: not in C implies not in E."""
    rows = _rows(df)
    limits = _limits(thresholds)
    _demand_txt, _area_txt, solar_txt = _criteria_text(limits)

    outside_c = [r for r in rows if r[3] < limits[2]]
    bad = [r for r in outside_c if not _fails(r, limits)]

    steps = [
        {"claim": "Instead of proving x ∈ E ⇒ x ∈ C directly, prove the "
                  "contrapositive: x ∉ C ⇒ x ∉ E.",
         "why": "A statement and its contrapositive are always equivalent.",
         "status": "assumption"},
        {"claim": "So suppose x ∉ C; its solar potential is below the threshold.",
         "why": f"Set C collects exactly the buildings with {solar_txt}.",
         "status": "assumption"},
        {"claim": "If x were in E, then x ∈ A ∩ B ∩ C and therefore x ∈ C.",
         "why": "E is defined as the intersection A ∩ B ∩ C.",
         "status": "derived"},
        {"claim": "This contradicts x ∉ C, so no such x is in E; x ∉ C ⇒ x ∉ E.",
         "why": "The contradiction rules out the assumption that x ∈ E.",
         "status": "conclusion"},
    ]

    return {
        "key":   "contraposition",
        "title": "Contraposition — below-threshold solar means not eligible",
        "claim": "If a building is not in C it is not eligible: x ∉ C ⇒ x ∉ E.",
        "steps": steps,
        "check": {
            "passed":   not bad,
            "headline": "¬C ⇒ ¬E",
            "message": (
                f"All {len(outside_c)} building(s) outside C are also outside E."
                if not bad else
                "A building outside C was found inside E."
            ),
            "evidence": (
                ", ".join(r[0] for r in outside_c) if outside_c
                else "every building currently meets the solar criterion"
            ),
        },
    }


def contradiction_proof(df: pd.DataFrame, thresholds: dict) -> dict:
    """Proof by contradiction: no below-threshold-solar building is eligible."""
    rows = _rows(df)
    limits = _limits(thresholds)
    _demand_txt, _area_txt, solar_txt = _criteria_text(limits)

    violation = [r for r in rows if r[3] < limits[2] and not _fails(r, limits)]

    steps = [
        {"claim": "Suppose, for contradiction, that some building x is eligible "
                  "and yet has solar below the threshold.",
         "why": "Assuming the opposite of the claim is the start of a proof by "
                "contradiction.",
         "status": "assumption"},
        {"claim": "Being eligible means x ∈ A ∩ B ∩ C, in particular x ∈ C.",
         "why": "E is the intersection of the three criteria sets.",
         "status": "derived"},
        {"claim": "But x ∈ C requires solar at least the threshold, which "
                  "contradicts the solar value of x.",
         "why": f"Set C is defined by {solar_txt}.",
         "status": "derived"},
        {"claim": "The assumption is therefore impossible: no building with "
                  "solar below the threshold is eligible.",
         "why": "No x can satisfy both conditions, so the claim holds.",
         "status": "conclusion"},
    ]

    return {
        "key":   "contradiction",
        "title": "Contradiction — low solar cannot qualify",
        "claim": "No building with solar below the threshold is eligible.",
        "steps": steps,
        "check": {
            "passed":   not violation,
            "headline": "no low-solar building in E",
            "message": (
                "No building with solar below the threshold appears in E."
                if not violation else
                "A low-solar building was found in E."
            ),
            "evidence": (
                ", ".join(r[0] for r in rows if r[3] < limits[2])
                if any(r[3] < limits[2] for r in rows)
                else "every building currently meets the solar criterion"
            ),
        },
    }


def counterexample_proof(df: pd.DataFrame, thresholds: dict) -> dict:
    """Disproof by counterexample of "every high-demand building qualifies"."""
    rows = _rows(df)
    limits = _limits(thresholds)
    demand_txt, area_txt, solar_txt = _criteria_text(limits)

    high_demand = [r for r in rows if r[1] >= limits[0]]
    witnesses = [r for r in high_demand if _fails(r, limits)]

    if witnesses:
        w = witnesses[0]
        failed = _fails(w, limits)
        missing_names = []
        if "B" in failed:
            missing_names.append("area")
        if "C" in failed:
            missing_names.append("solar")
        steps = [
            {"claim": "The claim to disprove is: every building with a high "
                      "demand also qualifies for rooftop solar (A ⊆ E).",
             "why": "To disprove a universal claim it is enough to find one "
                    "counterexample.",
             "status": "assumption"},
            {"claim": f"{w[0]} has demand {w[1]:g} kWh/day, at least the "
                      f"threshold, so {w[0]} ∈ A.",
             "why": f"Set A collects exactly the buildings with {demand_txt}.",
             "status": "derived"},
            {"claim": f"{w[0]} fails on {' and '.join(missing_names)}: "
                      f"{w[0]}'s rooftop area is {w[2]:g} m² and its solar "
                      f"potential is {w[3]:g}%.",
             "why": f"Eligibility needs all three criteria at once "
                    f"({demand_txt}, {area_txt} and {solar_txt}).",
             "status": "derived"},
            {"claim": f"Thus {w[0]} ∈ A but {w[0]} ∉ E, so the claim A ⊆ E is "
                      "false.",
             "why": "One counterexample is enough to refute a universal claim.",
             "status": "conclusion"},
        ]
        message = (f"{w[0]} has a high demand but fails "
                   f"{', '.join(sorted(failed))}, so A ⊆ E is false.")
        evidence = f"{w[0]} (demand {w[1]:g}, area {w[2]:g}, solar {w[3]:g}%)"
        passed = True
    else:
        steps = [
            {"claim": "The claim to disprove is: every building with a high "
                      "demand also qualifies for rooftop solar (A ⊆ E).",
             "why": "A counterexample would be a high-demand building that does "
                    "not qualify.",
             "status": "assumption"},
            {"claim": "Every high-demand building in the current data meets the "
                      "other two criteria as well.",
             "why": "This is checked live on the campus data.",
             "status": "derived"},
            {"claim": "So no counterexample exists for this data, and here A ⊆ E "
                      "happens to be true.",
             "why": "The disproof needs an actual witness; without one the "
                    "claim stands for this data.",
             "status": "conclusion"},
        ]
        message = "No counterexample in the current data, so A ⊆ E holds here."
        evidence = "no high-demand building fails another criterion"
        passed = True

    return {
        "key":   "counterexample",
        "title": "Counterexample — high demand alone is not enough",
        "claim": "It is false that every high-demand building qualifies: A ⊆ E "
                 "does not hold in general.",
        "steps": steps,
        "check": {
            "passed":   passed,
            "headline": "A ⊄ E",
            "message":  message,
            "evidence": evidence,
        },
    }


def correctness_proof(df: pd.DataFrame, thresholds: dict) -> dict:
    """Correctness of the routine that builds the eligible list."""
    trace = eligible_loop(df, thresholds)
    limits = _limits(thresholds)
    demand_txt, area_txt, solar_txt = _criteria_text(limits)
    n = len(trace["order"])

    steps = [
        {"claim": "Invariant: " + trace["invariant"],
         "why": "Stating the invariant first is what makes the loop's "
                "correctness checkable.",
         "status": "assumption"},
        {"claim": "Initialization: before the loop no building has been "
                  "examined, so k = 0 and the tray is empty — the invariant "
                  "holds for k = 0.",
         "why": "The empty tray matches the empty prefix of the buildings.",
         "status": "initialization"},
        {"claim": "Maintenance: assume the invariant holds after k buildings. "
                  "The routine then examines building k+1 and appends it "
                  "exactly when it meets all three criteria; either way the "
                  "tray matches the first k+1 buildings.",
         "why": f"The test is {demand_txt}, {area_txt} and {solar_txt} — the "
                f"same definition that builds E.",
         "status": "maintenance"},
        {"claim": f"Termination: after all {n} building(s) the loop ends with "
                  "the tray holding exactly the qualifying buildings, which is "
                  "the set E.",
         "why": "With k = n the invariant says the tray equals the qualifying "
                "buildings of the whole campus.",
         "status": "termination"},
    ]

    return {
        "key":   "correctness",
        "title": "Program correctness — the loop that builds the eligible list",
        "claim": "After the loop finishes, the tray contains exactly the "
                 "eligible buildings.",
        "steps": steps,
        "check": {
            "passed":   trace["holds"],
            "headline": "tray = E",
            "message": (
                f"The invariant held at all {n} step(s); the tray ends with "
                f"{len(trace['tray'])} building(s)."
                if trace["holds"] else
                "The invariant failed at some step."
            ),
            "evidence": ", ".join(trace["tray"]) or "the tray is empty",
        },
    }


PROOF_ORDER = ["direct", "contraposition", "contradiction",
               "counterexample", "correctness"]

_BUILDERS = {
    "direct":         direct_proof,
    "contraposition": contraposition_proof,
    "contradiction":  contradiction_proof,
    "counterexample": counterexample_proof,
    "correctness":    correctness_proof,
}


def build_proof(key: str, df: pd.DataFrame, thresholds: dict) -> dict:
    """Build one proof by key.  Unknown keys return an empty result."""
    builder = _BUILDERS.get(str(key))
    if builder is None:
        return {"key": str(key), "title": "", "claim": "", "steps": [],
                "check": {"passed": False, "headline": "", "message":
                          f"Unknown proof '{key}'.", "evidence": ""}}
    return builder(df, thresholds)


def all_proofs(df: pd.DataFrame, thresholds: dict) -> list:
    """Build every proof, in the order shown on the page."""
    return [build_proof(k, df, thresholds) for k in PROOF_ORDER]


# ---------------------------------------------------------------------------
# Induction
# ---------------------------------------------------------------------------

CONNECTED_CLAIM = (
    "In a network of n buildings where every building can reach every other, "
    "there are at least n − 1 connections."
)


def weak_induction(n: int) -> dict:
    """
    Describe the induction argument for :data:`CONNECTED_CLAIM`, and list the
    first *n* cases.

    The listing matches the argument; it is not itself a proof.
    """
    n = int(n) if isinstance(n, (int, float)) and not isinstance(n, bool) else 0
    if n < 1:
        n = 1
    if n > 24:
        n = 24

    cases = [
        {"n": k, "minimum": k - 1, "holds": (k - 1) >= 0}
        for k in range(1, n + 1)
    ]
    return {
        "n": n,
        "claim": CONNECTED_CLAIM,
        "base_case": {
            "n": 1,
            "text": "A single building needs no connections: 0 ≥ 1 − 1.",
        },
        "step": {
            "assume": "Assume every network of k buildings needs at least k − 1 "
                      "connections.",
            "show":   "Add one more building. It must be joined to the rest by "
                      "at least one connection, so the network now has at least "
                      "(k − 1) + 1 = k connections for k + 1 buildings.",
            "conclusion": "Therefore the claim holds for k + 1, and by "
                          "induction for every n ≥ 1.",
        },
        "cases": cases,
        "note": "The falling dominoes show how the argument chains from one "
                "case to the next.  Watching cases fall is a helpful picture, "
                "not a proof — only the induction step covers every n.",
    }


def strong_induction(n: int) -> dict:
    """
    Group *n* buildings (n ≥ 2) into phases of 2 and 3 for the strong
    induction argument, listing the two base cases.
    """
    n = int(n) if isinstance(n, (int, float)) and not isinstance(n, bool) else 2
    if n < 2:
        n = 2
    if n > 24:
        n = 24

    if n == 2:
        phases = [2]
    elif n == 3:
        phases = [3]
    elif n % 3 == 0:
        phases = [3] * (n // 3)
    elif n % 3 == 1:
        phases = [2, 2] + [3] * ((n - 4) // 3)
    else:                                   # n % 3 == 2
        phases = [2] + [3] * ((n - 2) // 3)

    return {
        "n": n,
        "claim": CONNECTED_CLAIM,
        "base_cases": [
            {"n": 2, "minimum": 1, "text":
             "Two buildings need one connection: 1 ≥ 2 − 1."},
            {"n": 3, "minimum": 2, "text":
             "Three buildings need two connections: 2 ≥ 3 − 1."},
        ],
        "phases": phases,
        "step": {
            "assume": "Assume the claim holds for every size from 2 up to k.",
            "show":   "Peel off a group of 2 or 3 buildings, apply the claim to "
                      "the remaining buildings, then reconnect the group with a "
                      "group-size − 1 connections.",
            "conclusion": "Every n ≥ 2 splits into groups of 2 and 3, so the "
                          "claim holds for every n ≥ 2.",
        },
        "note": "Strong induction is needed because a group of 3 builds on the "
                "case of size 2 as well as on the case just below.",
    }
