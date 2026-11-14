"""
test_dm_project.py — Test suite for Sustainable Solar Energy Allocation.

Tests cover:
  * validation (buildings, thresholds, edges — unordered name pairs)
  * set_theory (universal set, predicates, intersection, operations)
  * network (graph construction, adjacency matrix, degree table,
             degree-sum check, connected components, cycle detection,
             is_connected, is_tree — default 3-building triangle graph)
  * analysis (truth table, De Morgan checks, inclusion-exclusion)
  * stats (campus_stats, chart_data)
  * data_loader (loads the default buildings table)

No Streamlit imports; a connection is a plain unordered pair of building names.
"""

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

BUILDINGS_DICT = {
    "name":                  ["Library", "Laboratory", "Hostel", "Canteen"],
    "energy_demand_kwh_day": [500.0,     700.0,        900.0,    350.0],
    "rooftop_area_m2":       [1200.0,    800.0,        1500.0,   600.0],
    "solar_potential_pct":   [90.0,      85.0,         80.0,     75.0],
}

# Default thresholds: Library, Laboratory, Hostel pass (A∩B∩C); Canteen fails.
THRESHOLDS = {"min_demand": 400.0, "min_area": 800.0, "min_solar": 75.0}


@pytest.fixture
def df():
    return pd.DataFrame(BUILDINGS_DICT)


@pytest.fixture
def thresholds():
    return THRESHOLDS.copy()


# ---------------------------------------------------------------------------
# 1.  validation.py
# ---------------------------------------------------------------------------

class TestValidateBuildings:
    from algorithms.validation import validate_buildings

    def test_valid_df_accepted(self, df):
        from algorithms.validation import validate_buildings
        clean, errors = validate_buildings(df)
        assert errors == []
        assert len(clean) == 4

    def test_not_dataframe_returns_empty(self):
        from algorithms.validation import validate_buildings
        clean, errors = validate_buildings([1, 2, 3])
        assert len(errors) == 1
        assert clean.empty

    def test_missing_column_error(self, df):
        from algorithms.validation import validate_buildings
        bad = df.drop(columns=["rooftop_area_m2"])
        clean, errors = validate_buildings(bad)
        assert any("Missing required column" in e for e in errors)
        assert clean.empty

    def test_blank_name_excluded(self, df):
        from algorithms.validation import validate_buildings
        bad = df.copy()
        bad.loc[0, "name"] = "  "
        clean, errors = validate_buildings(bad)
        assert any("blank" in e for e in errors)
        assert len(clean) == 3

    def test_duplicate_name_excluded(self, df):
        from algorithms.validation import validate_buildings
        bad = df.copy()
        bad.loc[3, "name"] = "Library"  # duplicate of row 0
        clean, errors = validate_buildings(bad)
        assert any("duplicate" in e.lower() for e in errors)
        assert len(clean) == 3

    def test_non_numeric_excluded(self, df):
        from algorithms.validation import validate_buildings
        bad = df.astype({"energy_demand_kwh_day": "object"})
        bad.loc[0, "energy_demand_kwh_day"] = "not-a-number"
        clean, errors = validate_buildings(bad)
        assert any("not a valid number" in e for e in errors)
        assert len(clean) == 3

    def test_no_cost_column_in_schema(self):
        from algorithms.validation import REQUIRED_COLUMNS
        assert not any("cost" in c.lower() for c in REQUIRED_COLUMNS)
        assert not any("inr" in c.lower() for c in REQUIRED_COLUMNS)


class TestValidateThresholds:
    def test_valid_thresholds(self):
        from algorithms.validation import validate_thresholds
        clean, errors = validate_thresholds({"min_demand": 400.0, "min_area": 800.0, "min_solar": 75.0})
        assert errors == []
        assert clean["min_demand"] == 400.0

    def test_negative_clipped_to_default(self):
        from algorithms.validation import validate_thresholds, DEFAULT_THRESHOLDS
        clean, errors = validate_thresholds({"min_demand": -1.0, "min_area": 800.0, "min_solar": 75.0})
        # negative value → falls back to the default (400.0), NOT clipped to 0
        assert clean["min_demand"] == DEFAULT_THRESHOLDS["min_demand"]
        assert any("min_demand" in e for e in errors)

    def test_missing_key_gets_default(self):
        from algorithms.validation import validate_thresholds, DEFAULT_THRESHOLDS
        clean, errors = validate_thresholds({})
        for key in DEFAULT_THRESHOLDS:
            assert key in clean


