"""
visual_data.py — Pure builders that turn campus data into the JSON each
interactive visual draws.

Every function here is a pure function of the campus data: it computes the
result in Python and returns a plain, JSON-serialisable dict.  The browser only
draws what it is given — no arithmetic happens in JavaScript.

Two conventions hold throughout:

  * every building appears as a pair ``{"key": <raw name>, "label": <safe name>}``
    where ``label`` has been escaped with :func:`html.escape` and is the only
    value the visual is allowed to print, while ``key`` is used for comparisons;
  * nothing is hardcoded — every number comes from the data and the thresholds.

No Streamlit imports.
"""

from __future__ import annotations

import html as _html
import math

import pandas as pd

from algorithms.validation import (
    COL_NAME,
    COL_DEMAND,
    COL_AREA,
    COL_SOLAR,
    DEFAULT_THRESHOLDS,
)
from algorithms.set_theory import (
    build_sets,
    eligible_set,
    venn_regions,
    funnel_stages,
    power_set,
)
from algorithms.relations import (
    connect_relation,
    relation_matrix,
    demand_order_summary,
    ranking,
    demand_values,
)
from algorithms.functions import function_overview
from algorithms.logic import (
    relation_properties,
    truth_table,
    classify_formula,
    check_equivalence,
)
from algorithms import proofs
from algorithms.counting import (
    combinations,
    permutations,
    permutations_with_repetition,
    combinations_with_repetition,
    stars_and_bars,
    stars_and_bars_distributions,
    multinomial,
    list_selections,
    double_counting,
    pascal_triangle,
)
from algorithms.pigeonhole import (
    holes_overview,
    ramsey_ring,
    ramsey_k6_all_colourings,
    mantel_playground,
    monotone_runs,
)
from algorithms.inclusion_exclusion import (
    venn_counting,
    derangement_listing,
    onto_functions,
    phi_ring,
    prime_sieve_steps,
)


PALETTE = {
    "forest": "#14532D",
    "green":  "#16A34A",
    "amber":  "#F59E0B",
    "bg":     "#FAFAF7",
    "card":   "#FFFFFF",
    "ink":    "#1F2937",
    "muted":  "#6B7280",
    "danger": "#DC2626",
    "border": "#E5E7EB",
    "leaf":   "#DCFCE7",
}


def esc(text) -> str:
    """Escape user text so it can never break out of HTML or an attribute."""
    return _html.escape(str(text), quote=True)


def _limits(thresholds) -> dict:
    t = thresholds or {}
    return {
        "min_demand": float(t.get("min_demand", DEFAULT_THRESHOLDS["min_demand"])),
        "min_area":   float(t.get("min_area",   DEFAULT_THRESHOLDS["min_area"])),
        "min_solar":  float(t.get("min_solar",  DEFAULT_THRESHOLDS["min_solar"])),
    }


def _rows(df: pd.DataFrame) -> list:
    """Return ``[(name, demand, area, solar)]`` sorted by name."""
    if df is None or df.empty:
        return []
    out = [
        (str(row[COL_NAME]), float(row[COL_DEMAND]),
         float(row[COL_AREA]), float(row[COL_SOLAR]))
        for _, row in df.iterrows()
    ]
    return sorted(out, key=lambda r: r[0])


def _data_rows(df: pd.DataFrame) -> list:
    """Return ``[(name, demand, area, solar)]`` in the data's own row order."""
    if df is None or df.empty:
        return []
    return [
        (str(row[COL_NAME]), float(row[COL_DEMAND]),
         float(row[COL_AREA]), float(row[COL_SOLAR]))
        for _, row in df.iterrows()
    ]


def _eligible_ordered(df: pd.DataFrame, thresholds: dict) -> list:
    """Eligible buildings as raw names, in the data's own row order."""
    limits = _limits(thresholds)
    out = []
    for name, demand, area, solar in _data_rows(df):
        if not _failed_keys(demand, area, solar, limits):
            out.append(name)
    return out


def _failed_keys(demand, area, solar, limits) -> list:
    failed = []
    if not demand >= limits["min_demand"]:
        failed.append("A")
    if not area >= limits["min_area"]:
        failed.append("B")
    if not solar >= limits["min_solar"]:
        failed.append("C")
    return failed


_FAIL_TEXT = {
    "A": "demand", "B": "area", "C": "solar",
}


# ===========================================================================
# Sets page
# ===========================================================================

def campus_map_data(df: pd.DataFrame, thresholds: dict) -> dict:
    """
    Visual 1 — the campus map.

    Each building becomes a tile whose side depends on its rooftop area, with
    a demand bar, a solar figure and the criteria it fails.
    """
    limits = _limits(thresholds)
    rows = _rows(df)
    if not rows:
        return {"buildings": [], "thresholds": limits, "max_area": 0.0,
                "max_demand": 0.0}

    max_area = max(r[2] for r in rows) or 1.0
    max_demand = max(r[1] for r in rows) or 1.0

    buildings = []
    for i, (name, demand, area, solar) in enumerate(rows):
        failed = _failed_keys(demand, area, solar, limits)
        buildings.append({
            "id":       i,
            "key":      name,
            "label":    esc(name),
            "demand":   demand,
            "area":     area,
            "solar":    solar,
            "eligible": not failed,
            "failed":   failed,
            "failed_text": " and ".join(_FAIL_TEXT[k] for k in failed),
            "tile":     round(72 + 56 * (area / max_area)),
            "criteria": {
                "A": demand >= limits["min_demand"],
                "B": area >= limits["min_area"],
                "C": solar >= limits["min_solar"],
            },
        })

    return {
        "buildings":  buildings,
        "thresholds": limits,
        "max_area":   max_area,
        "max_demand": max_demand,
    }


def funnel_data(df: pd.DataFrame, thresholds: dict) -> dict:
    """Visual 2 — the filter funnel: the three criteria applied in turn."""
    result = funnel_stages(df, thresholds)
    stages = []
    for stage in result["stages"]:
        stages.append({
            "criterion": stage["criterion"],
            "label":     stage["label"],
            "count_in":  stage["count_in"],
            "count_out": stage["count_out"],
            "kept":      [{"key": n, "label": esc(n)} for n in stage["kept"]],
            "removed":   [{"key": r["name"], "label": esc(r["name"]),
                           "reason": r["reason"]} for r in stage["removed"]],
        })
    return {
        "start":       [{"key": n, "label": esc(n)} for n in result["start"]],
        "stages":      stages,
        "final":       [{"key": n, "label": esc(n)} for n in result["final"]],
        "final_label": result["final_label"],
        "counts":      result["counts"],
        "thresholds":  _limits(thresholds),
    }


