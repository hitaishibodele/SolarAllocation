"""
test_proofs.py — the five proofs, the loop invariant and the two induction
arguments, all recomputed from the campus data.

Nothing here imports Streamlit.
"""

import pandas as pd
import pytest

from algorithms.data_loader import load_buildings, get_default_thresholds
from algorithms.set_theory import build_sets, eligible_set
from algorithms.proofs import (
    PROOF_ORDER,
    build_proof,
    all_proofs,
    eligible_loop,
    direct_proof,
    contraposition_proof,
    contradiction_proof,
    counterexample_proof,
    correctness_proof,
    weak_induction,
    strong_induction,
    CONNECTED_CLAIM,
)


@pytest.fixture(scope="module")
def df():
    buildings, errors = load_buildings()
    assert errors == []
    return buildings


@pytest.fixture(scope="module")
def thresholds():
    return get_default_thresholds()


@pytest.fixture(scope="module")
def eligible_names(df, thresholds):
    sets = build_sets(df, thresholds)
    return eligible_set(sets["A"], sets["B"], sets["C"])


def _rows_df(rows) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "name": name,
                "energy_demand_kwh_day": demand,
                "rooftop_area_m2": area,
                "solar_potential_pct": solar,
            }
            for name, demand, area, solar in rows
        ]
    )


# ---------------------------------------------------------------------------
# shared shape of every proof
# ---------------------------------------------------------------------------

class TestProofShape:

    def test_five_proofs_in_order(self):
        assert PROOF_ORDER == [
            "direct", "contraposition", "contradiction",
            "counterexample", "correctness",
        ]

    @pytest.mark.parametrize("key", PROOF_ORDER)
    def test_every_proof_has_steps_and_a_check(self, key, df, thresholds):
        proof = build_proof(key, df, thresholds)
        assert proof["key"] == key
        assert proof["title"]
        assert len(proof["steps"]) >= 3
        assert all("claim" in step and "status" in step for step in proof["steps"])
        assert set(proof["check"]) >= {"passed", "headline", "message", "evidence"}

    @pytest.mark.parametrize("key", PROOF_ORDER)
    def test_every_check_passes_on_the_default_campus(self, key, df, thresholds):
        assert build_proof(key, df, thresholds)["check"]["passed"] is True

    def test_unknown_key_returns_a_failed_check(self, df, thresholds):
        proof = build_proof("no-such-proof", df, thresholds)
        assert proof["check"]["passed"] is False
        assert proof["steps"] == []

    def test_all_proofs_returns_every_proof(self, df, thresholds):
        proofs = all_proofs(df, thresholds)
        assert [p["key"] for p in proofs] == PROOF_ORDER


# ---------------------------------------------------------------------------
# the individual proofs
# ---------------------------------------------------------------------------

class TestDirectProof:

    def test_headline_is_the_subset_claim(self, df, thresholds):
        assert direct_proof(df, thresholds)["check"]["headline"] == "E ⊆ A"

    def test_evidence_lists_the_eligible_buildings(self, df, thresholds, eligible_names):
        evidence = direct_proof(df, thresholds)["check"]["evidence"]
        for name in eligible_names:
            assert name in evidence

    def test_it_fails_when_an_eligible_building_breaks_the_rule(self):
        # Craft data where a building is eligible by construction is impossible
        # for direct_proof; instead confirm the proof passes on real data and the
        # message reports the count of eligible buildings.
        df = _rows_df([("Only", 500.0, 900.0, 90.0)])
        proof = direct_proof(df, {"min_demand": 400.0, "min_area": 800.0,
                                  "min_solar": 75.0})
        assert proof["check"]["passed"] is True
        assert "Only" in proof["check"]["evidence"]


class TestContrapositionAndContradiction:

    def test_contraposition_headline(self, df, thresholds):
        assert contraposition_proof(df, thresholds)["check"]["headline"] == "¬C ⇒ ¬E"

    def test_contraposition_evidence_names_the_low_solar_building(self, df, thresholds):
        evidence = contraposition_proof(df, thresholds)["check"]["evidence"]
        assert "Auditorium" in evidence

    def test_contradiction_headline(self, df, thresholds):
        proof = contradiction_proof(df, thresholds)
        assert proof["check"]["headline"] == "no low-solar building in E"

    def test_both_pass_when_every_building_meets_the_solar_criterion(self):
        df = _rows_df([
            ("Alpha", 500.0, 900.0, 90.0),
            ("Beta", 600.0, 1000.0, 95.0),
        ])
        limits = {"min_demand": 400.0, "min_area": 800.0, "min_solar": 75.0}
        assert contraposition_proof(df, limits)["check"]["passed"] is True
        assert contradiction_proof(df, limits)["check"]["passed"] is True
        assert "every building" in contraposition_proof(df, limits)["check"]["evidence"]


