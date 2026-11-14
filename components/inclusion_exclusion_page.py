"""Inclusion-Exclusion page: counting by adding, subtracting and adding back."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from algorithms import inclusion_exclusion as ie
from algorithms.validation import COL_DEMAND, COL_NAME, COL_SOLAR
from components.style import page_header


def _area_col(df):
    for c in df.columns:
        if "area" in str(c).lower():
            return c
    return None


def _sets(df, td, ta, ts):
    area = _area_col(df)
    num = lambda col: pd.to_numeric(df[col], errors="coerce")
    names = df[COL_NAME].astype(str)
    A = set(names[num(COL_DEMAND) >= td])
    B = set(names[num(area) >= ta]) if area else set()
    C = set(names[num(COL_SOLAR) >= ts])
    return set(names), A, B, C


def _show_errors(res) -> bool:
    if res.get("errors"):
        for e in res["errors"]:
            st.error(e)
        return True
    return False


def _tab_campus(df):
    st.subheader("Counting buildings that meet A, B or C")
    c1, c2, c3 = st.columns(3)
    td = c1.number_input("A: demand at least (kWh/day)", 0.0, 100000.0, 400.0, key="ie_td")
    ta = c2.number_input("B: rooftop area at least (m²)", 0.0, 100000.0, 800.0, key="ie_ta")
    ts = c3.number_input("C: solar potential at least (%)", 0.0, 100.0, 75.0, key="ie_ts")
    U, A, B, C = _sets(df, td, ta, ts)
    r = ie.venn_counting(A, B, C, universe=U)
    st.latex(
        r"\begin{aligned}|A\cup B\cup C| &= |A|+|B|+|C| \\"
        r"&\quad - |A\cap B| - |A\cap C| - |B\cap C| \\"
        r"&\quad + |A\cap B\cap C|\end{aligned}"
    )
    m1, m2, m3 = st.columns(3)
    m1.metric("Counted directly", r["lhs"])
    m2.metric("From the formula", r["rhs"])
    m3.metric("Agree", "Yes" if r["holds"] else "No")
    steps = pd.DataFrame(r["steps"]).rename(columns={"term": "Term", "value": "Adds", "running": "Running total"})
    st.dataframe(steps, hide_index=True, width="stretch")
    labels = {"A_only": "Only A", "B_only": "Only B", "C_only": "Only C", "A_B": "A and B only",
              "A_C": "A and C only", "B_C": "B and C only", "A_B_C": "All three", "none": "None of them"}
    rows = [{"Region": labels[k], "Count": r["counts"][k], "Buildings": ", ".join(v) or "-"}
            for k, v in r["regions"].items()]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption(f"Exactly one set: {r['exactly_one']}, exactly two: {r['exactly_two']}, all three: "
               f"{r['exactly_three']}, outside all: {r['outside']}. Check: |A|+|B|+|C| = {r['abs_sum']} = "
               f"{r['exactly_one']} + 2×{r['exactly_two']} + 3×{r['exactly_three']} → "
               f"{'holds' if r['check'] else 'does not hold'}.")


def _tab_derangements():
    st.subheader("Derangements: nobody keeps their old building")
    n = st.slider("Number of crews", 0, 6, 4, key="ie_dn")
    r = ie.derangement_listing(n)
    if _show_errors(r):
        return
    st.latex(r"D(n) = n!\sum_{k=0}^{n}\frac{(-1)^k}{k!}")
    a, b, c = st.columns(3)
    a.metric("All arrangements", r["total"])
    b.metric("Derangements counted", r["derangement_count"])
    c.metric("D(n) from formula", r["formula"])
    rows = [{"Arrangement": " ".join(str(x + 1) for x in e["perm"]),
             "Crews at old building": ", ".join(str(i + 1) for i in e["fixed"]) or "none",
             "Derangement": "Yes" if e["is_derangement"] else "No"} for e in r["rows"]]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    if r["truncated"]:
        st.caption(f"Showing the first {len(r['rows'])} arrangements. Counts above cover all of them.")
    with st.expander("D(n) table from the recurrence"):
        st.dataframe(pd.DataFrame(r["table"]), hide_index=True)


def _tab_onto():
    st.subheader("Onto functions: every building gets at least one crew")
    c1, c2 = st.columns(2)
    m = int(c1.number_input("Crews (m)", 1, 10, 4, key="ie_om"))
    n = int(c2.number_input("Buildings (n)", 1, 10, 3, key="ie_on"))
    r = ie.onto_functions(m, n)
    if _show_errors(r):
        return
    st.latex(r"\text{onto}(m,n)=\sum_{k=0}^{n}(-1)^k\binom{n}{k}(n-k)^m")
    a, b = st.columns(2)
    a.metric("From the formula", r["formula"])
    b.metric("Counted by brute force", r["brute_force"] if r["brute_force"] is not None else "too many to list")
    st.dataframe(pd.DataFrame(r["terms"]).rename(columns={"k": "k", "term": "Term", "value": "Value"}),
                 hide_index=True, width="stretch")


def _tab_primes():
    st.subheader("Primes up to n by crossing out multiples")
    n = st.slider("n", 2, 1000, 100, key="ie_pn")
    r = ie.prime_sieve_steps(n)
    if _show_errors(r):
        return
    a, b, c = st.columns(3)
    a.metric("Crossed out", len(r["crossed"]))
    b.metric("Crossed out by inclusion-exclusion", r["ie_union"])
    c.metric("Primes found", f"{r['prime_count']} (standard sieve: {r['plain_prime_count']})")
    steps = [{"Prime": s["prime"], "Newly crossed": len(s["newly_crossed"]),
              "Crossed so far": s["crossed_total"], "Left": s["survivors"]} for s in r["steps"]]
    st.dataframe(pd.DataFrame(steps), hide_index=True, width="stretch")
    with st.expander("Inclusion-exclusion terms"):
        st.dataframe(pd.DataFrame(r["ie_terms"]).rename(columns={"size": "Sets", "term": "Term", "value": "Value"}),
                     hide_index=True, width="stretch")
    st.caption("Left after crossing out multiples of 2, 3, 5, 7: the number 1 and every prime up to n. "
               + ("The counts agree." if r["match"] else "The counts differ."))
    with st.expander("Primes found"):
        st.write(", ".join(str(x) for x in r["survivors"] if x > 1))


def _tab_phi():
    st.subheader("Euler's φ: step sizes that visit every inspection slot")
    n = st.slider("Slots on the ring (n)", 2, 64, 12, key="ie_phin")
    r = ie.phi_ring(n)
    if _show_errors(r):
        return
    a, b, c = st.columns(3)
    a.metric("Step sizes visiting every slot", r["phi_count"])
    b.metric("φ(n) from the formula", r["phi_formula"])
    c.metric("Agree", "Yes" if r["match"] else "No")
    st.write("Step sizes that work: " + ", ".join(str(s) for s in r["coprime_steps"]))
    st.code("\n".join(r["formula_steps"]))
    rows = [{"Step": s["s"], "gcd(step, n)": s["gcd"], "Visits all slots": "Yes" if s["visits_all"] else "No",
             "Slots in one lap": s["cycle_len"], "Separate laps": s["cycles"]} for s in r["steps"]]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def render_inclusion_exclusion_page() -> None:
    page_header("Inclusion–Exclusion",
                "Count a union without counting anything twice, then use the same idea on "
                "derangements, onto functions, primes and Euler's φ.")
    df = st.session_state.get("buildings")
    if df is None or len(df) == 0:
        st.info("Add buildings on Campus Data to start.")
        return
    t = st.tabs(["Campus sets", "Derangements", "Onto functions", "Primes", "Euler's φ"])
    with t[0]:
        _tab_campus(df)
    with t[1]:
        _tab_derangements()
    with t[2]:
        _tab_onto()
    with t[3]:
        _tab_primes()
    with t[4]:
        _tab_phi()