def venn_data(df: pd.DataFrame, thresholds: dict) -> dict:
    """Visual 3 — the three-set Venn diagram, its regions and its operations."""
    limits = _limits(thresholds)
    sets = build_sets(df, thresholds)
    U, A, B, C = sets["U"], sets["A"], sets["B"], sets["C"]
    E = eligible_set(A, B, C)
    regions = venn_regions(A, B, C, U)

    region_payload = {
        key: [{"key": n, "label": esc(n)} for n in sorted(value)]
        for key, value in regions.items()
    }

    def _notation(names) -> str:
        listed = sorted(names)
        parts = ", ".join(esc(n) for n in listed)
        return "{ " + parts + " }" if parts else "∅"

    operations = [
        {"key": "intersection", "label": "A ∩ B ∩ C",
         "regions": ["A_B_C"], "members": E},
        {"key": "union", "label": "A ∪ B ∪ C",
         "regions": ["A_only", "B_only", "C_only", "A_B", "A_C", "B_C", "A_B_C"],
         "members": A | B | C},
        {"key": "A-B", "label": "A − B",
         "regions": ["A_only", "A_C"], "members": A - B},
        {"key": "B-A", "label": "B − A",
         "regions": ["B_only", "B_C"], "members": B - A},
        {"key": "C-A", "label": "C − A",
         "regions": ["C_only", "B_C"], "members": C - A},
        {"key": "A-C", "label": "A − C",
         "regions": ["A_only", "A_B"], "members": A - C},
        {"key": "complement-C", "label": "C′  (complement of C)",
         "regions": ["A_only", "B_only", "A_B", "none"],
         "members": U - C},
        {"key": "complement-E", "label": "E′  (complement of E)",
         "regions": ["A_only", "B_only", "C_only", "A_B", "A_C", "B_C", "none"],
         "members": U - E},
    ]

    return {
        "thresholds": limits,
        "counts": {
            "U": len(U), "A": len(A), "B": len(B), "C": len(C), "E": len(E),
        },
        "region_counts": {k: len(v) for k, v in regions.items()},
        "regions":  region_payload,
        "operations": [
            {
                "key":     op["key"],
                "label":   op["label"],
                "regions": op["regions"],
                "members": [{"key": n, "label": esc(n)}
                            for n in sorted(op["members"])],
                "size":    len(op["members"]),
                "notation": _notation(op["members"]),
            }
            for op in operations
        ],
        "labels": {
            "A": "[A] demand",
            "B": "[B] area",
            "C": "[C] solar",
        },
    }


def power_set_data(df: pd.DataFrame, thresholds: dict) -> dict:
    """Support for the power-set card on the Sets page."""
    sets = build_sets(df, thresholds)
    E = eligible_set(sets["A"], sets["B"], sets["C"])
    subsets = power_set(E)
    return {
        "set":      [{"key": n, "label": esc(n)} for n in sorted(E)],
        "size":     len(E),
        "subsets":  [[esc(n) for n in subset] for subset in subsets],
        "count":    len(subsets),
    }


# ===========================================================================
# Relations & Functions page
# ===========================================================================

_PROP_LABELS = [
    ("reflexive",     "reflexive"),
    ("symmetric",     "symmetric"),
    ("antisymmetric", "antisymmetric"),
    ("transitive",    "transitive"),
    ("equivalence",   "equivalence"),
]


def relation_diagram_data(df: pd.DataFrame, edges, thresholds: dict) -> dict:
    """Visual 4 — the "can be connected to" relation, its properties and grid."""
    domain = sorted(str(n) for n in (df[COL_NAME].tolist() if df is not None and not df.empty else []))
    if not domain:
        return {"nodes": [], "links": [], "badges": [], "matrix":
                {"labels": [], "grid": []}, "counterexample": None}

    relation = connect_relation(edges, domain)
    props = relation_properties(relation, domain)
    matrix = relation_matrix(relation, domain)

    index = {name: i for i, name in enumerate(domain)}
    nodes = [
        {"id": i, "key": name, "label": esc(name),
         "angle": round(360.0 * i / len(domain), 2)}
        for i, name in enumerate(domain)
    ]

    links = []
    for a, b in relation:
        if index[a] < index[b]:
            links.append({"a": index[a], "b": index[b],
                          "a_key": a, "b_key": b})

    ce = props["counterexamples"]

    def _pair_text(pair) -> str:
        if pair is None:
            return ""
        return f"({esc(pair[0])}, {esc(pair[1])})"

    highlights = {}
    if ce.get("reflexive"):
        a = ce["reflexive"][0]
        highlights["reflexive"] = {
            "nodes": [index[a]], "links": [],
            "text": f"No loop at {esc(a)}: ({esc(a)}, {esc(a)}) is missing.",
        }
    if ce.get("symmetric"):
        a, b = ce["symmetric"]
        highlights["symmetric"] = {
            "nodes": [index[a], index[b]],
            "links": [[index[a], index[b]]],
            "text": f"({esc(a)}, {esc(b)}) is present but ({esc(b)}, {esc(a)}) "
                    f"is not.",
        }
    if ce.get("antisymmetric"):
        a, b = ce["antisymmetric"]
        highlights["antisymmetric"] = {
            "nodes": [index[a], index[b]],
            "links": [[index[a], index[b]], [index[b], index[a]]],
            "text": f"{esc(a)} and {esc(b)} are each linked to the other, and "
                    f"they are different buildings.",
        }
    if ce.get("transitive"):
        a, b, c = ce["transitive"]
        highlights["transitive"] = {
            "nodes": [index[a], index[b], index[c]],
            "links": [[index[a], index[b]], [index[b], index[c]]],
            "text": f"({esc(a)}, {esc(b)}) and ({esc(b)}, {esc(c)}) are present "
                    f"but ({esc(a)}, {esc(c)}) is not.",
        }
    highlights["equivalence"] = {
        "nodes": [], "links": [],
        "text": "An equivalence relation must be reflexive, symmetric and "
                "transitive; at least one of the three fails.",
    }

    reasons = {
        "reflexive": "every building would need a link to itself",
        "symmetric": "a link one way would need a link back",
        "antisymmetric": "two different buildings linked both ways break it",
        "transitive": "a link a–b and b–c would need a link a–c",
        "equivalence": "needs reflexive, symmetric and transitive together",
    }

    badges = [
        {"key": key, "label": label, "passed": bool(props[key]),
         "reason": reasons[key]}
        for key, label in _PROP_LABELS
    ]

    return {
        "nodes":       nodes,
        "links":       links,
        "badges":      badges,
        "highlights":  highlights,
        "partial_order": bool(props.get("partial_order")),
        "matrix":      matrix,
        "pair_count":  len(relation),
        "domain_size": len(domain),
        "empty":       len(relation) == 0,
    }


