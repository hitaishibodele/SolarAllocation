"""
test_graph_algorithms.py — Tests for algorithms/graph_algorithms.py.
"""

import pytest
from algorithms.graph_algorithms import (
    adjacency_list, incidence_matrix, euler_check, hamiltonian_check,
    bipartite_check, graph_colouring, max_matching,
    planarity_bound_check, tree_check,
)


class TestAdjacencyList:
    def test_undirected_triangle(self):
        V = ["A","B","C"]
        E = [("A","B"),("B","C"),("A","C")]
        r = adjacency_list(V, E)
        assert set(r["A"]) == {"B","C"}
        assert set(r["B"]) == {"A","C"}

    def test_directed(self):
        V = ["A","B","C"]
        E = [("A","B"),("B","C")]
        r = adjacency_list(V, E, directed=True)
        assert "B" in r["A"]
        assert "A" not in r["B"]   # directed — no back edge

    def test_isolated_vertex(self):
        V = ["A","B","C"]
        E = [("A","B")]
        r = adjacency_list(V, E)
        assert r["C"] == []


class TestIncidenceMatrix:
    def test_column_sums_undirected(self):
        V = ["A","B","C"]
        E = [("A","B"),("B","C")]
        r = incidence_matrix(V, E)
        # Each column should sum to 2
        assert all(s == 2 for s in r["col_sums"])
        assert r["col_sum_check"] is True

    def test_row_sums_are_degrees(self):
        V = ["A","B","C"]
        E = [("A","B"),("B","C"),("A","C")]
        r = incidence_matrix(V, E)
        # Each vertex has degree 2
        assert all(s == 2 for s in r["row_sums"])


class TestEulerCheck:
    def test_euler_circuit_k4(self):
        # K3 has all even degrees (deg=2)
        V = ["A","B","C"]
        E = [("A","B"),("B","C"),("A","C")]
        r = euler_check(V, E)
        assert r["circuit_exists"] is True

    def test_no_euler_circuit_path_graph(self):
        # P3: A-B-C — 2 odd vertices (A and C)
        V = ["A","B","C"]
        E = [("A","B"),("B","C")]
        r = euler_check(V, E)
        assert r["circuit_exists"] is False
        assert r["path_exists"] is True

    def test_euler_path_exists(self):
        # K3 = Euler circuit → also has an Euler path
        V = ["A","B","C"]
        E = [("A","B"),("B","C"),("A","C")]
        r = euler_check(V, E)
        assert r["circuit_exists"] is True

    def test_disconnected_no_euler(self):
        V = ["A","B","C","D"]
        E = [("A","B"),("C","D")]
        r = euler_check(V, E)
        assert r["circuit_exists"] is False
        assert r["path_exists"] is False

    def test_circuit_valid(self):
        V = ["A","B","C","D"]
        E = [("A","B"),("B","C"),("C","D"),("D","A")]
        r = euler_check(V, E)
        assert r["circuit_exists"] is True
        if r["circuit"]:
            assert r["circuit"][0] == r["circuit"][-1]

    def test_empty_graph(self):
        r = euler_check([], [])
        assert r["circuit_exists"] is False


class TestHamiltonianCheck:
    def test_k3_has_cycle(self):
        V = ["A","B","C"]
        E = [("A","B"),("B","C"),("A","C")]
        r = hamiltonian_check(V, E)
        assert r["cycle"] != []

    def test_path_graph_no_cycle(self):
        V = ["A","B","C","D"]
        E = [("A","B"),("B","C"),("C","D")]
        r = hamiltonian_check(V, E)
        assert r["cycle"] == []
        assert r["path"] != []   # Hamiltonian path exists

    def test_k4_has_both(self):
        V = ["A","B","C","D"]
        E = [(u,v) for i,u in enumerate(V) for v in V[i+1:]]
        r = hamiltonian_check(V, E)
        assert r["cycle"] != []
        assert r["path"] != []

    def test_too_many_vertices_error(self):
        V = [str(i) for i in range(9)]
        r = hamiltonian_check(V, [])
        assert r["errors"]

    def test_disconnected_no_hamiltonian(self):
        V = ["A","B","C","D"]
        E = [("A","B")]
        r = hamiltonian_check(V, E)
        assert r["cycle"] == []