class TestValidateEdges:
    """Name-pair validation — the primary new behaviour."""

    NAMES = ["Hostel", "Laboratory", "Library"]

    def _ve(self, edges):
        from algorithms.validation import validate_edges
        return validate_edges(edges, self.NAMES)

    def test_valid_pair_accepted(self):
        clean, errors = self._ve([("Hostel", "Library")])
        assert errors == []
        assert len(clean) == 1
        u, v = clean[0]
        assert u < v          # canonical order
        assert len(clean[0]) == 2   # a connection is an unordered pair

    def test_canonical_order_u_less_v(self):
        clean, errors = self._ve([("Library", "Hostel")])
        assert errors == []
        u, v = clean[0]
        assert u == "Hostel"
        assert v == "Library"

    def test_unknown_building_rejected(self):
        clean, errors = self._ve([("Hostel", "Unknown")])
        assert len(errors) == 1
        assert "not found" in errors[0]
        assert clean == []

    def test_self_loop_rejected(self):
        clean, errors = self._ve([("Hostel", "Hostel")])
        assert len(errors) == 1
        assert "self-loop" in errors[0]
        assert clean == []

    def test_duplicate_ab_ba_rejected(self):
        """A-B and B-A are the same undirected edge; second must be skipped."""
        clean, errors = self._ve([
            ("Hostel", "Library"),
            ("Library", "Hostel"),
        ])
        assert len(clean) == 1
        assert len(errors) == 1
        assert "duplicate" in errors[0].lower()

    def test_three_valid_distinct_pairs(self):
        clean, errors = self._ve([
            ("Hostel", "Laboratory"),
            ("Hostel", "Library"),
            ("Laboratory", "Library"),
        ])
        assert errors == []
        assert len(clean) == 3

    def test_none_input_returns_empty(self):
        clean, errors = self._ve(None)
        assert clean == []
        assert errors == []


# ---------------------------------------------------------------------------
# 2.  set_theory.py
# ---------------------------------------------------------------------------

class TestSetTheory:
    def test_universal_set_all_names(self, df):
        from algorithms.set_theory import universal_set
        U = universal_set(df)
        assert U == {"Library", "Laboratory", "Hostel", "Canteen"}

    def test_universal_set_empty_df(self):
        from algorithms.set_theory import universal_set
        assert universal_set(pd.DataFrame()) == set()

    def test_set_a_high_demand(self, df, thresholds):
        from algorithms.set_theory import build_sets
        sets = build_sets(df, thresholds)
        # demand >= 400: Library(500), Laboratory(700), Hostel(900)
        assert sets["A"] == {"Library", "Laboratory", "Hostel"}

    def test_set_b_large_area(self, df, thresholds):
        from algorithms.set_theory import build_sets
        sets = build_sets(df, thresholds)
        # area >= 800: Library(1200), Laboratory(800), Hostel(1500)
        assert sets["B"] == {"Library", "Laboratory", "Hostel"}

    def test_set_c_good_solar(self, df, thresholds):
        from algorithms.set_theory import build_sets
        sets = build_sets(df, thresholds)
        # solar >= 75: Library(90), Laboratory(85), Hostel(80), Canteen(75)
        assert sets["C"] == {"Library", "Laboratory", "Hostel", "Canteen"}

    def test_eligible_set_intersection(self, df, thresholds):
        from algorithms.set_theory import build_sets, eligible_set
        sets = build_sets(df, thresholds)
        E = eligible_set(sets["A"], sets["B"], sets["C"])
        assert E == {"Library", "Laboratory", "Hostel"}

    def test_eligible_set_empty_when_none_pass(self, df):
        from algorithms.set_theory import build_sets, eligible_set
        # demand threshold far above all values
        t = {"min_demand": 9999.0, "min_area": 0.0, "min_solar": 0.0}
        sets = build_sets(df, t)
        E = eligible_set(sets["A"], sets["B"], sets["C"])
        assert E == set()

    def test_complement(self, df, thresholds):
        from algorithms.set_theory import build_sets, set_operations_summary
        s = set_operations_summary(df, thresholds)
        assert s["A'"] == s["U"] - s["A"]

    def test_de_morgan_union(self, df, thresholds):
        from algorithms.set_theory import build_sets
        from algorithms.analysis import de_morgan_checks
        sets = build_sets(df, thresholds)
        checks = de_morgan_checks(sets["A"], sets["B"], sets["C"], sets["U"])
        assert all(c["holds"] for c in checks)

    def test_venn_regions_partition_u(self, df, thresholds):
        from algorithms.set_theory import build_sets, venn_regions
        sets = build_sets(df, thresholds)
        regions = venn_regions(sets["A"], sets["B"], sets["C"], sets["U"])
        union_of_regions = set()
        for s in regions.values():
            union_of_regions |= s
        assert union_of_regions == sets["U"]

    def test_classification_table_columns(self, df, thresholds):
        from algorithms.set_theory import classification_table
        ct = classification_table(df, thresholds)
        for col in ["Building", "In A", "In B", "In C", "Eligible"]:
            assert col in ct.columns