def ranking_data(df: pd.DataFrame, thresholds: dict, equal_pair=None) -> dict:
    """
    Visual 5 — the demand ladder.

    ``equal_pair`` is an optional ``(a, b)``; when given, the second building's
    demand is replaced by the first's so the ladder shows what a tie does.
    """
    work = df
    note = ""
    if equal_pair and df is not None and not df.empty:
        a, b = str(equal_pair[0]), str(equal_pair[1])
        values = demand_values(df)
        if a in values and b in values:
            work = df.copy()
            work.loc[work[COL_NAME].astype(str) == b, COL_DEMAND] = values[a]
            note = (f"{esc(b)} now has the same demand as {esc(a)}, so the two "
                    f"share a rung of the ladder.")

    summary = demand_order_summary(work)
    order = summary["order"]
    return {
        "order": [{"key": n, "label": esc(n),
                   "rank": summary["ranks"][n],
                   "demand": demand_values(work).get(n, 0.0)}
                  for n in order],
        "ranks":       summary["ranks"],
        "ties":        [[{"key": n, "label": esc(n)} for n in group]
                        for group in summary["ties"]],
        "total_order": summary["total_order"],
        "pair_count":  len(summary["pairs"]),
        "note":        note,
        "equal_active": bool(note),
    }


def function_data(df: pd.DataFrame, thresholds: dict) -> dict:
    """Visual 6 — the three function maps, with their properties."""
    overview = function_overview(df, thresholds)

    def _pack(info):
        return {
            "name":       info["name"],
            "domain":     [{"key": str(d), "label": esc(d)} for d in info["domain"]],
            "codomain":   [{"key": str(c), "label": esc(c)} for c in info["codomain"]],
            "arrows":     [[str(a), str(b)] for a, b in info["arrows"]],
            "missing":    [str(m) for m in info.get("missing", [])],
            "injective":  bool(info["injective"]),
            "surjective": bool(info["surjective"]),
            "bijective":  bool(info["bijective"]),
            "valid":      bool(info["valid"]),
            "details":    info.get("details", ""),
        }

    return {
        "demand":   _pack(overview["demand"]),
        "eligible": _pack(overview["eligible"]),
        "rank":     _pack(overview["rank"]),
    }


# ===========================================================================
# Logic page
# ===========================================================================

_VARS = ["p", "q", "r"]


def _row_index(p: bool, q: bool, r: bool) -> int:
    return (int(p) << 2) | (int(q) << 1) | int(r)


def logic_gate_data(df: pd.DataFrame, thresholds: dict) -> dict:
    """Visual 7 — the switch diagram and the truth-table row it points at."""
    limits = _limits(thresholds)
    rows = _rows(df)
    buildings = []
    by_row: dict = {}
    for name, demand, area, solar in rows:
        failed = _failed_keys(demand, area, solar, limits)
        p = "A" not in failed
        q = "B" not in failed
        r = "C" not in failed
        idx = _row_index(p, q, r)
        buildings.append({
            "key": name, "label": esc(name),
            "p": p, "q": q, "r": r, "row": idx, "eligible": not failed,
        })
        by_row.setdefault(idx, []).append({"key": name, "label": esc(name)})

    return {
        "variables": ["p", "q", "r"],
        "meanings": {"p": "in A — demand", "q": "in B — area",
                     "r": "in C — solar"},
        "buildings": buildings,
        "rows":      [{"index": i, "p": bool(i >> 2 & 1),
                       "q": bool(i >> 1 & 1), "r": bool(i & 1),
                       "eligible": bool((i >> 2 & 1) and (i >> 1 & 1) and (i & 1)),
                       "buildings": by_row.get(i, [])}
                      for i in range(8)],
        "thresholds": limits,
    }


def truth_table_data(df: pd.DataFrame, thresholds: dict) -> dict:
    """Visual 8 — the eight-row truth table with building chips."""
    gate = logic_gate_data(df, thresholds)
    classification = classify_formula("(p and q) and r")
    return {
        "rows": [{"index": r["index"], "p": r["p"], "q": r["q"], "r": r["r"],
                  "eligible": r["p"] and r["q"] and r["r"],
                  "buildings": r["buildings"]}
                 for r in gate["rows"]],
        "classification": classification["classification"],
        "formula": "eligible = p ∧ q ∧ r",
        "variables": ["p", "q", "r"],
    }


def de_morgan_data(df: pd.DataFrame, thresholds: dict) -> dict:
    """Visual 9 — De Morgan's law shown on all eight rows."""
    left = truth_table("not (p and q and r)")
    right = truth_table("(not p) or (not q) or (not r)")

    rows = []
    for lrow, rrow in zip(left["rows"], right["rows"]):
        rows.append({
            "p": lrow.get("p", False),
            "q": lrow.get("q", False),
            "r": lrow.get("r", False),
            "left": bool(lrow["result"]),
            "right": bool(rrow["result"]),
            "equal": bool(lrow["result"]) == bool(rrow["result"]),
        })

    return {
        "rows": rows,
        "all_equal": all(r["equal"] for r in rows),
        "left_label": "not (p and q and r)",
        "right_label": "(not p) or (not q) or (not r)",
        "left_pretty": "¬(p ∧ q ∧ r)",
        "right_pretty": "¬p ∨ ¬q ∨ ¬r",
        "errors": left["errors"] + right["errors"],
    }


def formula_data(formula: str, df: pd.DataFrame, thresholds: dict) -> dict:
    """
    Visual 10 — the formula tester.

    Returns the truth table, the classification, whether the formula is
    equivalent to "eligible", and the implication with its converse and
    contrapositive.
    """
    table = truth_table(formula)
    classification = classify_formula(formula)

    eligible = "(p and q) and r"
    equiv = check_equivalence(formula, eligible)

    implication = "((p and q) and r) -> p"
    converse = "p -> ((p and q) and r)"
    contrapositive = "not p -> not ((p and q) and r)"

    return {
        "formula":       formula,
        "variables":     table["variables"],
        "rows":          [{"values": {k: v for k, v in row.items() if k != "result"},
                           "result": bool(row["result"])}
                          for row in table["rows"]],
        "errors":        table["errors"],
        "classification": classification["classification"],
        "equivalent_to_eligible": bool(equiv["equivalent"]),
        "equivalence_errors": equiv["errors"],
        "equivalence_counterexample": equiv.get("counterexample"),
        "implication": {
            "statement":       implication,
            "converse":        converse,
            "contrapositive":  contrapositive,
            "statement_vs_contrapositive":
                check_equivalence(implication, contrapositive)["equivalent"],
            "statement_vs_converse":
                check_equivalence(implication, converse)["equivalent"],
        },
    }


