"""
test_logic.py — Tests for algorithms/logic.py.
"""

import pytest
from algorithms.logic import (
    parse_formula, evaluate_formula, truth_table, classify_formula,
    check_equivalence, relation_properties, function_properties,
    induction_verify, factor_tree, INDUCTION_FORMULAS,
)


# ===========================================================================
# Parser and evaluator
# ===========================================================================

class TestParseAndEvaluate:
    def test_simple_and(self):
        assert evaluate_formula("p and q", {"p": True, "q": True}) is True
        assert evaluate_formula("p and q", {"p": True, "q": False}) is False

    def test_implies(self):
        # p → q is False only when p=T, q=F
        assert evaluate_formula("p implies q", {"p": True, "q": False}) is False
        assert evaluate_formula("p implies q", {"p": False, "q": False}) is True

    def test_iff(self):
        assert evaluate_formula("p iff q", {"p": True, "q": True}) is True
        assert evaluate_formula("p iff q", {"p": True, "q": False}) is False

    def test_xor(self):
        assert evaluate_formula("p xor q", {"p": True, "q": True}) is False
        assert evaluate_formula("p xor q", {"p": True, "q": False}) is True

    def test_not(self):
        assert evaluate_formula("not p", {"p": True}) is False
        assert evaluate_formula("not p", {"p": False}) is True

    def test_parentheses(self):
        assert evaluate_formula("(p or q) and r", {"p": False, "q": True, "r": True}) is True

    def test_unicode_operators(self):
        assert evaluate_formula("p ∧ q", {"p": True, "q": True}) is True
        assert evaluate_formula("p → q", {"p": True, "q": False}) is False
        assert evaluate_formula("¬p", {"p": True}) is False

    def test_parse_error_returns_parse_error(self):
        from algorithms.logic import ParseError
        with pytest.raises(ParseError):
            parse_formula("p and and q")

    def test_parse_error_empty(self):
        from algorithms.logic import ParseError
        with pytest.raises(ParseError):
            parse_formula("")

    def test_constant_true_false(self):
        assert evaluate_formula("T", {}) is True
        assert evaluate_formula("F", {}) is False


# ===========================================================================
# Truth table
# ===========================================================================

class TestTruthTable:
    def test_two_variables(self):
        result = truth_table("p and q")
        assert result["errors"] == []
        assert len(result["rows"]) == 4
        assert result["variables"] == ["p", "q"]

    def test_correct_values_implies(self):
        result = truth_table("p implies q")
        assert result["errors"] == []
        # p=T,q=F → False; all others True
        false_rows = [r for r in result["rows"] if not r["result"]]
        assert len(false_rows) == 1
        assert false_rows[0]["p"] is True and false_rows[0]["q"] is False


# ===========================================================================
# Classification
# ===========================================================================

class TestClassifyFormula:
    def test_tautology_p_or_not_p(self):
        r = classify_formula("p or not p")
        assert r["classification"] == "tautology"
        assert r["all_true"] is True

    def test_contradiction_p_and_not_p(self):
        r = classify_formula("p and not p")
        assert r["classification"] == "contradiction"
        assert r["all_false"] is True

    def test_contingency_p(self):
        r = classify_formula("p")
        assert r["classification"] == "contingency"

    def test_tautology_implies_contrapositive(self):
        # (p→q) ↔ (¬q→¬p) is a tautology
        r = classify_formula("(p implies q) iff (not q implies not p)")
        assert r["classification"] == "tautology"


# ===========================================================================
# Equivalence
# ===========================================================================

class TestEquivalence:
    def test_p_implies_q_equiv_not_p_or_q(self):
        r = check_equivalence("p implies q", "not p or q")
        assert r["equivalent"] is True
        assert r["counterexample"] is None

    def test_p_and_q_not_equiv_p_or_q(self):
        r = check_equivalence("p and q", "p or q")
        assert r["equivalent"] is False
        assert r["counterexample"] is not None

    def test_de_morgan_and(self):
        # ¬(p∧q) ≡ ¬p∨¬q
        r = check_equivalence("not (p and q)", "not p or not q")
        assert r["equivalent"] is True

    def test_contrapositive(self):
        r = check_equivalence("p implies q", "not q implies not p")
        assert r["equivalent"] is True


# ===========================================================================
# Relation properties
# ===========================================================================