# ---------------------------------------------------------------------------
# 3.  network.py — default triangle graph (Hostel, Laboratory, Library)
# ---------------------------------------------------------------------------

# Default edges: all three pairs connected → triangle (cycle present).
DEFAULT_VERTS = ["Hostel", "Laboratory", "Library"]
DEFAULT_EDGES = [
    ("Hostel",     "Laboratory"),
    ("Hostel",     "Library"),
    ("Laboratory", "Library"),
]


class TestNetworkDefault:
    """Verify the specified Graph Theory facts for the default graph."""

    def test_vertices_count(self):
        from algorithms.network import build_network
        net = build_network(DEFAULT_VERTS, DEFAULT_EDGES)
        assert len(net["vertices"]) == 3

    def test_edge_count(self):
        from algorithms.network import build_network
        net = build_network(DEFAULT_VERTS, DEFAULT_EDGES)
        assert len(net["edges"]) == 3

    def test_is_connected(self):
        from algorithms.network import is_connected
        assert is_connected(DEFAULT_VERTS, DEFAULT_EDGES) is True

    def test_has_cycle(self):
        from algorithms.network import has_cycle
        assert has_cycle(DEFAULT_VERTS, DEFAULT_EDGES) is True

    def test_is_not_tree(self):
        """Connected + cycle → not a tree."""
        from algorithms.network import is_connected, has_cycle
        conn  = is_connected(DEFAULT_VERTS, DEFAULT_EDGES)
        cycle = has_cycle(DEFAULT_VERTS, DEFAULT_EDGES)
        is_tree = conn and not cycle
        assert is_tree is False

    def test_degree_sum_equals_2_times_edges(self):
        """Degree-sum theorem: Σ deg = 2 × |E| = 6 for the triangle."""
        from algorithms.network import degree_table
        deg = degree_table(DEFAULT_VERTS, DEFAULT_EDGES)
        total_deg = int(deg["degree"].sum())
        assert total_deg == 2 * len(DEFAULT_EDGES)   # 6 == 2×3
        assert total_deg == 6

    def test_each_vertex_degree_2(self):
        """In a triangle every vertex has degree 2."""
        from algorithms.network import degree_table
        deg = degree_table(DEFAULT_VERTS, DEFAULT_EDGES)
        for _, row in deg.iterrows():
            assert row["degree"] == 2

    def test_single_component(self):
        from algorithms.network import connected_components
        comps = connected_components(DEFAULT_VERTS, DEFAULT_EDGES)
        assert len(comps) == 1


