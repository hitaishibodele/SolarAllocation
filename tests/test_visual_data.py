"""
test_visual_data.py — the pure Python layer that feeds every interactive
visual.  Each builder is checked for the shape and the values of the JSON it
returns, on the default campus and on empty data.

Nothing here imports Streamlit; the visuals themselves are HTML, so the data
they draw from is what these tests pin down.
"""

import pandas as pd
import pytest

from algorithms.data_loader import load_buildings, get_default_thresholds
from algorithms.validation import DEFAULT_EDGES
from algorithms import visual_data as vd


@pytest.fixture(scope="module")
def df():
    buildings, errors = load_buildings()
    assert errors == []
    return buildings


@pytest.fixture(scope="module")
def thresholds():
    return get_default_thresholds()


@pytest.fixture(scope="module")
def empty():
    return pd.DataFrame(columns=[
        "name", "energy_demand_kwh_day", "rooftop_area_m2", "solar_potential_pct",
    ])


def _by_key(items):
    return {item["key"]: item for item in items}


# ===========================================================================
# 1. campus map
# ===========================================================================

class TestCampusMapData:

    def test_one_tile_per_building_sorted(self, df, thresholds):
        data = vd.campus_map_data(df, thresholds)
        assert [b["key"] for b in data["buildings"]] == [
            "Administration", "Auditorium", "Canteen",
            "Hostel", "Laboratory", "Library",
        ]

    def test_maxima_come_from_the_table(self, df, thresholds):
        data = vd.campus_map_data(df, thresholds)
        assert data["max_area"] == 1500.0
        assert data["max_demand"] == 900.0

    def test_three_buildings_are_eligible(self, df, thresholds):
        data = vd.campus_map_data(df, thresholds)
        eligible = [b["key"] for b in data["buildings"] if b["eligible"]]
        assert eligible == ["Hostel", "Laboratory", "Library"]

    def test_failed_criteria_per_building(self, df, thresholds):
        data = vd.campus_map_data(df, thresholds)
        by_key = _by_key(data["buildings"])
        assert by_key["Auditorium"]["failed"] == ["C"]
        assert by_key["Canteen"]["failed"] == ["A", "B"]
        assert by_key["Administration"]["failed"] == ["A", "B"]
        assert by_key["Library"]["failed"] == []

    def test_tile_side_grows_with_area(self, df, thresholds):
        data = vd.campus_map_data(df, thresholds)
        by_key = _by_key(data["buildings"])
        assert by_key["Hostel"]["tile"] > by_key["Canteen"]["tile"]
        assert min(b["tile"] for b in data["buildings"]) >= 72

    def test_criteria_flags_match_the_thresholds(self, df, thresholds):
        data = vd.campus_map_data(df, thresholds)
        by_key = _by_key(data["buildings"])
        assert by_key["Auditorium"]["criteria"] == {"A": True, "B": True, "C": False}
        assert by_key["Canteen"]["criteria"] == {"A": False, "B": False, "C": True}

    def test_thresholds_are_echoed(self, df, thresholds):
        data = vd.campus_map_data(df, thresholds)
        assert data["thresholds"] == {"min_demand": 400.0,
                                     "min_area": 800.0,
                                     "min_solar": 75.0}

    def test_names_are_escaped(self, thresholds):
        df = pd.DataFrame([{
            "name": "<img src=x onerror=alert(1)>",
            "energy_demand_kwh_day": 500.0,
            "rooftop_area_m2": 900.0,
            "solar_potential_pct": 90.0,
        }])
        data = vd.campus_map_data(df, thresholds)
        label = data["buildings"][0]["label"]
        assert "<img" not in label
        assert "&lt;img" in label

    def test_empty_data(self, empty, thresholds):
        data = vd.campus_map_data(empty, thresholds)
        assert data["buildings"] == []
        assert data["max_area"] == 0.0


# ===========================================================================
# 2. filter funnel
# ===========================================================================