class TestBipartiteCheck:
    def test_even_cycle_bipartite(self):
        V = ["A","B","C","D"]
        E = [("A","B"),("B","C"),("C","D"),("D","A")]
        r = bipartite_check(V, E)
        assert r["is_bipartite"] is True

    def test_triangle_not_bipartite(self):
        V = ["A","B","C"]
        E = [("A","B"),("B","C"),("A","C")]
        r = bipartite_check(V, E)
        assert r["is_bipartite"] is False
        assert r["odd_cycle"] != []

    def test_complete_bipartite_k23(self):
        V = ["L1","L2","R1","R2","R3"]
        E = [(u,v) for u in ["L1","L2"] for v in ["R1","R2","R3"]]
        r = bipartite_check(V, E)
        assert r["is_bipartite"] is True

    def test_empty_graph(self):
        r = bipartite_check([], [])
        assert r["is_bipartite"] is True

    def test_single_vertex(self):
        r = bipartite_check(["A"], [])
        assert r["is_bipartite"] is True

    def test_path_is_bipartite(self):
        V = ["A","B","C","D"]
        E = [("A","B"),("B","C"),("C","D")]
        r = bipartite_check(V, E)
        assert r["is_bipartite"] is True


class TestGraphColouring:
    def test_triangle_chromatic_3(self):
        V = ["A","B","C"]
        E = [("A","B"),("B","C"),("A","C")]
        r = graph_colouring(V, E)
        assert r["chromatic_number"] == 3

    def test_bipartite_path_chromatic_2(self):
        V = ["A","B","C","D"]
        E = [("A","B"),("B","C"),("C","D")]
        r = graph_colouring(V, E)
        assert r["chromatic_number"] == 2

    def test_empty_graph_chromatic_1(self):
        V = ["A","B","C"]
        E = []
        r = graph_colouring(V, E)
        assert r["chromatic_number"] == 1

    def test_k4_chromatic_4(self):
        V = ["A","B","C","D"]
        E = [(u,v) for i,u in enumerate(V) for v in V[i+1:]]
        r = graph_colouring(V, E)
        assert r["chromatic_number"] == 4

    def test_colouring_valid(self):
        V = ["A","B","C","D","E"]
        E = [("A","B"),("B","C"),("C","D"),("D","E"),("A","C")]
        r = graph_colouring(V, E)
        colouring = r["exact_colouring"] or r["greedy_colouring"]
        # No two adjacent vertices share a colour
        adj_set = {(str(e[0]), str(e[1])) for e in E}
        adj_set |= {(v, u) for u, v in adj_set}
        for u, v in adj_set:
            if u in colouring and v in colouring:
                assert colouring[u] != colouring[v]


class TestMaxMatching:
    def test_perfect_matching(self):
        L = ["A","B","C"]
        R = ["1","2","3"]
        E = [("A","1"),("B","2"),("C","3")]
        r = max_matching(L, R, E)
        assert r["size"] == 3

    def test_incomplete_matching(self):
        L = ["A","B","C"]
        R = ["1","2"]
        E = [("A","1"),("B","1"),("C","2")]
        r = max_matching(L, R, E)
        assert r["size"] == 2

    def test_hall_violation(self):
        # All three from L map to the same right vertex
        L = ["A","B","C"]
        R = ["1","2","3"]
        E = [("A","1"),("B","1"),("C","1")]
        r = max_matching(L, R, E)
        assert r["hall_satisfied"] is False
        assert r["size"] == 1

    def test_no_edges(self):
        r = max_matching(["A","B"], ["1","2"], [])
        assert r["size"] == 0


class TestPlanarityBound:
    def test_k5_violates_bound(self):
        # K5: 5 vertices, 10 edges; bound = 3*5-6 = 9 < 10
        r = planarity_bound_check(5, 10)
        assert r["satisfies_bound"] is False

    def test_k33_violates_bipartite_bound(self):
        # K3,3: 6 vertices, 9 edges; bipartite bound = 2*6-4 = 8 < 9
        r = planarity_bound_check(6, 9, is_bipartite=True)
        assert r["satisfies_bound"] is False

    def test_small_graph_satisfies(self):
        # 4 vertices, 4 edges; 3*4-6 = 6 ≥ 4
        r = planarity_bound_check(4, 4)
        assert r["satisfies_bound"] is True

    def test_small_n_trivially_planar(self):
        r = planarity_bound_check(2, 1)
        assert r["satisfies_bound"] is True


class TestTreeCheck:
    def test_path_is_tree(self):
        V = ["A","B","C","D"]
        E = [("A","B"),("B","C"),("C","D")]
        r = tree_check(V, E)
        assert r["is_tree"] is True

    def test_cycle_not_tree(self):
        V = ["A","B","C"]
        E = [("A","B"),("B","C"),("A","C")]
        r = tree_check(V, E)
        # Cycle → not a tree (e=3, n-1=2)
        assert r["is_tree"] is False

    def test_leaves_detected(self):
        # Star: centre + 3 leaves
        V = ["C","A","B","D"]
        E = [("C","A"),("C","B"),("C","D")]
        r = tree_check(V, E)
        assert r["is_tree"] is True
        assert set(r["leaves"]) == {"A","B","D"}

    def test_single_vertex_tree(self):
        r = tree_check(["A"], [])
        assert r["is_tree"] is True