class TestAdjacencyMatrix:
    def test_symmetric(self):
        from algorithms.network import adjacency_matrix
        adj = adjacency_matrix(DEFAULT_VERTS, DEFAULT_EDGES)
        assert (adj.values == adj.T.values).all()

    def test_diagonal_zero(self):
        from algorithms.network import adjacency_matrix
        adj = adjacency_matrix(DEFAULT_VERTS, DEFAULT_EDGES)
        for name in DEFAULT_VERTS:
            assert adj.at[name, name] == 0

    def test_entries_0_or_1(self):
        from algorithms.network import adjacency_matrix
        adj = adjacency_matrix(DEFAULT_VERTS, DEFAULT_EDGES)
        unique_vals = set(adj.values.flatten().tolist())
        assert unique_vals.issubset({0, 1})

    def test_triangle_entries(self):
        """All three off-diagonal pairs should be 1 in a triangle."""
        from algorithms.network import adjacency_matrix
        adj = adjacency_matrix(DEFAULT_VERTS, DEFAULT_EDGES)
        for u in DEFAULT_VERTS:
            for v in DEFAULT_VERTS:
                if u != v:
                    assert adj.at[u, v] == 1


class TestNetworkEdgeCases:
    def test_empty_graph_not_cycle(self):
        from algorithms.network import has_cycle
        assert has_cycle([], []) is False

    def test_single_vertex_connected(self):
        from algorithms.network import is_connected
        assert is_connected(["A"], []) is True

    def test_two_verts_no_edge_disconnected(self):
        from algorithms.network import is_connected
        assert is_connected(["A", "B"], []) is False

    def test_two_verts_one_edge_connected(self):
        from algorithms.network import is_connected
        assert is_connected(["A", "B"], [("A", "B", 1.0)]) is True

    def test_path_graph_no_cycle(self):
        """A-B-C with no B-A edge is acyclic."""
        from algorithms.network import has_cycle
        verts = ["A", "B", "C"]
        edges = [("A", "B", 1.0), ("B", "C", 1.0)]
        assert has_cycle(verts, edges) is False

    def test_path_graph_is_tree(self):
        from algorithms.network import has_cycle, is_connected
        verts = ["A", "B", "C"]
        edges = [("A", "B", 1.0), ("B", "C", 1.0)]
        assert is_connected(verts, edges) and not has_cycle(verts, edges)

    def test_ineligible_endpoint_dropped(self):
        from algorithms.network import build_network
        verts = ["A", "B"]
        edges = [("A", "C", 1.0)]  # C not eligible
        net = build_network(verts, edges)
        assert len(net["edges"]) == 0
        assert len(net["dropped"]) == 1

    def test_adjacency_values_are_zero_or_one(self):
        """Adjacency matrix must be 0/1 integers."""
        from algorithms.network import adjacency_matrix
        adj = adjacency_matrix(DEFAULT_VERTS, DEFAULT_EDGES)
        for val in adj.values.flatten():
            assert val in (0, 1), f"Unexpected value {val}"

    def test_two_components(self):
        from algorithms.network import connected_components
        verts = ["A", "B", "C", "D"]
        edges = [("A", "B", 1.0), ("C", "D", 1.0)]
        comps = connected_components(verts, edges)
        assert len(comps) == 2


# ---------------------------------------------------------------------------
# 4.  analysis.py
# ---------------------------------------------------------------------------

class TestAnalysis:
    def test_truth_table_has_8_rows(self, df, thresholds):
        from algorithms.analysis import truth_table
        tt = truth_table(df, thresholds)
        assert len(tt) == 8

    def test_truth_table_eligible_row_all_true(self, df, thresholds):
        from algorithms.analysis import truth_table
        tt = truth_table(df, thresholds)
        eligible_row = tt[tt["Eligible"] == True]
        assert not eligible_row.empty
        assert bool(eligible_row.iloc[0]["In A"])
        assert bool(eligible_row.iloc[0]["In B"])
        assert bool(eligible_row.iloc[0]["In C"])

    def test_truth_table_counts_sum_to_total(self, df, thresholds):
        from algorithms.analysis import truth_table
        tt = truth_table(df, thresholds)
        assert tt["Count"].sum() == len(df)

    def test_de_morgan_holds(self, df, thresholds):
        from algorithms.analysis import de_morgan_checks
        from algorithms.set_theory import build_sets
        sets = build_sets(df, thresholds)
        checks = de_morgan_checks(sets["A"], sets["B"], sets["C"], sets["U"])
        assert len(checks) == 2
        assert all(c["holds"] for c in checks)

    def test_inclusion_exclusion_holds(self, df, thresholds):
        from algorithms.analysis import inclusion_exclusion_check
        from algorithms.set_theory import build_sets
        sets = build_sets(df, thresholds)
        result = inclusion_exclusion_check(sets["A"], sets["B"], sets["C"])
        assert result["holds"]
        assert result["lhs"] == result["rhs"]

    def test_inclusion_exclusion_7_terms(self, df, thresholds):
        from algorithms.analysis import inclusion_exclusion_check
        from algorithms.set_theory import build_sets
        sets = build_sets(df, thresholds)
        result = inclusion_exclusion_check(sets["A"], sets["B"], sets["C"])
        assert len(result["terms"]) == 7


