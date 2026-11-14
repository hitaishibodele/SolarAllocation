"""
test_functions.py — the three functions defined on the campus buildings.

  * demand   : building -> daily demand
  * eligible : building -> 1 or 0
  * rank     : eligible building -> its position 1..|E|

Nothing here imports Streamlit.
"""

import pandas as pd
import pytest

from algorithms.data_loader import load_buildings, get_default_thresholds
from algorithms.functions import (
    demand_function,
    eligible_function,
    rank_function,
    function_overview,
)
from algorithms.set_theory import build_sets, eligible_set


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


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "name", "energy_demand_kwh_day", "rooftop_area_m2", "solar_potential_pct",
    ])


# ---------------------------------------------------------------------------
# demand
# ---------------------------------------------------------------------------

class TestDemandFunction:

    def test_domain_is_every_building(self, df):
        assert demand_function(df)["domain"] == [
            "Administration", "Auditorium", "Canteen",
            "Hostel", "Laboratory", "Library",
        ]

    def test_every_building_has_exactly_one_arrow(self, df):
        info = demand_function(df)
        assert len(info["arrows"]) == len(info["domain"]) == 6

    def test_arrow_values_match_the_table(self, df):
        info = demand_function(df)
        by_name = {name: value for name, value in info["arrows"]}
        assert by_name["Hostel"] == 900.0
        assert by_name["Library"] == 500.0

    def test_codomain_contains_every_image(self, df):
        info = demand_function(df)
        images = {value for _n, value in info["arrows"]}
        assert images <= set(info["codomain"])
        assert info["missing"] == []

    def test_distinct_demands_make_it_one_to_one(self, df):
        info = demand_function(df)
        assert info["valid"] is True
        assert info["injective"] is True
        assert info["surjective"] is True

    def test_empty_frame_is_handled(self):
        info = demand_function(_empty())
        assert info["domain"] == []
        assert info["arrows"] == []


# ---------------------------------------------------------------------------
# eligible
# ---------------------------------------------------------------------------

class TestEligibleFunction:

    def test_codomain_is_zero_and_one(self, df, thresholds):
        assert eligible_function(df, thresholds)["codomain"] == ["0", "1"]

    def test_eligible_buildings_map_to_one(self, df, thresholds, eligible_names):
        info = eligible_function(df, thresholds)
        by_name = {name: value for name, value in info["arrows"]}
        for name in eligible_names:
            assert by_name[name] == "1"
        assert sorted(n for n, v in by_name.items() if v == "1") == sorted(eligible_names)

    def test_it_is_onto(self, df, thresholds):
        assert eligible_function(df, thresholds)["surjective"] is True

    def test_it_is_not_one_to_one(self, df, thresholds):
        info = eligible_function(df, thresholds)
        assert info["injective"] is False
        assert info["bijective"] is False

    def test_it_is_a_valid_function(self, df, thresholds):
        assert eligible_function(df, thresholds)["valid"] is True

    def test_empty_frame_is_handled(self, thresholds):
        info = eligible_function(_empty(), thresholds)
        assert info["domain"] == []
        assert info["arrows"] == []


# ---------------------------------------------------------------------------
# rank
# ---------------------------------------------------------------------------

class TestRankFunction:

    def test_domain_is_the_eligible_set(self, df, thresholds, eligible_names):
        assert sorted(rank_function(df, thresholds)["domain"]) == sorted(eligible_names)

    def test_codomain_is_one_to_the_size(self, df, thresholds, eligible_names):
        info = rank_function(df, thresholds)
        assert info["codomain"] == list(range(1, len(eligible_names) + 1))

    def test_it_is_a_bijection(self, df, thresholds):
        info = rank_function(df, thresholds)
        assert info["injective"] is True
        assert info["surjective"] is True
        assert info["bijective"] is True

    def test_highest_demand_gets_rank_one(self, df, thresholds):
        info = rank_function(df, thresholds)
        by_name = {name: rank for name, rank in info["arrows"]}
        assert by_name["Hostel"] == 1
        assert by_name["Laboratory"] == 2
        assert by_name["Library"] == 3

    def test_ranks_are_all_different(self, df, thresholds):
        ranks = [rank for _n, rank in rank_function(df, thresholds)["arrows"]]
        assert len(ranks) == len(set(ranks))

    def test_no_eligible_building_is_handled(self, df):
        info = rank_function(df, {"min_demand": 10_000.0,
                                  "min_area": 10_000.0,
                                  "min_solar": 100.0})
        assert info["domain"] == []
        assert info["codomain"] == []

    def test_empty_frame_is_handled(self, thresholds):
        assert rank_function(_empty(), thresholds)["domain"] == []


# ---------------------------------------------------------------------------
# overview
# ---------------------------------------------------------------------------

class TestFunctionOverview:

    def test_three_functions_returned(self, df, thresholds):
        overview = function_overview(df, thresholds)
        assert set(overview) == {"demand", "eligible", "rank"}
        for info in overview.values():
            assert info["name"] in {"demand", "eligible", "rank"}
            assert isinstance(info["valid"], bool)

    def test_empty_frame_still_returns_three_functions(self, thresholds):
        overview = function_overview(_empty(), thresholds)
        assert set(overview) == {"demand", "eligible", "rank"}