# ===========================================================================
# Proofs page
# ===========================================================================

def proof_stepper_data(df: pd.DataFrame, thresholds: dict, key: str) -> dict:
    """Visual 11 — one proof as numbered step cards with a live check."""
    return proofs.build_proof(key, df, thresholds)


def all_proofs_data(df: pd.DataFrame, thresholds: dict) -> dict:
    return {key: proofs.build_proof(key, df, thresholds)
            for key in proofs.PROOF_ORDER}


def induction_data(n: int) -> dict:
    """Visual 12 — the falling-dominoes induction argument."""
    return proofs.weak_induction(n)


def strong_induction_data(n: int) -> dict:
    """Visual 13 — the strong-induction grouping into 2s and 3s."""
    return proofs.strong_induction(n)


def conveyor_data(df: pd.DataFrame, thresholds: dict) -> dict:
    """Visual 14 — the loop that builds the eligible list, one step per row."""
    trace = proofs.eligible_loop(df, thresholds)
    return {
        "order":     [{"key": s["name"], "label": esc(s["name"])}
                      for s in trace["steps"]],
        "steps": [
            {
                "index":     s["index"],
                "name":      s["name"],
                "label":     esc(s["name"]),
                "accepted":  s["accepted"],
                "tray":      [{"key": n, "label": esc(n)} for n in s["tray"]],
                "invariant_holds": s["invariant_holds"],
            }
            for s in trace["steps"]
        ],
        "tray":      [{"key": n, "label": esc(n)} for n in trace["tray"]],
        "invariant": trace["invariant"],
        "holds":     trace["holds"],
    }


# ===========================================================================
# Shared helpers for the counting / pigeonhole / inclusion-exclusion pages
# ===========================================================================

_DISPLAY_CAP = 60
_ITEM_CAP = 40
# How many on/off patterns a visual may be handed: 2^10 = 1024 states.
_STATE_BITS = 10


def _chips(names) -> list:
    """A list of ``{"key", "label"}`` pairs with the labels escaped."""
    return [{"key": str(n), "label": esc(n)} for n in names]


def _item_labels(items) -> list:
    """Escape every name inside a list of tuples of names."""
    return [[esc(x) for x in tup] for tup in items]


# ===========================================================================
# Counting page
# ===========================================================================

def selection_explorer_data(df: pd.DataFrame, thresholds: dict, k: int = 2) -> dict:
    """
    Visual 15 — pick k eligible buildings, with or without order.

    Every k from 0 to n is precomputed, so the slider inside the visual is a
    pure lookup: C(n,k), P(n,k) and, when repetition is allowed, n^k and
    C(n+k−1, k), each with the whole selection listed.
    """
    names = _eligible_ordered(df, thresholds)
    n = len(names)
    if n == 0:
        return {"n": 0, "k": 0, "max_k": 0, "item_cap": _ITEM_CAP,
                "buildings": [], "by_k": [],
                "errors": ["No eligible buildings yet."]}

    k = int(k) if isinstance(k, int) and not isinstance(k, bool) else 2
    k = max(0, min(k, n))

    by_k = []
    for j in range(n + 1):
        combos = list_selections(n, j, ordered=False, labels=names)
        perms = list_selections(n, j, ordered=True, labels=names)
        c = combinations(n, j)
        p = permutations(n, j)
        rep_ordered = permutations_with_repetition(n, j)
        rep_unordered = combinations_with_repetition(n, j)

        combo_items = _item_labels(combos["items"])
        perm_items = _item_labels(perms["items"])

        by_k.append({
            "k": j,
            "unordered": {
                "count":     c["value"],
                "formula":   c["formula"],
                "items":     combo_items[:_ITEM_CAP],
                "listed":    len(combo_items),
                "truncated": combos["truncated"] or len(combo_items) > _ITEM_CAP,
            },
            "ordered": {
                "count":     p["value"],
                "formula":   p["formula"],
                "items":     perm_items[:_ITEM_CAP],
                "listed":    len(perm_items),
                "truncated": perms["truncated"] or len(perm_items) > _ITEM_CAP,
            },
            "repeat": {
                "ordered":   {"count": rep_ordered["value"],
                              "formula": rep_ordered["formula"]},
                "unordered": {"count": rep_unordered["value"],
                              "formula": rep_unordered["formula"]},
            },
        })

    return {
        "n": n,
        "k": k,
        "max_k": n,
        "item_cap": _ITEM_CAP,
        "buildings": _chips(names),
        "by_k": by_k,
        "unordered": by_k[k]["unordered"],
        "ordered":   by_k[k]["ordered"],
        "repeat":    by_k[k]["repeat"],
        "errors": [],
    }


_MAX_BATCHES = 15


def _balls_state(m: int, n: int, names) -> dict:
    """One batch count, fully worked out (used for every possible m)."""
    sb = stars_and_bars(m, n)
    distinguishable = permutations_with_repetition(n, m)

    state = {
        "m": m,
        "identical": {
            "count":    sb["value"],
            "formula":  sb["formula"],
            "expected": math.comb(m + n - 1, n - 1),
        },
        "distributions":  [],
        "dist_count":     0,
        "dist_expected":  0,
        "dist_truncated": False,
        "distinguishable": {"count": distinguishable["value"],
                            "formula": distinguishable["formula"]},
        "at_least_one": None,
    }

    if n <= 6:
        dist = stars_and_bars_distributions(m, n, min_each=0, labels=names)
        rows = [list(d) for d in dist["distributions"]]
        state["distributions"] = rows[:_DISPLAY_CAP]
        state["dist_count"] = dist["count"]
        state["dist_expected"] = dist["expected"]
        state["dist_truncated"] = dist["truncated"] or len(rows) > _DISPLAY_CAP

        if m >= n:
            each = stars_and_bars_distributions(m, n, min_each=1, labels=names)
            each_rows = [list(d) for d in each["distributions"]]
            state["at_least_one"] = {
                "count":    each["count"],
                "expected": each["expected"],
                "formula":  (f"C({m}−1, {n}−1) = C({m - 1},{n - 1}) = "
                             f"{each['expected']}"),
                "distributions": each_rows[:_DISPLAY_CAP],
                "truncated": each["truncated"] or len(each_rows) > _DISPLAY_CAP,
            }

    return state