# ---------------------------------------------------------------------------
# 5.  stats.py
# ---------------------------------------------------------------------------

class TestStats:
    def test_total_buildings(self, df, thresholds):
        from algorithms.stats import campus_stats
        s = campus_stats(df, thresholds)
        assert s["total_buildings"] == 4

    def test_eligible_count(self, df, thresholds):
        from algorithms.stats import campus_stats
        s = campus_stats(df, thresholds)
        assert s["eligible_count"] == 3

    def test_excluded_count(self, df, thresholds):
        from algorithms.stats import campus_stats
        s = campus_stats(df, thresholds)
        assert s["excluded_count"] == 1  # Canteen

    def test_no_cost_key_in_stats(self, df, thresholds):
        from algorithms.stats import campus_stats
        s = campus_stats(df, thresholds)
        for key in s:
            assert "cost" not in key.lower()
            assert "inr" not in key.lower()
            assert "saving" not in key.lower()

    def test_empty_df_returns_zeros(self):
        from algorithms.stats import campus_stats
        s = campus_stats(pd.DataFrame(), {})
        assert s["total_buildings"] == 0
        assert s["eligible_count"] == 0

    def test_chart_data_columns(self, df, thresholds):
        from algorithms.stats import chart_data
        from algorithms.validation import COL_NAME, COL_DEMAND, COL_AREA, COL_SOLAR
        cd = chart_data(df, thresholds)
        for col in [COL_NAME, COL_DEMAND, COL_AREA, COL_SOLAR, "eligible"]:
            assert col in cd.columns
        assert "cost" not in cd.columns


# ---------------------------------------------------------------------------
# 6.  data_loader.py
# ---------------------------------------------------------------------------

class TestDataLoader:
    def test_loads_without_cost_column(self):
        from algorithms.data_loader import load_buildings
        df, errors = load_buildings()
        assert errors == [] or all("cost" not in e.lower() for e in errors)
        assert "install_cost_inr" not in df.columns
        assert len(df) > 0

    def test_required_columns_present(self):
        from algorithms.data_loader import load_buildings
        from algorithms.validation import REQUIRED_COLUMNS
        df, _ = load_buildings()
        for col in REQUIRED_COLUMNS:
            assert col in df.columns

    def test_default_edges_are_name_pairs(self):
        from algorithms.validation import DEFAULT_EDGES
        for edge in DEFAULT_EDGES:
            assert len(edge) == 2
            u, v = edge
            assert u != v
            assert u < v  # canonical u < v


# ---------------------------------------------------------------------------
# 7.  Degree-sum theorem standalone check
# ---------------------------------------------------------------------------

class TestDegreeSum:
    """Explicit checks for the Graph Theory page degree-sum fact."""

    def test_degree_sum_theorem_triangle(self):
        """Σ deg = 6 = 2 × 3 edges in the triangle."""
        from algorithms.network import degree_table
        deg = degree_table(DEFAULT_VERTS, DEFAULT_EDGES)
        assert int(deg["degree"].sum()) == 6
        assert int(deg["degree"].sum()) == 2 * len(DEFAULT_EDGES)

    def test_degree_sum_theorem_path(self):
        """Path A-B-C: degrees are 1, 2, 1; Σ=4=2×2."""
        from algorithms.network import degree_table
        verts = ["A", "B", "C"]
        edges = [("A", "B", 1.0), ("B", "C", 1.0)]
        deg = degree_table(verts, edges)
        assert int(deg["degree"].sum()) == 4
        assert int(deg["degree"].sum()) == 2 * len(edges)

    def test_degree_sum_empty_graph(self):
        from algorithms.network import degree_table
        deg = degree_table([], [])
        assert deg.empty or int(deg["degree"].sum()) == 0
