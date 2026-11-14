"""
test_inclusion_exclusion.py — Tests for algorithms/inclusion_exclusion.py.
"""

import pytest
from algorithms.inclusion_exclusion import (
    ie_two_sets, ie_three_sets, derangements, onto_functions,
    primes_up_to, euler_phi,
)


class TestIETwoSets:
    def test_basic(self):
        A = {1, 2, 3, 4}
        B = {3, 4, 5, 6}
        r = ie_two_sets(A, B)
        assert r["lhs"] == r["rhs"] == 6
        assert r["holds"] is True

    def test_disjoint(self):
        r = ie_two_sets({1, 2}, {3, 4})
        assert r["lhs"] == 4
        assert r["holds"] is True

    def test_one_subset(self):
        r = ie_two_sets({1, 2}, {1, 2, 3})
        assert r["lhs"] == 3
        assert r["holds"] is True


class TestIEThreeSets:
    def test_basic(self):
        A = {1, 2, 3}
        B = {2, 3, 4}
        C = {3, 4, 5}
        r = ie_three_sets(A, B, C)
        assert r["lhs"] == r["rhs"]
        assert r["holds"] is True

    def test_empty_sets(self):
        r = ie_three_sets(set(), set(), set())
        assert r["lhs"] == 0
        assert r["holds"] is True

    def test_all_same(self):
        S = {1, 2, 3}
        r = ie_three_sets(S, S, S)
        assert r["lhs"] == 3
        assert r["holds"] is True

    def test_step_count(self):
        r = ie_three_sets({1}, {2}, {3})
        assert len(r["steps"]) == 7


class TestDerangements:
    # Known values
    @pytest.mark.parametrize("n,expected", [
        (0, 1),
        (1, 0),
        (2, 1),
        (3, 2),
        (4, 9),
        (5, 44),
        (6, 265),
    ])
    def test_known_values(self, n, expected):
        r = derangements(n)
        assert r["errors"] == []
        assert r["formula"] == expected
        assert r["recurrence"] == expected

    def test_brute_force_matches_formula_up_to_8(self):
        for n in range(9):
            r = derangements(n)
            assert r["brute_force"] == r["formula"]

    def test_invalid_negative(self):
        assert derangements(-1)["errors"]

    def test_invalid_large(self):
        assert derangements(13)["errors"]

    def test_d4_eq_9(self):
        assert derangements(4)["formula"] == 9

    def test_d5_eq_44(self):
        assert derangements(5)["formula"] == 44


class TestOntoFunctions:
    # onto(m, n) = surjective functions from m-set to n-set
    @pytest.mark.parametrize("m,n,expected", [
        (3, 2, 6),   # 2^3 - 2 = 6
        (4, 3, 36),  # known
        (2, 2, 2),   # 2! = 2
        (1, 1, 1),
    ])
    def test_known_values(self, m, n, expected):
        r = onto_functions(m, n)
        assert r["errors"] == []
        assert r["formula"] == expected

    def test_brute_force_matches_formula(self):
        for m in range(1, 5):
            for n in range(1, 5):
                r = onto_functions(m, n)
                if r["brute_force"] is not None:
                    assert r["formula"] == r["brute_force"], \
                        f"m={m},n={n}: formula={r['formula']}, brute={r['brute_force']}"

    def test_onto_4_to_3_is_36(self):
        assert onto_functions(4, 3)["formula"] == 36

    def test_invalid_m(self):
        assert onto_functions(0, 3)["errors"]

    def test_n_gt_m_gives_0(self):
        # No surjection from 2 elements to 3 elements
        assert onto_functions(2, 3)["formula"] == 0


class TestPrimesUpTo:
    def test_primes_up_to_100_count_25(self):
        r = primes_up_to(100)
        assert r["errors"] == []
        assert r["count"] == 25

    def test_primes_up_to_10(self):
        r = primes_up_to(10)
        assert r["primes"] == [2, 3, 5, 7]

    def test_primes_up_to_2(self):
        r = primes_up_to(2)
        assert r["primes"] == [2]

    def test_invalid_out_of_range(self):
        assert primes_up_to(1)["errors"]
        assert primes_up_to(1001)["errors"]


class TestEulerPhi:
    @pytest.mark.parametrize("n,expected", [
        (1, 1),
        (2, 1),
        (6, 2),
        (7, 6),
        (12, 4),
        (36, 12),
        (100, 40),
    ])
    def test_known_values(self, n, expected):
        r = euler_phi(n)
        assert r["errors"] == []
        assert r["phi_formula"] == expected

    def test_phi_36_eq_12(self):
        assert euler_phi(36)["phi_formula"] == 12

    def test_gcd_count_matches_formula(self):
        for n in range(1, 21):
            r = euler_phi(n)
            if r["phi_gcd"] is not None:
                assert r["phi_formula"] == r["phi_gcd"]

    def test_invalid_zero(self):
        assert euler_phi(0)["errors"]