def balls_and_bins_data(df: pd.DataFrame, thresholds: dict, m: int = 5) -> dict:
    """
    Visual 16 — m identical panel batches shared between n buildings.

    Every batch count from 0 to 15 is worked out in Python, so the slider in
    the visual only looks a state up: the distributions (stars and bars), the
    distinguishable-panel count n^m, and the "every building gets at least
    one" case.
    """
    names = _eligible_ordered(df, thresholds)
    n = len(names)
    if n == 0:
        return {"m": 0, "n": 0, "max_m": _MAX_BATCHES, "bins": [], "by_m": [],
                "identical": None, "distributions": [], "dist_count": 0,
                "dist_expected": 0, "dist_truncated": False,
                "distinguishable": None, "at_least_one": None,
                "errors": ["No eligible buildings yet."]}

    m = int(m) if isinstance(m, int) and not isinstance(m, bool) else 5
    m = max(0, min(m, _MAX_BATCHES))

    by_m = [_balls_state(j, n, names) for j in range(_MAX_BATCHES + 1)]

    return {
        "m": m,
        "n": n,
        "max_m": _MAX_BATCHES,
        "bins": _chips(names),
        "by_m": by_m,
        **{key: by_m[m][key] for key in (
            "identical", "distributions", "dist_count", "dist_expected",
            "dist_truncated", "distinguishable", "at_least_one")},
        "errors": [],
    }


_DEFAULT_SHIFT_TYPES = ("Day", "Night", "Standby")


def multinomial_data(df: pd.DataFrame, thresholds: dict,
                     counts=(2, 2, 1), types=_DEFAULT_SHIFT_TYPES) -> dict:
    """
    Visual 17 — a crew-shift sequence built from counts per type.

    The number of distinct sequences is the multinomial
    (2+2+1)! / (2!·2!·1!) = 30.
    """
    counts = [int(c) for c in counts]
    types = list(types)
    r = multinomial(counts)

    payload_types = [
        {"key": f"t{i}", "label": esc(label), "count": c}
        for i, (label, c) in enumerate(zip(types, counts))
    ]
    sequence: list = []
    for label, c in zip(types, counts):
        sequence.extend([esc(label)] * max(0, c))

    return {
        "types":        payload_types,
        "counts":       counts,
        "sequence":     sequence,
        "total":        r["total"],
        "value":        r["value"],
        "numerator":    r["numerator"],
        "denominator":  r["denominator"],
        "formula":      r["formula"],
        "errors":       r["errors"],
    }


def pascal_explorer_data(df: pd.DataFrame, thresholds: dict, rows: int = 13,
                         n: int = 5, k: int = 2) -> dict:
    """
    Visual 18 — Pascal's triangle up to row 12.

    Clicking a cell highlights its two parents and the rule
    C(n,k) = C(n−1,k−1) + C(n−1,k); the row-sum bar shows 2^n and the
    symmetry toggle mirrors C(n,k) to C(n,n−k).
    """
    tri = pascal_triangle(rows)
    if tri["errors"]:
        return {"triangle": [], "row_sums": [], "rows": 0, "selected": None,
                "symmetric": None, "identity_checks": {}, "errors": tri["errors"]}

    triangle = tri["triangle"]
    row_sums = [sum(row) for row in triangle]
    total_rows = len(triangle)

    n = int(n) if isinstance(n, int) and not isinstance(n, bool) else 5
    k = int(k) if isinstance(k, int) and not isinstance(k, bool) else 2
    n = max(0, min(n, total_rows - 1))
    k = max(0, min(k, n))

    # Every cell carries its own two parents, its own rule check and its own
    # mirror, so clicking any cell in the visual is a lookup, not a sum.
    cells = []
    for r in range(total_rows):
        row_cells = []
        for column in range(r + 1):
            value = triangle[r][column]
            has_parents = r >= 1 and 1 <= column <= r - 1
            left_value = triangle[r - 1][column - 1] if has_parents else None
            right_value = triangle[r - 1][column] if has_parents else None
            row_cells.append({
                "n": r, "k": column, "value": value,
                "has_parents": has_parents,
                "left_value":  left_value,
                "right_value": right_value,
                "left_n": r - 1 if has_parents else None,
                "left_k": column - 1 if has_parents else None,
                "right_n": r - 1 if has_parents else None,
                "right_k": column if has_parents else None,
                "rule_holds": bool(has_parents and
                                   left_value + right_value == value),
                "mirror_k": r - column,
                "mirror_value": triangle[r][r - column],
                "symmetric_holds": value == triangle[r][r - column],
            })
        cells.append(row_cells)

    has_parents = n >= 1 and 1 <= k <= n - 1
    left = {
        "n": n - 1, "k": k - 1,
        "value": triangle[n - 1][k - 1] if has_parents else None,
        "exists": has_parents,
    }
    right = {
        "n": n - 1, "k": k,
        "value": triangle[n - 1][k] if has_parents else None,
        "exists": has_parents,
    }
    selected_value = triangle[n][k]

    return {
        "triangle":  triangle,
        "row_sums":  row_sums,
        "rows":      total_rows,
        "cells":     cells,
        "selected": {
            "n": n, "k": k, "value": selected_value,
            "left": left, "right": right,
            "has_parents": has_parents,
            "rule_holds": bool(has_parents and
                               left["value"] + right["value"] == selected_value),
        },
        "symmetric": {
            "n": n, "k": k, "mirror_k": n - k,
            "value": selected_value,
            "mirror_value": triangle[n][n - k],
            "holds": selected_value == triangle[n][n - k],
        },
        "identity_checks": tri["identity_checks"],
        "errors": [],
    }


def double_counting_data(df: pd.DataFrame, thresholds: dict, edges) -> dict:
    """
    Visual 19 — the same total counted from both sides.

    Every (building, connection) pairing is one line: summing each building's
    connections and counting two endpoints per connection both give 12.
    """
    names = [row[0] for row in _data_rows(df)]
    r = double_counting(names, edges)

    return {
        "buildings": [
            {"key": b["key"], "label": esc(b["key"]), "degree": b["degree"]}
            for b in r["buildings"]
        ],
        "connections": [
            {"key": c["key"], "label": esc(c["key"]), "endpoints": c["endpoints"]}
            for c in r["connections"]
        ],
        "lines": [
            {
                "building_key":     line["building"],
                "building_label":   esc(line["building"]),
                "connection_key":   line["connection"],
                "connection_label": esc(line["connection"]),
            }
            for line in r["lines"]
        ],
        "tally_buildings":   r["tally_buildings"],
        "tally_connections": r["tally_connections"],
        "check":             r["check"],
        "vertex_count":      r["vertex_count"],
        "edge_count":        r["edge_count"],
    }


