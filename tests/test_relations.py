"""
test_relations.py — the two relations built from the campus data.

  * "can be connected to"    — symmetric, not reflexive, not transitive
  * "has at least as much demand as" — a total order on the default campus

Nothing here imports Streamlit.
"""

import pytest

from algorithms.data_loader import load_buildings
from algorithms.data_loader import get_default_thresholds
from algorithms.validation import DEFAULT_EDGES
from algorithms.relations import (
    demand_values,
    domain_of,
    connect_relation,
    relation_matrix,
    demand_relation,
    ranking,
    rank_map,
    ties,
    demand_order_summary,
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
def relation(df):
    return connect_relation(DEFAULT_EDGES, domain_of(df))


# ---------------------------------------------------------------------------
# domain / demand values
# ---------------------------------------------------------------------------

class TestDomainAndDemand:

    def test_domain_is_every_building_sorted(self, df):
        assert domain_of(df) == [
            "Administration", "Auditorium", "Canteen",
            "Hostel", "Laboratory", "Library",
        ]

    def test_demand_values(self, df):
        values = demand_values(df)
        assert values["Hostel"] == 900.0
        assert values["Library"] == 500.0
        assert len(values) == 6

    def test_domain_of_empty_frame(self):
        import pandas as pd
        assert domain_of(pd.DataFrame()) == []
        assert demand_values(pd.DataFrame()) == {}


# ---------------------------------------------------------------------------
# "can be connected to"
# ---------------------------------------------------------------------------

class TestConnectRelation:

    def test_every_connection_appears_both_ways(self, relation):
        for a, b in relation:
            assert (b, a) in relation

    def test_no_self_pairs(self, relation):
        for a, b in relation:
            assert a != b

    def test_pair_count_is_twice_the_connections(self, relation):
        assert len(relation) == 2 * len(DEFAULT_EDGES)

    def test_unknown_endpoints_are_dropped(self, df):
        rel = connect_relation([("Hostel", "Nowhere")], domain_of(df))
        assert rel == []

    def test_relation_is_symmetric(self, relation, df):
        from algorithms.logic import relation_properties
        props = relation_properties(relation, domain_of(df))
        assert props["symmetric"] is True

    def test_relation_is_not_reflexive(self, relation, df):
        from algorithms.logic import relation_properties
        props = relation_properties(relation, domain_of(df))
        assert props["reflexive"] is False

    def test_relation_is_not_transitive(self, relation, df):
        from algorithms.logic import relation_properties
        props = relation_properties(relation, domain_of(df))
        assert props["transitive"] is False
        # Administration – Laboratory – Hostel, but no Administration – Hostel
        assert ("Administration", "Laboratory") in relation
        assert ("Laboratory", "Hostel") in relation
        assert ("Administration", "Hostel") not in relation

    def test_relation_is_not_an_equivalence(self, relation, df):
        from algorithms.logic import relation_properties
        props = relation_properties(relation, domain_of(df))
        assert props["equivalence"] is False

    def test_empty_edge_list_gives_empty_relation(self, df):
        assert connect_relation([], domain_of(df)) == []
        assert connect_relation(None, domain_of(df)) == []


# ---------------------------------------------------------------------------
# relation matrix
# ---------------------------------------------------------------------------

class TestRelationMatrix:

    def test_labels_are_the_sorted_domain(self, relation, df):
        matrix = relation_matrix(relation, domain_of(df))
        assert matrix["labels"] == sorted(domain_of(df))

    def test_grid_is_square(self, relation, df):
        matrix = relation_matrix(relation, domain_of(df))
        n = len(matrix["labels"])
        assert all(len(row) == n for row in matrix["grid"])
        assert len(matrix["grid"]) == n

    def test_grid_is_symmetric_with_zero_diagonal(self, relation, df):
        matrix = relation_matrix(relation, domain_of(df))
        grid = matrix["grid"]
        n = len(grid)
        for i in range(n):
            assert grid[i][i] == 0
            for j in range(n):
                assert grid[i][j] == grid[j][i]

    def test_entries_are_zero_or_one(self, relation, df):
        matrix = relation_matrix(relation, domain_of(df))
        for row in matrix["grid"]:
            for cell in row:
                assert cell in (0, 1)

    def test_ones_equal_the_ordered_pair_count(self, relation, df):
        matrix = relation_matrix(relation, domain_of(df))
        ones = sum(cell for row in matrix["grid"] for cell in row)
        assert ones == len(relation)


# ---------------------------------------------------------------------------
# "has at least as much demand as"
# ---------------------------------------------------------------------------

class TestDemandRelation:

    def test_ranking_is_largest_demand_first(self, df):
        assert ranking(df) == [
            "Hostel", "Laboratory", "Library",
            "Auditorium", "Canteen", "Administration",
        ]

    def test_three_named_buildings_in_order(self, df):
        order = ranking(df)
        assert order.index("Hostel") < order.index("Laboratory")
        assert order.index("Laboratory") < order.index("Library")

    def test_rank_map_is_one_based(self, df):
        ranks = rank_map(df)
        assert fields_ok(ranks)
        assert ranks["Hostel"] == 1
        assert max(ranks.values()) == len(df)

    def test_no_ties_on_the_default_campus(self, df):
        assert ties(df) == []
        assert demand_order_summary(df)["total_order"] is True

    def test_relation_holds_exactly_when_demand_is_at_least(self, df):
        values = demand_values(df)
        relation = demand_relation(df)
        for a in values:
            for b in values:
                assert ((a, b) in relation) == (values[a] >= values[b])

    def test_relation_contains_every_self_pair(self, df):
        relation = set(demand_relation(df))
        for name in demand_values(df):
            assert (name, name) in relation

    def test_summary_shape(self, df):
        summary = demand_order_summary(df)
        assert set(summary) == {"order", "ranks", "pairs", "ties", "total_order"}
        assert summary["order"] == ranking(df)
        # distinct demands: 6 self pairs + one of each of the 15 unordered pairs
        assert len(summary["pairs"]) == 21

    def test_tie_is_reported_when_two_demands_match(self, df):
        work = df.copy()
        work.loc[work["name"] == "Library", "energy_demand_kwh_day"] = 900.0
        assert ties(work) == [["Hostel", "Library"]]
        assert demand_order_summary(work)["total_order"] is False
        order = demand_order_summary(work)["order"]
        assert order[:2] == ["Hostel", "Library"]   # equal demand → alphabetical

    def test_empty_frame_is_handled(self):
        import pandas as pd
        empty = pd.DataFrame()
        assert ranking(empty) == []
        assert rank_map(empty) == {}
        assert ties(empty) == []
        assert demand_relation(empty) == []


def fields_ok(ranks) -> bool:
    """Every rank is a distinct 1-based integer."""
    values = sorted(ranks.values())
    return values == list(range(1, len(values) + 1))