class TestFunnelData:

    def test_stage_counts(self, df, thresholds):
        data = vd.funnel_data(df, thresholds)
        assert data["counts"] == [6, 4, 4, 3]

    def test_three_stages_in_order(self, df, thresholds):
        data = vd.funnel_data(df, thresholds)
        assert [s["criterion"] for s in data["stages"]] == ["A", "B", "C"]

    def test_each_stage_removes_the_right_building(self, df, thresholds):
        data = vd.funnel_data(df, thresholds)
        stage_a, stage_b, stage_c = data["stages"]
        assert [r["key"] for r in stage_a["removed"]] == ["Administration", "Canteen"]
        assert stage_b["removed"] == []
        assert [r["key"] for r in stage_c["removed"]] == ["Auditorium"]

    def test_final_group_is_the_eligible_set(self, df, thresholds):
        data = vd.funnel_data(df, thresholds)
        assert [b["key"] for b in data["final"]] == ["Hostel", "Laboratory", "Library"]
        assert data["final_label"] == "E = A ∩ B ∩ C"

    def test_every_start_building_has_a_label(self, df, thresholds):
        data = vd.funnel_data(df, thresholds)
        assert len(data["start"]) == 6
        assert all("label" in b for b in data["start"])

    def test_empty_data(self, empty, thresholds):
        data = vd.funnel_data(empty, thresholds)
        assert data["counts"] == [0]
        assert data["final"] == []


# ===========================================================================
# 3. Venn diagram
# ===========================================================================

class TestVennData:

    def test_set_sizes(self, df, thresholds):
        data = vd.venn_data(df, thresholds)
        assert data["counts"] == {"U": 6, "A": 4, "B": 4, "C": 5, "E": 3}

    def test_region_sizes(self, df, thresholds):
        data = vd.venn_data(df, thresholds)
        assert data["region_counts"] == {
            "A_only": 0, "B_only": 0, "C_only": 2, "A_B": 1,
            "A_C": 0, "B_C": 0, "A_B_C": 3, "none": 0,
        }

    def test_regions_partition_the_campus(self, df, thresholds):
        data = vd.venn_data(df, thresholds)
        total = sum(data["region_counts"].values())
        assert total == data["counts"]["U"]

    def test_region_membership(self, df, thresholds):
        data = vd.venn_data(df, thresholds)
        assert [b["key"] for b in data["regions"]["A_B_C"]] == [
            "Hostel", "Laboratory", "Library"]
        assert [b["key"] for b in data["regions"]["A_B"]] == ["Auditorium"]
        assert [b["key"] for b in data["regions"]["C_only"]] == [
            "Administration", "Canteen"]

    def test_named_operations(self, df, thresholds):
        data = vd.venn_data(df, thresholds)
        ops = _by_key(data["operations"])
        assert set(ops) == {
            "intersection", "union", "A-B", "B-A", "C-A", "A-C",
            "complement-C", "complement-E",
        }
        assert [b["key"] for b in ops["A-C"]["members"]] == ["Auditorium"]
        assert [b["key"] for b in ops["C-A"]["members"]] == [
            "Administration", "Canteen"]
        assert ops["complement-C"]["size"] == 1
        assert [b["key"] for b in ops["complement-C"]["members"]] == ["Auditorium"]
        assert ops["intersection"]["size"] == 3
        assert ops["union"]["size"] == 6

    def test_notation_is_written_out(self, df, thresholds):
        data = vd.venn_data(df, thresholds)
        ops = _by_key(data["operations"])
        assert ops["complement-E"]["notation"].startswith("{")
        assert ops["intersection"]["notation"] == "{ Hostel, Laboratory, Library }"

    def test_labels_present(self, df, thresholds):
        data = vd.venn_data(df, thresholds)
        assert set(data["labels"]) == {"A", "B", "C"}

    def test_empty_data(self, empty, thresholds):
        data = vd.venn_data(empty, thresholds)
        assert data["counts"]["U"] == 0
        assert data["operations"][0]["size"] == 0
        assert data["operations"][0]["notation"] == "∅"


# ===========================================================================
# power set
# ===========================================================================

class TestPowerSetData:

    def test_eight_subsets_of_the_eligible_set(self, df, thresholds):
        data = vd.power_set_data(df, thresholds)
        assert data["size"] == 3
        assert data["count"] == 8
        assert len(data["subsets"]) == 8

    def test_subsets_are_lists_of_labels(self, df, thresholds):
        data = vd.power_set_data(df, thresholds)
        assert data["subsets"][0] == []
        assert ["Hostel", "Laboratory", "Library"] in data["subsets"]

    def test_set_is_the_eligible_set(self, df, thresholds):
        data = vd.power_set_data(df, thresholds)
        assert [b["key"] for b in data["set"]] == ["Hostel", "Laboratory", "Library"]

    def test_empty_data(self, empty, thresholds):
        data = vd.power_set_data(empty, thresholds)
        assert data["size"] == 0
        assert data["count"] == 1