def combinatorial_proof_data(df: pd.DataFrame, thresholds: dict, k: int = 2) -> dict:
    """
    Visual 20 — the bijection behind C(n,k) = C(n,n−k).

    Each selection of k buildings to install pairs with the n−k buildings
    left out, so both sides count the same thing. The binomial row lets the
    panel read off C(n,s) for whatever s the toggles produce.
    """
    names = _eligible_ordered(df, thresholds)
    n = len(names)
    if n == 0:
        return {"n": 0, "k": 0, "max_k": 0, "buildings": [], "row": [],
                "pairs": [], "pairs_truncated": False, "totals": None,
                "states": [], "states_ready": False,
                "errors": ["No eligible buildings yet."]}

    k = int(k) if isinstance(k, int) and not isinstance(k, bool) else 2
    k = max(0, min(k, n))

    row = [math.comb(n, j) for j in range(n + 1)]
    combos = list_selections(n, k, ordered=False, labels=names)

    pairs = []
    for combo in combos["items"]:
        install = list(combo)
        skip = [x for x in names if x not in install]
        pairs.append({"install": [esc(x) for x in install],
                      "skip": [esc(x) for x in skip]})

    # Every "install or skip" pattern, with both sides of the identity already
    # counted, so toggling a building in the visual is a lookup.
    states = []
    if n <= _STATE_BITS:
        for mask in range(1 << n):
            install = [names[i] for i in range(n) if (mask >> i) & 1]
            skip = [names[i] for i in range(n) if not (mask >> i) & 1]
            size = len(install)
            every = list_selections(n, size, ordered=False, labels=names)["items"]
            position = every.index(tuple(install)) + 1 if every else 0
            states.append({
                "mask":        mask,
                "install":     [esc(x) for x in install],
                "skip":        [esc(x) for x in skip],
                "k":           size,
                "left_count":  math.comb(n, size),
                "right_count": math.comb(n, n - size),
                "position":    position,
                "equal":       math.comb(n, size) == math.comb(n, n - size),
            })

    return {
        "n": n,
        "k": k,
        "max_k": n,
        "buildings": _chips(names),
        "row": row,
        "pairs": pairs[:_DISPLAY_CAP],
        "pairs_truncated": len(pairs) > _DISPLAY_CAP,
        "states": states,
        "states_ready": n <= _STATE_BITS,
        "totals": {
            "k":         math.comb(n, k),
            "n_minus_k": math.comb(n, n - k),
            "equal":     math.comb(n, k) == math.comb(n, n - k),
        },
        "errors": [],
    }


# ===========================================================================
# Pigeonhole page
# ===========================================================================

_HOLE_MODES = ("bands", "crews")

_HOLE_MODE_LABELS = {
    "bands": "solar-potential bands",
    "crews": "surviving crews",
}


def _holes_entry(result: dict, m: int, mode: str) -> dict:
    """One (mode, hole count) pair, in the shape the visual draws."""
    if result["errors"]:
        return {"m": m, "mode": mode, "holes": [], "fullest": None,
                "fullest_label": "", "guaranteed": 0, "actual_max": 0,
                "statement": "", "errors": result["errors"]}

    return {
        "m": m,
        "mode": mode,
        "holes": [
            {
                "label":   h["label"],
                "members": _chips(h["members"]),
                "count":   h["count"],
                "lo":      h.get("lo"),
                "hi":      h.get("hi"),
            }
            for h in result["holes"]
        ],
        "fullest":       result["fullest"],
        "fullest_label": result["fullest_label"],
        "guaranteed":    result["guaranteed"],
        "actual_max":    result["actual_max"],
        "statement":     result["statement"],
        "errors":        [],
    }


def pigeons_holes_data(df: pd.DataFrame, thresholds: dict, n_holes: int = 4,
                       mode: str = "bands") -> dict:
    """
    Visual 21 — the six buildings dropped into m holes.

    In "bands" mode the holes are equal-width solar-potential bands; in
    "crews" mode the buildings are dealt round-robin to surviving crews.

    Every hole count from 1 to 8, in both modes, is worked out in Python, so
    the switch and the slider inside the visual only look a state up.
    """
    rows = _data_rows(df)
    names = [r[0] for r in rows]
    solars = [r[3] for r in rows]

    if not names:
        return {"n": 0, "m": 0, "mode": "bands", "max_holes": 8,
                "modes": list(_HOLE_MODES), "mode_labels": _HOLE_MODE_LABELS,
                "states": {}, "holes": [], "buildings": [], "fullest": None,
                "fullest_label": "", "guaranteed": 0, "actual_max": 0,
                "statement": "", "errors": ["No buildings yet."]}

    max_holes = 8
    states = {
        each: [_holes_entry(holes_overview(names, solars, j, each), j, each)
               for j in range(1, max_holes + 1)]
        for each in _HOLE_MODES
    }

    n_holes = int(n_holes) if isinstance(n_holes, int) and not isinstance(n_holes, bool) else 4
    n_holes = max(1, min(n_holes, max_holes))
    if mode not in _HOLE_MODES:
        mode = "bands"

    current = states[mode][n_holes - 1]

    return {
        "n": len(names),
        "m": n_holes,
        "mode": mode,
        "max_holes": max_holes,
        "modes": list(_HOLE_MODES),
        "mode_labels": _HOLE_MODE_LABELS,
        "states": states,
        "holes": current["holes"],
        "buildings": [{"key": name, "label": esc(name), "solar": solar}
                      for name, solar in zip(names, solars)],
        "fullest":       current["fullest"],
        "fullest_label": current["fullest_label"],
        "guaranteed":    current["guaranteed"],
        "actual_max":    current["actual_max"],
        "statement":     current["statement"],
        "errors":        [],
    }


_RAMSEY_RINGS = (5, 6)


def _ramsey_ring_payload(result: dict, check: dict) -> dict:
    """One ring, with the whole colouring table ready for the browser."""
    labels = [esc(v) for v in result["vertices"]]
    pairs = result["pairs"]
    triples = result["triples"]

    ring = {
        "n":             result["n"],
        "vertices":      _chips(result["vertices"]),
        "pairs":         pairs,
        "edge_labels":   [f"{labels[a]}–{labels[b]}" for a, b in pairs],
        "triples":       triples,
        "triple_labels": [" · ".join(labels[i] for i in tri) for tri in triples],
        "mask":          result["mask"],
        "mono_table":    result["mono_table"],
        "alphabet":      result["alphabet"],
        "no_triangle":   result["no_triangle"],
        "edges":         [{"a": e["a"], "b": e["b"], "colour": e["colour"]}
                          for e in result["edges"]],
        "mono_triangle": result["mono_triangle"],
        "mono_colour":   result["mono_colour"],
        "mono_line":     result["result_line"],
        "from_data":     result["from_data"],
        "note":          result["note"],
        "colour_labels": result["colour_labels"],
    }

    if result["n"] == 6:
        ring["exhaustive_line"] = (
            f"All {check['colourings_checked']:,} two-colourings of six buildings "
            f"contain a triple joined in one colour."
        )
    else:
        without = result["mono_table"].count(result["no_triangle"])
        ring["exhaustive_line"] = (
            f"{without} of the {2 ** len(pairs):,} two-colourings of five buildings "
            f"have no such triple, so five buildings are not enough."
        )
    return ring


