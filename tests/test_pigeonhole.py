"""
test_pigeonhole.py — Tests for algorithms/pigeonhole.py.
"""

import pytest
from algorithms.pigeonhole import (
    pigeonhole, generalized_pigeonhole, campus_pigeonhole_demo,
    ramsey_r33_brute_force, mantel_theorem, erdos_szekeres_demo,
)


class TestPigeonhole:
    def test_basic(self):
        r = pigeonhole(10, 3)
        assert r["guaranteed"] == 4   # ceil(10/3)
        assert r["errors"] == []

    def test_exact_division(self):
        r = pigeonhole(9, 3)
        assert r["guaranteed"] == 3

    def test_n_equals_m(self):
        r = pigeonhole(5, 5)
        assert r["guaranteed"] == 1

    def test_invalid_zero_boxes(self):
        assert pigeonhole(5, 0)["errors"]

    def test_invalid_zero_items(self):
        assert pigeonhole(0, 3)["errors"]


class TestGeneralizedPigeonhole:
    def test_formula_matches_ceil(self):
        import math
        for n in range(1, 20):
            for m in range(1, 10):
                r = generalized_pigeonhole(n, m)
                assert r["guaranteed"] == math.ceil(n / m)

    def test_min_for_t(self):
        r = generalized_pigeonhole(10, 3)
        # To guarantee t=2: need 3*(2-1)+1 = 4 items
        assert r["min_for_t"][2] == 4


class TestCampusPigeonholeDemo:
    def test_basic(self):
        solars = [10.0, 30.0, 50.0, 70.0, 90.0]
        r = campus_pigeonhole_demo(solars, n_bands=3)
        assert r["errors"] == []
        assert r["guaranteed"] == 2   # ceil(5/3)
        assert r["actual_max"] >= r["guaranteed"]

    def test_empty(self):
        assert campus_pigeonhole_demo([])["errors"]

    def test_invalid_bands(self):
        assert campus_pigeonhole_demo([50.0], n_bands=0)["errors"]


class TestRamseyR33:
    def test_k5_has_good_coloring(self):
        r = ramsey_r33_brute_force()
        assert r["k5_has_good_coloring"] is True

    def test_k6_all_have_mono_triangle(self):
        r = ramsey_r33_brute_force()
        assert r["k6_all_have_mono_triangle"] is True

    def test_conclusion_mentions_r33(self):
        r = ramsey_r33_brute_force()
        assert "R(3,3)" in r["conclusion"] or "6" in r["conclusion"]


class TestMantelTheorem:
    @pytest.mark.parametrize("n,expected", [
        (2, 1),
        (3, 2),
        (4, 4),
        (5, 6),
        (6, 9),
    ])
    def test_mantel_bound(self, n, expected):
        r = mantel_theorem(n)
        assert r["errors"] == []
        assert r["mantel_bound"] == expected

    def test_brute_force_matches_formula(self):
        for n in range(2, 7):
            r = mantel_theorem(n)
            assert r["match"] is True, f"n={n}: mantel={r['mantel_bound']}, brute={r['brute_force_max']}"

    def test_mantel_n5_eq_6(self):
        r = mantel_theorem(5)
        assert r["mantel_bound"] == 6
        assert r["brute_force_max"] == 6

    def test_invalid_range(self):
        assert mantel_theorem(7)["errors"]
        assert mantel_theorem(1)["errors"]


class TestErdosSzekeres:
    def test_basic(self):
        seq = [3, 1, 4, 2]   # n=4 → guarantee=2
        r = erdos_szekeres_demo(seq)
        assert r["errors"] == []
        assert r["actual_max"] >= r["guarantee"]

    def test_theorem_satisfied(self):
        # k=3, k^2+1=10; guarantee=3
        import random
        random.seed(42)
        seq = random.sample(range(1, 50), 10)
        r = erdos_szekeres_demo(seq)
        assert r["theorem_satisfied"] is True

    def test_increasing_sequence(self):
        seq = list(range(1, 6))
        r = erdos_szekeres_demo(seq)
        assert len(r["lis"]) == 5

    def test_decreasing_sequence(self):
        seq = list(range(5, 0, -1))
        r = erdos_szekeres_demo(seq)
        assert len(r["lds"]) == 5

    def test_duplicate_error(self):
        r = erdos_szekeres_demo([1, 1, 2])
        assert r["errors"]

    def test_too_short_error(self):
        r = erdos_szekeres_demo([1])
        assert r["errors"]
