"""
test_counting.py — Tests for algorithms/counting.py.
"""

import math
import itertools
import pytest
from algorithms.counting import (
    factorial, permutations, combinations,
    permutations_with_repetition, combinations_with_repetition,
    stars_and_bars, pascal_triangle, campus_selections,
    verify_by_enumeration,
)


class TestFactorial:
    def test_zero(self):
        assert factorial(0) == 1

    def test_one(self):
        assert factorial(1) == 1

    def test_five(self):
        assert factorial(5) == 120

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            factorial(-1)


class TestPermutations:
    def test_p_5_3(self):
        assert permutations(5, 3)["value"] == 60

    def test_p_10_0(self):
        assert permutations(10, 0)["value"] == 1

    def test_p_n_n(self):
        assert permutations(5, 5)["value"] == 120

    def test_k_gt_n_error(self):
        assert permutations(3, 5)["errors"]

    def test_no_errors(self):
        assert permutations(10, 3)["errors"] == []


class TestCombinations:
    def test_c_10_3(self):
        assert combinations(10, 3)["value"] == 120

    def test_c_5_0(self):
        assert combinations(5, 0)["value"] == 1

    def test_c_n_n(self):
        assert combinations(7, 7)["value"] == 1

    def test_c_10_5(self):
        assert combinations(10, 5)["value"] == 252

    def test_symmetry(self):
        assert combinations(10, 3)["value"] == combinations(10, 7)["value"]

    def test_k_gt_n_error(self):
        assert combinations(3, 5)["errors"]

    def test_no_errors(self):
        assert combinations(10, 3)["errors"] == []


class TestPermutationsWithRepetition:
    def test_3_pow_2(self):
        assert permutations_with_repetition(3, 2)["value"] == 9

    def test_k_gt_n_allowed(self):
        r = permutations_with_repetition(2, 5)
        assert r["value"] == 32
        assert r["errors"] == []


class TestCombinationsWithRepetition:
    def test_multiset(self):
        # C(3+2-1,2) = C(4,2) = 6
        assert combinations_with_repetition(3, 2)["value"] == 6

    def test_k_gt_n_allowed(self):
        r = combinations_with_repetition(2, 5)
        assert r["errors"] == []


class TestStarsAndBars:
    def test_5_items_3_bins(self):
        # C(5+3-1,3-1) = C(7,2) = 21
        assert stars_and_bars(5, 3)["value"] == 21

    def test_0_items(self):
        assert stars_and_bars(0, 3)["value"] == 1  # C(2,2) = 1

    def test_invalid_k(self):
        assert stars_and_bars(5, 0)["errors"]


class TestPascalTriangle:
    def test_row_0(self):
        r = pascal_triangle(1)
        assert r["triangle"][0] == [1]

    def test_row_4(self):
        r = pascal_triangle(5)
        assert r["triangle"][4] == [1, 4, 6, 4, 1]

    def test_symmetry_identity(self):
        r = pascal_triangle(10)
        assert r["identity_checks"]["symmetry"]["holds"] is True

    def test_pascal_rule_identity(self):
        r = pascal_triangle(10)
        assert r["identity_checks"]["pascal_rule"]["holds"] is True

    def test_row_sum_identity(self):
        r = pascal_triangle(10)
        assert r["identity_checks"]["row_sum"]["holds"] is True

    def test_row_sum_values(self):
        r = pascal_triangle(6)
        for n, row in enumerate(r["triangle"]):
            assert sum(row) == 2 ** n

    def test_invalid_rows(self):
        assert pascal_triangle(0)["errors"]
        assert pascal_triangle(17)["errors"]

    def test_c_10_3_in_triangle(self):
        r = pascal_triangle(11)
        assert r["triangle"][10][3] == 120


class TestCampusSelections:
    def test_c_6_2(self):
        r = campus_selections(6, 2)
        assert r["unordered"] == 15
        assert r["ordered"] == 30

    def test_k_gt_n_error(self):
        r = campus_selections(3, 5)
        assert r["errors"]

    def test_k_0(self):
        r = campus_selections(6, 0)
        assert r["unordered"] == 1
        assert r["ordered"] == 1

    def test_enumeration_for_small(self):
        r = campus_selections(4, 2)
        assert r["enumeration"] is not None
        assert len(r["enumeration"]) == 6


class TestVerifyByEnumeration:
    @pytest.mark.parametrize("n,k", [(5,2),(6,3),(7,4),(8,3),(10,4)])
    def test_formula_matches_enum(self, n, k):
        r = verify_by_enumeration(n, k)
        assert r["errors"] == []
        assert r["comb_match"] is True
        assert r["perm_match"] is True

    def test_n_too_large(self):
        r = verify_by_enumeration(11, 2)
        assert r["errors"]