def ramsey_data(df: pd.DataFrame, thresholds: dict, n: int = 6, edges=None) -> dict:
    """
    Visual 22 — R(3,3) = 6 on the ring of buildings.

    Both rings (five and six buildings) are prepared together: the base
    colouring taken from the campus connections, and a table holding the
    monochromatic triangle of every possible colouring, so flipping an edge in
    the visual is a lookup and the result line follows the click.
    """
    names = [row[0] for row in _data_rows(df)]
    available = [size for size in _RAMSEY_RINGS if len(names) >= size]

    if not available:
        return {"n": 0, "available": [], "rings": {},
                "colour_labels": {"can": "can be connected",
                                  "cannot": "cannot be connected"},
                "vertices": [], "edges": [], "mono_triangle": None,
                "mono_colour": None, "from_data": False, "note": "",
                "result_line": "",
                "errors": ["at least 5 buildings are needed for this view."]}

    check = ramsey_k6_all_colourings()
    rings = {str(size): _ramsey_ring_payload(ramsey_ring(size, names, edges), check)
             for size in available}

    n = int(n) if isinstance(n, int) and not isinstance(n, bool) else available[-1]
    if n not in available:
        n = available[-1]
    current = rings[str(n)]

    return {
        "n":             n,
        "available":     available,
        "rings":         rings,
        "colour_labels": current["colour_labels"],
        "vertices":      current["vertices"],
        "edges":         current["edges"],
        "mono_triangle": current["mono_triangle"],
        "mono_colour":   current["mono_colour"],
        "from_data":     current["from_data"],
        "note":          current["note"],
        "result_line":   current["mono_line"],
        "k6_check":      check,
        "errors":        [],
    }


def mantel_data(df: pd.DataFrame, thresholds: dict, edges=None) -> dict:
    """
    Visual 23 — remove connections until no triangle is left.

    Mantel's bound ⌊n²/4⌋ is 6 for five buildings and 9 for six; every subset
    of the campus connections is scored in Python so the browser only looks
    the current state up.
    """
    names = [row[0] for row in _data_rows(df)]
    r = mantel_playground(names, edges)

    if r["errors"]:
        return {"n": r["n"], "vertices": [], "edges": [], "states": [],
                "bound": r["bound"], "bounds": r["bounds"], "k33": None,
                "campus_triangles": [], "errors": r["errors"]}

    vertices = [{"key": name, "label": esc(name), "index": i}
                for i, name in enumerate(r["vertices"])]

    k33 = None
    if r["k33"]:
        k33 = {
            "left":          r["k33"]["left"],
            "right":         r["k33"]["right"],
            "edges":         r["k33"]["edges"],
            "count":         r["k33"]["count"],
            "triangle_free": r["k33"]["triangle_free"],
            "bound":         r["k33"]["bound"],
        }

    return {
        "n":                r["n"],
        "vertices":         vertices,
        "edges":            r["edges"],
        "states":           r["states"],
        "bound":            r["bound"],
        "bounds":           r["bounds"],
        "k33":              k33,
        "campus_triangles": r["campus_triangles"],
        "errors": [],
    }


TURAN_STATEMENT = {
    "title": "Turán's theorem",
    "text": ("On n buildings, a network that leaves out every group of r "
             "buildings has at most (1 − 1/(r−1)) · n²/2 connections. With "
             "r = 3 that is exactly Mantel's ⌊n²/4⌋."),
}


def erdos_szekeres_data(df: pd.DataFrame, thresholds: dict, count: int = 5) -> dict:
    """
    Visual 24 — the longest monotone run in the campus demands.

    The demands of the buildings in data order form a sequence; the longest
    non-decreasing and non-increasing runs are highlighted, and the theorem
    guarantees a run of length ⌈√n⌉.  Every prefix length has its runs worked
    out in Python, so the slider in the visual only looks a state up.
    """
    rows = _data_rows(df)
    if not rows:
        return {"bars": [], "sequence": [], "increase": [], "decrease": [],
                "increase_values": [], "decrease_values": [], "guarantee": 0,
                "actual_max": 0, "theorem_satisfied": False, "statement": "",
                "by_count": [], "max_count": 0, "run_rule": [],
                "turan": TURAN_STATEMENT, "errors": ["No buildings yet."]}

    top = max(2, min(len(rows), 30))
    by_count = []
    for j in range(2, top + 1):
        chosen = rows[:j]
        r = monotone_runs([c[1] for c in chosen])
        by_count.append({
            "count":     j,
            "bars":      [{"key": name, "label": esc(name), "value": demand}
                          for name, demand, _, _ in chosen],
            "sequence":  [c[1] for c in chosen],
            "increase":  r["increase"],
            "decrease":  r["decrease"],
            "increase_values": r["increase_values"],
            "decrease_values": r["decrease_values"],
            "guarantee": r["guarantee"],
            "actual_max": r["actual_max"],
            "theorem_satisfied": r["theorem_satisfied"],
            "statement": r["statement"],
        })

    count = int(count) if isinstance(count, int) and not isinstance(count, bool) else 5
    count = max(2, min(count, top))
    current = by_count[count - 2]

    return {
        **current,
        "by_count":  by_count,
        "max_count": top,
        "run_rule":  [{"k": k, "n_needed": k * k + 1, "run": k + 1}
                      for k in range(1, 6)],
        "turan":     TURAN_STATEMENT,
        "errors":    [],
    }


# ===========================================================================
# Inclusion–Exclusion page
# ===========================================================================