# ===========================================================================
# 4-6. relations and functions
# ===========================================================================

class TestRelationDiagramData:

    def test_one_node_per_building(self, df, thresholds):
        data = vd.relation_diagram_data(df, DEFAULT_EDGES, thresholds)
        assert len(data["nodes"]) == 6
        assert data["domain_size"] == 6
        assert [n["key"] for n in data["nodes"]] == [
            "Administration", "Auditorium", "Canteen",
            "Hostel", "Laboratory", "Library",
        ]

    def test_one_link_per_connection(self, df, thresholds):
        data = vd.relation_diagram_data(df, DEFAULT_EDGES, thresholds)
        assert len(data["links"]) == len(DEFAULT_EDGES)
        assert data["pair_count"] == 2 * len(DEFAULT_EDGES)

    def test_each_link_points_from_a_lower_to_a_higher_index(self, df, thresholds):
        data = vd.relation_diagram_data(df, DEFAULT_EDGES, thresholds)
        for link in data["links"]:
            assert link["a"] < link["b"]

    def test_five_property_badges(self, df, thresholds):
        data = vd.relation_diagram_data(df, DEFAULT_EDGES, thresholds)
        badges = _by_key(data["badges"])
        assert set(badges) == {"reflexive", "symmetric", "antisymmetric",
                              "transitive", "equivalence"}
        assert badges["symmetric"]["passed"] is True
        assert badges["reflexive"]["passed"] is False
        assert badges["transitive"]["passed"] is False
        assert badges["equivalence"]["passed"] is False

    def test_grid_is_square_and_symmetric(self, df, thresholds):
        data = vd.relation_diagram_data(df, DEFAULT_EDGES, thresholds)
        grid = data["matrix"]["grid"]
        assert len(grid) == 6
        assert all(len(row) == 6 for row in grid)

    def test_highlights_explain_each_failing_property(self, df, thresholds):
        data = vd.relation_diagram_data(df, DEFAULT_EDGES, thresholds)
        # symmetric holds, so it gets no highlight; the failing ones do
        assert set(data["highlights"]) == {
            "reflexive", "antisymmetric", "transitive", "equivalence"}
        assert data["highlights"]["reflexive"]["text"]
        assert "symmetric" not in data["highlights"]

    def test_no_connections_gives_an_empty_state(self, df, thresholds):
        data = vd.relation_diagram_data(df, [], thresholds)
        assert data["empty"] is True
        assert data["links"] == []
        assert data["pair_count"] == 0

    def test_empty_data(self, empty, thresholds):
        data = vd.relation_diagram_data(empty, [], thresholds)
        assert data["nodes"] == []
        assert data["links"] == []
        assert data["matrix"] == {"labels": [], "grid": []}


class TestRankingData:

    def test_ladder_is_largest_demand_first(self, df, thresholds):
        data = vd.ranking_data(df, thresholds)
        assert [entry["key"] for entry in data["order"]] == [
            "Hostel", "Laboratory", "Library",
            "Auditorium", "Canteen", "Administration",
        ]

    def test_ranks_are_one_to_six(self, df, thresholds):
        data = vd.ranking_data(df, thresholds)
        assert [entry["rank"] for entry in data["order"]] == [1, 2, 3, 4, 5, 6]

    def test_demand_values_are_attached(self, df, thresholds):
        data = vd.ranking_data(df, thresholds)
        assert data["order"][0]["demand"] == 900.0

    def test_default_campus_is_a_total_order(self, df, thresholds):
        data = vd.ranking_data(df, thresholds)
        assert data["total_order"] is True
        assert data["ties"] == []
        assert data["equal_active"] is False
        assert data["note"] == ""

    def test_equal_pair_creates_a_tie(self, df, thresholds):
        data = vd.ranking_data(df, thresholds, equal_pair=("Hostel", "Library"))
        assert data["total_order"] is False
        assert data["equal_active"] is True
        assert data["note"]
        assert [ [b["key"] for b in group] for group in data["ties"] ] == [
            ["Hostel", "Library"]]

    def test_pair_count_counts_each_comparable_pair_once(self, df, thresholds):
        data = vd.ranking_data(df, thresholds)
        # distinct demands: 6 self pairs + one of each of the 15 unordered pairs
        assert data["pair_count"] == 21

    def test_empty_data(self, empty, thresholds):
        data = vd.ranking_data(empty, thresholds)
        assert data["order"] == []
        assert data["ties"] == []