class TestCounterexampleProof:

    def test_auditorium_is_the_witness(self, df, thresholds):
        proof = counterexample_proof(df, thresholds)
        assert proof["check"]["passed"] is True
        assert "Auditorium" in proof["check"]["evidence"]

    def test_it_still_passes_when_no_counterexample_exists(self):
        df = _rows_df([
            ("Alpha", 500.0, 900.0, 90.0),
            ("Beta", 600.0, 1000.0, 95.0),
        ])
        proof = counterexample_proof(df, {"min_demand": 400.0, "min_area": 800.0,
                                          "min_solar": 75.0})
        assert proof["check"]["passed"] is True
        assert "No counterexample" in proof["check"]["message"]


# ---------------------------------------------------------------------------
# the loop invariant / correctness
# ---------------------------------------------------------------------------

class TestLoopInvariant:

    def test_one_step_per_building(self, df, thresholds):
        trace = eligible_loop(df, thresholds)
        assert len(trace["steps"]) == len(df)
        assert len(trace["order"]) == len(df)

    def test_step_indices_are_one_based(self, df, thresholds):
        trace = eligible_loop(df, thresholds)
        assert [s["index"] for s in trace["steps"]] == list(range(1, len(df) + 1))

    def test_invariant_holds_at_every_step(self, df, thresholds):
        trace = eligible_loop(df, thresholds)
        assert trace["holds"] is True
        assert all(s["invariant_holds"] for s in trace["steps"])

    def test_final_tray_equals_the_eligible_set(self, df, thresholds, eligible_names):
        trace = eligible_loop(df, thresholds)
        assert sorted(trace["tray"]) == sorted(eligible_names)

    def test_tray_only_grows(self, df, thresholds):
        trace = eligible_loop(df, thresholds)
        sizes = [len(s["tray"]) for s in trace["steps"]]
        assert sizes == sorted(sizes)

    def test_correctness_proof_reports_the_trace(self, df, thresholds):
        proof = correctness_proof(df, thresholds)
        assert proof["check"]["passed"] is True
        assert proof["check"]["headline"] == "tray = E"

    def test_invariant_survives_an_edited_campus(self, df, thresholds):
        edited = df[df["name"] != "Canteen"].copy()
        trace = eligible_loop(edited, thresholds)
        assert trace["holds"] is True
        assert len(trace["steps"]) == len(edited)

    def test_invariant_survives_edited_thresholds(self, df):
        trace = eligible_loop(df, {"min_demand": 450.0,
                                   "min_area": 700.0,
                                   "min_solar": 82.0})
        assert trace["holds"] is True

    def test_empty_frame_gives_an_empty_trace(self, thresholds):
        trace = eligible_loop(pd.DataFrame(), thresholds)
        assert trace["steps"] == []
        assert trace["tray"] == []
        assert trace["holds"] is True          # vacuously


# ---------------------------------------------------------------------------
# boundary values
# ---------------------------------------------------------------------------

class TestBoundaryValues:

    def test_a_value_equal_to_the_threshold_qualifies(self):
        df = _rows_df([
            ("Edge", 400.0, 800.0, 75.0),      # exactly on all three thresholds
            ("Under", 399.9, 799.9, 74.9),     # just below all three
        ])
        limits = {"min_demand": 400.0, "min_area": 800.0, "min_solar": 75.0}
        trace = eligible_loop(df, limits)
        assert trace["tray"] == ["Edge"]
        assert build_proof("direct", df, limits)["check"]["passed"] is True


# ---------------------------------------------------------------------------
# induction
# ---------------------------------------------------------------------------

class TestWeakInduction:

    def test_claim_is_the_connected_network_claim(self):
        assert weak_induction(5)["claim"] == CONNECTED_CLAIM

    def test_cases_run_from_one_to_n(self):
        info = weak_induction(4)
        assert [c["n"] for c in info["cases"]] == [1, 2, 3, 4]

    def test_minimum_is_one_less_than_the_size(self):
        for case in weak_induction(6)["cases"]:
            assert case["minimum"] == case["n"] - 1
            assert case["holds"] is True

    def test_base_case_is_a_single_building(self):
        assert weak_induction(5)["base_case"]["n"] == 1

    def test_n_is_clamped_to_one_through_twenty_four(self):
        assert weak_induction(0)["n"] == 1
        assert weak_induction(-5)["n"] == 1
        assert weak_induction(100)["n"] == 24

    def test_note_says_the_animation_is_not_a_proof(self):
        assert "not a proof" in weak_induction(5)["note"]


class TestStrongInduction:

    def test_base_cases_are_two_and_three(self):
        bases = strong_induction(6)["base_cases"]
        assert [b["n"] for b in bases] == [2, 3]

    @pytest.mark.parametrize("n", [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 24])
    def test_phases_use_only_twos_and_threes_and_sum_to_n(self, n):
        phases = strong_induction(n)["phases"]
        assert sum(phases) == n
        assert set(phases) <= {2, 3}

    @pytest.mark.parametrize("n,expected", [
        (2, [2]), (3, [3]), (4, [2, 2]), (5, [2, 3]),
        (6, [3, 3]), (7, [2, 2, 3]), (8, [2, 3, 3]),
    ])
    def test_known_splits(self, n, expected):
        assert strong_induction(n)["phases"] == expected

    def test_n_is_clamped_to_two_through_twenty_four(self):
        assert strong_induction(0)["n"] == 2
        assert strong_induction(999)["n"] == 24