def venn_counting_data(df: pd.DataFrame, thresholds: dict) -> dict:
    """
    Visual 25 — the three-set counting stepper.

    |A∪B∪C| = |A|+|B|+|C| − |A∩B| − |A∩C| − |B∩C| + |A∩B∩C|, term by term,
    with the building counts in exactly one, exactly two, all three and none.
    """
    limits = _limits(thresholds)
    sets = build_sets(df, thresholds)
    A, B, C, U = sets["A"], sets["B"], sets["C"], sets["U"]
    r = venn_counting(A, B, C, U)

    regions = {key: _chips(sorted(value))
               for key, value in r["regions"].items()}

    return {
        "thresholds":     limits,
        "sizes":          r["sizes"],
        "intersections":  r["intersections"],
        "regions":        regions,
        "region_counts":  r["counts"],
        "terms":          [{"term": label, "value": value}
                           for label, value in r["terms"]],
        "steps":          r["steps"],
        "abs_sum":        r["abs_sum"],
        "lhs":            r["lhs"],
        "rhs":            r["rhs"],
        "holds":          r["holds"],
        "exactly_one":    r["exactly_one"],
        "exactly_two":    r["exactly_two"],
        "exactly_three":  r["exactly_three"],
        "outside":        r["outside"],
        "check":          r["check"],
        "labels":         {"A": "[A] demand", "B": "[B] area", "C": "[C] solar"},
        "errors":         [],
    }


def derangements_data(df: pd.DataFrame, thresholds: dict, n: int = 4) -> dict:
    """
    Visual 26 — crews rotating so nobody stays put.

    Every permutation of the n crews is listed with its fixed points marked;
    the derangements are the ones with none, and the count matches D(n).
    Every size from 0 to 6 is prepared so the slider only looks a state up.
    """
    n = int(n) if isinstance(n, int) and not isinstance(n, bool) else 4
    n = max(0, min(n, 6))
    names = [row[0] for row in _data_rows(df)]

    def _pack(size: int) -> dict:
        listing = derangement_listing(size)
        labels = [esc(names[i]) for i in range(min(size, len(names)))]
        while len(labels) < size:
            labels.append(esc(f"Slot {len(labels) + 1}"))
        return {
            "n": size,
            "labels": labels,
            "total": listing["total"],
            "rows": [{"perm": row["perm"], "fixed": row["fixed"],
                      "is_derangement": row["is_derangement"]}
                     for row in listing["rows"]],
            "truncated":   listing["truncated"],
            "count":       listing["derangement_count"],
            "formula":     listing["formula"],
            "brute_force": listing["brute_force"],
            "match":       listing["match"],
            "table":       listing["table"],
            "errors":      listing["errors"],
        }

    by_n = [_pack(size) for size in range(7)]
    current = by_n[n]
    return {**current, "max_n": 6, "by_n": by_n}


def onto_data(df: pd.DataFrame, thresholds: dict, crews: int = 3) -> dict:
    """
    Visual 27 — assign buildings to crews so every crew gets at least one.

    Onto(6,3) = 3⁶ − 3·2⁶ + 3·1⁶ − 0 = 540, shown term by term.
    """
    names = [row[0] for row in _data_rows(df)]
    n = len(names)
    if n == 0:
        return {"n": 0, "m": 0, "max_crews": 0, "buildings": [], "crews": [],
                "terms": [], "value": 0, "brute_force": None, "match": False,
                "total": 0, "total_formula": "", "errors": ["No buildings yet."]}

    crews = int(crews) if isinstance(crews, int) and not isinstance(crews, bool) else 3
    max_crews = min(n, 6)
    crews = max(1, min(crews, max_crews, 10))

    def _pack(m: int) -> dict:
        r = onto_functions(n, m)
        total = permutations_with_repetition(m, n)
        return {
            "m": m,
            "crews": [{"key": f"c{i}", "label": f"Crew {i + 1}"}
                      for i in range(m)],
            "terms":         r["terms"],
            "value":         r["formula"],
            "brute_force":   r["brute_force"],
            "match":         r["match"],
            "total":         total["value"],
            "total_formula": total["formula"],
            "errors":        r["errors"],
        }

    by_m = {str(m): _pack(m) for m in range(1, max_crews + 1)}
    current = by_m[str(crews)]
    return {
        "n": n,
        "m": crews,
        "max_crews": max_crews,
        "buildings": _chips(names),
        "by_m": by_m,
        **current,
    }


def phi_ring_data(df: pd.DataFrame, thresholds: dict, n: int = 12) -> dict:
    """
    Visual 28 — a ring of inspection slots and the step sizes that cover it.

    A step of size s visits every slot exactly when gcd(s,n) = 1, and there
    are φ(n) such steps — matching the inclusion-exclusion formula.
    """
    n = int(n) if isinstance(n, int) and not isinstance(n, bool) else 12
    n = max(2, min(n, 64))

    def _pack(size: int) -> dict:
        r = phi_ring(size)
        if r["errors"]:
            return {"n": size, "slots": 0, "steps": [], "coprime_steps": [],
                    "phi_count": 0, "phi_formula": 0, "prime_factors": [],
                    "formula_steps": [], "match": False, "errors": r["errors"]}
        return {
            "n":             size,
            "slots":         r["slots"],
            "steps":         r["steps"],
            "coprime_steps": r["coprime_steps"],
            "phi_count":     r["phi_count"],
            "phi_formula":   r["phi_formula"],
            "prime_factors": r["prime_factors"],
            "formula_steps": r["formula_steps"],
            "match":         r["match"],
            "errors":        [],
        }

    # Common ring sizes the slider can land on without a Streamlit rerun.
    sizes = sorted(set(list(range(2, 25)) + [n, 36]))
    sizes = [s for s in sizes if 2 <= s <= 64]
    by_n = {str(s): _pack(s) for s in sizes}
    current = by_n.get(str(n)) or _pack(n)
    return {**current, "max_n": 64, "by_n": by_n, "sizes": sizes}


def prime_sieve_data(df: pd.DataFrame, thresholds: dict, n: int = 100) -> dict:
    """
    Visual 29 — cross out the multiples of 2, 3, 5, 7 step by step.

    The survivors are 1 together with every prime up to n; the running
    inclusion-exclusion count of survivors is shown alongside.
    """
    n = int(n) if isinstance(n, int) and not isinstance(n, bool) else 100
    n = max(2, min(n, 1000))
    r = prime_sieve_steps(n)

    if r["errors"]:
        return {"n": n, "max_n": 1000, "columns": 10, "primes_used": [],
                "steps": [], "grid": [], "survivors": [], "survivor_count": 0,
                "prime_count": 0, "plain_prime_count": 0, "ie_terms": [],
                "ie_union": 0, "match": False, "errors": r["errors"]}

    columns = 10 if n >= 10 else n

    return {
        "n":                 n,
        "max_n":             1000,
        "columns":           columns,
        "primes_used":       r["primes_used"],
        "steps":             r["steps"],
        "grid":              r["grid"],
        "survivors":         r["survivors"],
        "survivor_count":    r["survivor_count"],
        "prime_count":       r["prime_count"],
        "plain_prime_count": r["plain_prime_count"],
        "ie_terms":          r["ie_terms"],
        "ie_union":          r["ie_union"],
        "match":             r["match"],
        "errors":            [],
    }