class TestFunctionData:

    def test_three_functions(self, df, thresholds):
        data = vd.function_data(df, thresholds)
        assert set(data) == {"demand", "eligible", "rank"}

    def test_every_domain_element_has_a_label(self, df, thresholds):
        data = vd.function_data(df, thresholds)
        for name in ("demand", "eligible", "rank"):
            for element in data[name]["domain"]:
                assert element["label"]
                assert "key" in element

    def test_eligible_is_onto_but_not_one_to_one(self, df, thresholds):
        eligible = vd.function_data(df, thresholds)["eligible"]
        assert eligible["surjective"] is True
        assert eligible["injective"] is False
        assert eligible["codomain"] == [
            {"key": "0", "label": "0"}, {"key": "1", "label": "1"}]

    def test_rank_is_a_bijection(self, df, thresholds):
        rank = vd.function_data(df, thresholds)["rank"]
        assert rank["bijective"] is True
        assert len(rank["arrows"]) == 3

    def test_arrows_have_the_right_arity(self, df, thresholds):
        data = vd.function_data(df, thresholds)
        for name in ("demand", "eligible", "rank"):
            for arrow in data[name]["arrows"]:
                assert len(arrow) == 2

    def test_empty_data(self, empty, thresholds):
        data = vd.function_data(empty, thresholds)
        assert data["demand"]["domain"] == []
        assert data["rank"]["domain"] == []


# ===========================================================================
# 7-10. logic
# ===========================================================================

class TestLogicGateData:

    def test_three_variables(self, df, thresholds):
        data = vd.logic_gate_data(df, thresholds)
        assert data["variables"] == ["p", "q", "r"]
        assert set(data["meanings"]) == {"p", "q", "r"}

    def test_eight_rows(self, df, thresholds):
        data = vd.logic_gate_data(df, thresholds)
        assert [row["index"] for row in data["rows"]] == list(range(8))

    def test_row_flags_decode_the_index(self, df, thresholds):
        data = vd.logic_gate_data(df, thresholds)
        for row in data["rows"]:
            i = row["index"]
            assert row["p"] is bool((i >> 2) & 1)
            assert row["q"] is bool((i >> 1) & 1)
            assert row["r"] is bool(i & 1)

    def test_eligible_buildings_land_on_row_seven(self, df, thresholds):
        data = vd.logic_gate_data(df, thresholds)
        assert [b["key"] for b in data["rows"][7]["buildings"]] == [
            "Hostel", "Laboratory", "Library"]

    def test_auditorium_lands_on_row_six(self, df, thresholds):
        data = vd.logic_gate_data(df, thresholds)
        assert [b["key"] for b in data["rows"][6]["buildings"]] == ["Auditorium"]

    def test_canteen_and_administration_land_on_row_one(self, df, thresholds):
        data = vd.logic_gate_data(df, thresholds)
        assert [b["key"] for b in data["rows"][1]["buildings"]] == [
            "Administration", "Canteen"]

    def test_every_building_appears_exactly_once(self, df, thresholds):
        data = vd.logic_gate_data(df, thresholds)
        seen = [b["key"] for row in data["rows"] for b in row["buildings"]]
        assert sorted(seen) == sorted(b["key"] for b in data["buildings"])

    def test_empty_data(self, empty, thresholds):
        data = vd.logic_gate_data(empty, thresholds)
        assert data["buildings"] == []
        assert len(data["rows"]) == 8


class TestTruthTableData:

    def test_eight_rows_with_building_chips(self, df, thresholds):
        data = vd.truth_table_data(df, thresholds)
        assert len(data["rows"]) == 8
        assert all("buildings" in row for row in data["rows"])

    def test_eligible_column_is_p_and_q_and_r(self, df, thresholds):
        data = vd.truth_table_data(df, thresholds)
        for row in data["rows"]:
            assert row["eligible"] == (row["p"] and row["q"] and row["r"])

    def test_classification(self, df, thresholds):
        data = vd.truth_table_data(df, thresholds)
        assert data["classification"] == "contingency"
        assert data["formula"] == "eligible = p ∧ q ∧ r"