class TestRelationProperties:
    def _identity_relation(self):
        return [(1,1),(2,2),(3,3)]

    def test_identity_reflexive(self):
        r = relation_properties(self._identity_relation(), [1,2,3])
        assert r["reflexive"] is True

    def test_identity_symmetric(self):
        r = relation_properties(self._identity_relation(), [1,2,3])
        assert r["symmetric"] is True

    def test_identity_antisymmetric(self):
        r = relation_properties(self._identity_relation(), [1,2,3])
        assert r["antisymmetric"] is True

    def test_identity_transitive(self):
        r = relation_properties(self._identity_relation(), [1,2,3])
        assert r["transitive"] is True

    def test_identity_is_equivalence_and_partial_order(self):
        r = relation_properties(self._identity_relation(), [1,2,3])
        assert r["equivalence"] is True
        assert r["partial_order"] is True

    def test_not_reflexive(self):
        r = relation_properties([(1,2),(2,1)], [1,2,3])
        assert r["reflexive"] is False
        assert r["counterexamples"]["reflexive"] is not None

    def test_not_symmetric_counterexample(self):
        # {(1,2)} — not symmetric (missing (2,1))
        r = relation_properties([(1,2)], [1,2])
        assert r["symmetric"] is False
        ce = r["counterexamples"]["symmetric"]
        assert ce is not None

    def test_not_transitive_counterexample(self):
        # {(1,2),(2,3)} — not transitive (missing (1,3))
        r = relation_properties([(1,2),(2,3)], [1,2,3])
        assert r["transitive"] is False

    def test_equivalence_relation(self):
        # Modular 2: {(1,1),(2,2),(3,3),(1,3),(3,1)}
        r = relation_properties([(1,1),(2,2),(3,3),(1,3),(3,1)], [1,2,3])
        assert r["equivalence"] is True

    def test_partial_order_le(self):
        # ≤ on {1,2,3}
        r = relation_properties(
            [(1,1),(2,2),(3,3),(1,2),(1,3),(2,3)], [1,2,3]
        )
        assert r["partial_order"] is True
        assert r["antisymmetric"] is True

    def test_empty_domain(self):
        r = relation_properties([], [])
        assert r["reflexive"] is True  # vacuously

    def test_domain_too_large_error(self):
        r = relation_properties([], list(range(11)))
        assert r["errors"]


# ===========================================================================
# Function properties
# ===========================================================================

class TestFunctionProperties:
    def test_bijection(self):
        r = function_properties(
            [("1","a"),("2","b"),("3","c")],
            ["1","2","3"], ["a","b","c"]
        )
        assert r["valid"] is True
        assert r["injective"] is True
        assert r["surjective"] is True
        assert r["bijective"] is True

    def test_not_injective(self):
        r = function_properties(
            [("1","a"),("2","a"),("3","c")],
            ["1","2","3"], ["a","b","c"]
        )
        assert r["injective"] is False
        assert r["surjective"] is False

    def test_not_surjective(self):
        r = function_properties(
            [("1","a"),("2","b")],
            ["1","2"], ["a","b","c"]
        )
        assert r["surjective"] is False

    def test_invalid_not_a_function(self):
        # 1 maps to both a and b
        r = function_properties(
            [("1","a"),("1","b"),("2","c")],
            ["1","2"], ["a","b","c"]
        )
        assert r["valid"] is False
        assert r["errors"]

    def test_empty_mapping(self):
        r = function_properties([], ["1"], ["a"])
        assert r["valid"] is False


# ===========================================================================
# Induction
# ===========================================================================

class TestInduction:
    @pytest.mark.parametrize("name", list(INDUCTION_FORMULAS.keys()))
    def test_all_formulas_hold_for_n10(self, name):
        r = induction_verify(name, 10)
        assert r["errors"] == []
        assert r["base_case"]["holds"] is True
        assert all(v["holds"] for v in r["verification"])

    def test_invalid_formula_name(self):
        r = induction_verify("nonexistent", 5)
        assert r["errors"]

    def test_n_max_out_of_range(self):
        r = induction_verify("sum_n", 0)
        assert r["errors"]

    def test_sum_n_base_case(self):
        r = induction_verify("sum_n", 1)
        assert r["base_case"]["lhs"] == r["base_case"]["rhs"]


# ===========================================================================
# Factor tree
# ===========================================================================

class TestFactorTree:
    def test_prime(self):
        r = factor_tree(7)
        assert r["errors"] == []
        assert r["factors"] == [7]

    def test_composite(self):
        r = factor_tree(60)
        assert r["errors"] == []
        assert sorted(r["factors"]) == [2, 2, 3, 5]
        product = 1
        for f in r["factors"]:
            product *= f
        assert product == 60

    def test_power_of_2(self):
        r = factor_tree(8)
        assert r["factors"] == [2, 2, 2]

    def test_out_of_range(self):
        r = factor_tree(1)
        assert r["errors"]
        r2 = factor_tree(10001)
        assert r2["errors"]