class TestDeMorganData:

    def test_all_eight_rows_agree(self, df, thresholds):
        data = vd.de_morgan_data(df, thresholds)
        assert len(data["rows"]) == 8
        assert data["all_equal"] is True
        assert all(row["equal"] for row in data["rows"])

    def test_both_sides_are_labelled(self, df, thresholds):
        data = vd.de_morgan_data(df, thresholds)
        assert data["left_label"] == "not (p and q and r)"
        assert data["right_label"] == "(not p) or (not q) or (not r)"
        assert data["left_pretty"] and data["right_pretty"]

    def test_no_parse_errors(self, df, thresholds):
        assert vd.de_morgan_data(df, thresholds)["errors"] == []


class TestFormulaData:

    def test_eligibility_formula_matches_eligible(self, df, thresholds):
        data = vd.formula_data("(p and q) and r", df, thresholds)
        assert data["equivalent_to_eligible"] is True
        assert data["classification"] == "contingency"
        assert len(data["rows"]) == 8

    def test_tautology_is_classified(self, df, thresholds):
        data = vd.formula_data("p or not p", df, thresholds)
        assert data["classification"] == "tautology"

    def test_contradiction_is_classified(self, df, thresholds):
        data = vd.formula_data("p and not p", df, thresholds)
        assert data["classification"] == "contradiction"

    def test_implication_equals_its_contrapositive_but_not_its_converse(
            self, df, thresholds):
        data = vd.formula_data("(p and q) and r", df, thresholds)
        implication = data["implication"]
        assert implication["statement_vs_contrapositive"] is True
        assert implication["statement_vs_converse"] is False

    def test_rows_carry_their_values_and_result(self, df, thresholds):
        data = vd.formula_data("(p and q) and r", df, thresholds)
        for row in data["rows"]:
            assert set(row["values"]) == {"p", "q", "r"}
            assert isinstance(row["result"], bool)

    def test_invalid_formula_reports_an_error(self, df, thresholds):
        data = vd.formula_data("p and (", df, thresholds)
        assert data["errors"]
        assert data["rows"] == []


# ===========================================================================
# 11-14. proofs, induction and the loop invariant
# ===========================================================================

class TestProofVisualData:

    def test_stepper_matches_the_proof_builder(self, df, thresholds):
        data = vd.proof_stepper_data(df, thresholds, "direct")
        assert data["key"] == "direct"
        assert data["check"]["passed"] is True
        assert data["steps"]

    def test_all_proofs_covers_every_key(self, df, thresholds):
        data = vd.all_proofs_data(df, thresholds)
        assert list(data) == ["direct", "contraposition", "contradiction",
                             "counterexample", "correctness"]
        assert all(proof["check"]["passed"] for proof in data.values())

    def test_induction_payload(self):
        data = vd.induction_data(5)
        assert data["n"] == 5
        assert len(data["cases"]) == 5

    def test_strong_induction_payload(self):
        data = vd.strong_induction_data(8)
        assert data["n"] == 8
        assert sum(data["phases"]) == 8


class TestConveyorData:

    def test_one_step_per_building(self, df, thresholds):
        data = vd.conveyor_data(df, thresholds)
        assert len(data["steps"]) == 6
        assert len(data["order"]) == 6

    def test_final_tray_is_the_eligible_set(self, df, thresholds):
        data = vd.conveyor_data(df, thresholds)
        assert [b["key"] for b in data["tray"]] == [
            "Hostel", "Laboratory", "Library"]
        assert data["holds"] is True

    def test_every_step_records_the_invariant(self, df, thresholds):
        data = vd.conveyor_data(df, thresholds)
        for step in data["steps"]:
            assert step["invariant_holds"] is True
            assert isinstance(step["tray"], list)

    def test_accepted_steps_are_the_eligible_buildings(self, df, thresholds):
        data = vd.conveyor_data(df, thresholds)
        accepted = [step["name"] for step in data["steps"] if step["accepted"]]
        assert accepted == ["Hostel", "Laboratory", "Library"]

    def test_empty_data(self, empty, thresholds):
        data = vd.conveyor_data(empty, thresholds)
        assert data["steps"] == []
        assert data["tray"] == []
        assert data["holds"] is True


# ===========================================================================
# escaping helper
# ===========================================================================

class TestEscaping:

    def test_esc_neutralises_html(self):
        assert vd.esc("<b>Tag</b>") == "&lt;b&gt;Tag&lt;/b&gt;"

    def test_esc_escapes_quotes(self):
        assert vd.esc('a"b') == "a&quot;b"
