# Acceptance Criteria — Sustainable Solar Energy Allocation Using Set Theory and Graph Optimization
**Application:** Sustainable Solar Energy Allocation Using Set Theory and Graph Optimization  
**Phase:** 1 — Requirements (checklist to be verified in Phase 14 testing)  
**Format:** Each item is a testable assertion. ✅ = must pass before final submission.

---

## Reference Data (Illustrative — used in all tests below unless stated otherwise)

```
Buildings:
  Library:        demand=500, area=1200, solar=90, cost=0
  Laboratory:     demand=700, area=800,  solar=85, cost=0
  Hostel:         demand=900, area=1500, solar=80, cost=0
  Canteen:        demand=350, area=600,  solar=75, cost=0
  Auditorium:     demand=400, area=1000, solar=60, cost=0
  Administration: demand=300, area=700,  solar=85, cost=0

Default Thresholds:
  min_demand     = 400  (>= comparison)
  min_area       = 800  (>= comparison)
  min_solar      = 75   (>= comparison)

Candidate Edges:
  Library    ↔ Laboratory: 12000 INR
  Library    ↔ Hostel:     18000 INR
  Laboratory ↔ Hostel:     10000 INR
```

---

## Group 1: Set Theory

| ID | Test Description | Expected Result |
|---|---|---|
| ST-01 | Universal set U with reference data | `U = {Library, Laboratory, Hostel, Canteen, Auditorium, Administration}` (6 buildings) |
| ST-02 | Set A (demand >= 400) | `A = {Library, Laboratory, Hostel, Auditorium}` |
| ST-03 | Set B (area >= 800) | `B = {Library, Laboratory, Hostel, Auditorium}` |
| ST-04 | Set C (solar >= 75) | `C = {Library, Laboratory, Hostel, Canteen, Administration}` |
| ST-05 | Eligible set E = A ∩ B ∩ C | `E = {Library, Laboratory, Hostel}` |
| ST-06 | Union A ∪ B ∪ C | `= {Library, Laboratory, Hostel, Canteen, Auditorium, Administration}` = U |
| ST-07 | Difference A − B | `= {}` (A and B are equal for reference data) |
| ST-08 | Difference B − A | `= {}` |
| ST-09 | Complement of A (U − A) | `= {Canteen, Administration}` |
| ST-10 | Complement of E (U − E) | `= {Canteen, Auditorium, Administration}` |
| ST-11 | Membership: "Hostel" ∈ E | `True` |
| ST-12 | Membership: "Canteen" ∈ E | `False` |
| ST-13 | Membership: "Auditorium" ∈ A | `True` (demand=400 exactly equals threshold 400; >= applies) |
| ST-14 | Boundary: Auditorium demand exactly 400 (threshold 400) | Auditorium IS in A (>= 400) |
| ST-15 | Boundary: Building with demand = 399 (threshold 400) | Building NOT in A |
| ST-16 | Boundary: Building with solar = 75 (threshold 75) | Building IS in C |
| ST-17 | Boundary: Building with solar = 74 (threshold 75) | Building NOT in C |
| ST-18 | Boundary: Building with area = 800 (threshold 800) | Building IS in B |
| ST-19 | Boundary: Building with area = 799 (threshold 800) | Building NOT in B |
| ST-20 | Empty eligible set: raise all thresholds above max values | E = ∅; no error raised; message displayed |
| ST-21 | Threshold set to 0 for all criteria | All buildings qualify; E = U |
| ST-22 | Building list empty | U = A = B = C = E = ∅; no error; informational message shown |
| ST-23 | Exclusion reasons for Canteen with default thresholds | Reasons include: "demand (350) < 400", "area (600) < 800" |
| ST-24 | Exclusion reasons for Auditorium with default thresholds | Reason includes: "solar (60) < 75" |
| ST-25 | Predicate re-evaluation on threshold change | Changing min_demand to 500 removes Auditorium from A; E recomputed |
| ST-26 | Sets are Python `set` objects (not lists) | `isinstance(result["E"], set)` is True |

---

## Group 2: Priority Ranking

| ID | Test Description | Expected Result |
|---|---|---|
| PR-01 | Only eligible buildings are ranked | Exactly {Library, Laboratory, Hostel} ranked with reference data |
| PR-02 | Return type is list of (str, float) tuples | `list[tuple[str, float]]` |
| PR-03 | Scores are in descending order | `scores[0][1] >= scores[1][1] >= scores[2][1]` |
| PR-04 | Normalization: max demand in E = Hostel 900, min = Library 500 | Hostel D_norm = 100; Library D_norm = 0; Laboratory D_norm = 50 |
| PR-05 | Score formula weights sum to 1.0 | 0.5 + 0.3 + 0.2 = 1.0 (documented) |
| PR-06 | Tie-break: two buildings with identical P score → alphabetical ascending | Building "Alpha" ranked before "Zeta" if scores equal |
| PR-07 | Eligible set with 1 building | Single building returned with score = 100.0 (all norms = 100) |
| PR-08 | Eligible set with 0 buildings | Returns empty list; no error |
| PR-09 | All eligible buildings with equal values in all dims | All scores equal 100.0; ordered alphabetically |
| PR-10 | install_cost_inr is NOT included in P(b) formula | Changing install_cost_inr does not change ranking order |
| PR-11 | Scores rounded to ≤ 4 decimal places | No score with more than 4 decimal places in float repr |
| PR-12 | Priority weights documented as illustrative | Code contains comment: "illustrative assumptions, not scientifically validated" |

---

## Group 3: MST (Kruskal's Algorithm)

| ID | Test Description | Expected Result |
|---|---|---|
| MST-01 | MST with reference data and 3 candidate edges | MST = {Laboratory↔Hostel (10000), Library↔Laboratory (12000)}; total = 22000 INR |
| MST-02 | Candidate total cost | 10000 + 12000 + 18000 = 40000 INR |
| MST-03 | Savings (absolute) | 40000 − 22000 = 18000 INR |
| MST-04 | Savings (percentage) | 18000 / 40000 = 45.0% |
| MST-05 | Step log entry count | 3 entries (one per candidate edge considered) |
| MST-06 | Step log: Library↔Hostel edge | action="REJECTED", reason contains "cycle" |
| MST-07 | Step log: all accepted edges have action="ACCEPTED" | True |
| MST-08 | Step log: all rejected edges have action="REJECTED" | True |
| MST-09 | 0 eligible buildings | status="insufficient_nodes"; mst_edges=[]; step_log=[] |
| MST-10 | 1 eligible building | status="success"; mst_edges=[]; mst_cost=0; step_log=[] |
| MST-11 | 2 eligible buildings, 0 edges | status="disconnected"; mst_edges=[] |
| MST-12 | Disconnected graph (2 components, no cross edges) | status="disconnected"; partial MST returned; message shown |
| MST-13 | Equal-cost edges | MST is valid; secondary sort by (cost, node_a, node_b) makes result deterministic |
| MST-14 | Edge (A, B) and (B, A) treated as same undirected edge | Only one entry in step_log for that edge |
| MST-15 | MST has exactly n−1 edges when graph is connected | len(mst_edges) == n_eligible_buildings − 1 |
| MST-16 | UnionFind.find uses path compression | Parent pointers updated after find (verified by inspection / unit test) |
| MST-17 | UnionFind.union uses union by rank | Rank incremented only when merging equal-rank trees |
| MST-18 | No Streamlit import in mst.py | `import streamlit` not present in file |

---

## Group 4: Dijkstra's Algorithm

| ID | Test Description | Expected Result |
|---|---|---|
| DJ-01 | Shortest path Library → Hostel in reference graph | path=["Library","Laboratory","Hostel"], distance=22000 (12000+10000) |
| DJ-02 | Shorter than direct Library→Hostel (18000) | 22000 > 18000 — wait: Library→Hostel direct = 18000 < 22000 via Laboratory. Correct shortest = Library→Hostel direct, distance=18000 |
| DJ-03 | DJ-02 corrected: Library → Hostel shortest path | path=["Library","Hostel"], distance=18000 |
| DJ-04 | Shortest path Laboratory → Library | path=["Laboratory","Library"], distance=12000 |
| DJ-05 | Shortest path Laboratory → Hostel | path=["Laboratory","Hostel"], distance=10000 |
| DJ-06 | Source == destination | status="same_node", distance=0, path=[source] |
| DJ-07 | Invalid source (not in graph) | status="invalid_source" |
| DJ-08 | Invalid destination (not in graph) | status="invalid_destination" |
| DJ-09 | Destination unreachable (disconnected graph) | status="unreachable", path=None, distance=None |
| DJ-10 | Single-node graph, source == only node, dest == same | status="same_node", distance=0 |
| DJ-11 | visited_order field present and is list[str] | True |
| DJ-12 | No Streamlit import in shortest_path.py | `import streamlit` not present in file |
| DJ-13 | MST result ≠ shortest path result (different problems) | For reference data: MST cost=22000, Library→Hostel shortest=18000; not equal |

> **Note on DJ-02/DJ-03:** The direct Library→Hostel edge (18000 INR) gives a shorter path than via Laboratory (12000+10000=22000 INR). This is intentional — MST minimizes total tree cost, not individual paths. This difference is used in the UI to explain why MST ≠ shortest path.

---

## Group 5: Cost Analysis

| ID | Test Description | Expected Result |
|---|---|---|
| CA-01 | Total candidate cost with reference edges | 40000 INR |
| CA-02 | MST cost with reference data | 22000 INR |
| CA-03 | Absolute savings | 18000 INR |
| CA-04 | Percentage savings | 45.0% |
| CA-05 | Zero-baseline guard: 0 candidate edges | Savings % = "N/A" (no divide-by-zero error) |
| CA-06 | Cost chart rendered without error | `st.pyplot()` called exactly once per render; no exception |
| CA-07 | Disclaimer displayed | Text contains "modeled network connection costs, not electricity" |
| CA-08 | Savings calculation is not hardcoded | Changing edge costs updates savings dynamically |

---

## Group 6: Validation

| ID | Test Description | Expected Result |
|---|---|---|
| VAL-01 | Empty building name | Error: "Building name cannot be empty" |
| VAL-02 | Duplicate building name (case-insensitive) | Error: "Building name 'X' already exists" |
| VAL-03 | Non-numeric demand | Error: "demand_kwh_day must be a positive number" |
| VAL-04 | Negative demand | Error: "demand_kwh_day must be a positive number (got: -50)" |
| VAL-05 | Zero demand | Error: "demand_kwh_day must be a positive number (got: 0)" |
| VAL-06 | Negative rooftop area | Error: "rooftop_area_m2 must be a positive number" |
| VAL-07 | Solar potential = 0 | Error: "solar_potential_pct must be between 0 and 100 (exclusive of 0)" |
| VAL-08 | Solar potential = 101 | Error: "solar_potential_pct must be between 0 and 100" |
| VAL-09 | Solar potential = 100 | Valid (accepted) |
| VAL-10 | Negative install cost | Error: "install_cost_inr must be >= 0" |
| VAL-11 | Zero install cost | Valid (means "not estimated") |
| VAL-12 | Negative edge cost | Error: "Edge cost must be >= 0 (negative weights not supported)" |
| VAL-13 | Self-loop edge (same node both ends) | Error: "Edge endpoints must be different buildings" |
| VAL-14 | Duplicate edge (A-B already exists, adding B-A) | Error: "Edge between 'A' and 'B' already exists" |
| VAL-15 | Edge with non-existent building name | Error: "Building 'X' does not exist in the current building list" |
| VAL-16 | Missing required field in CSV row | Row skipped with warning; other rows loaded normally |
| VAL-17 | Threshold with non-numeric value | Error: "Threshold value must be a number" |
| VAL-18 | min_solar_pct > 100 | Error: "min_solar_potential_pct must be between 0 and 100" |
| VAL-19 | Algorithm functions receive already-validated data | validators.py called by components before passing to algorithms |

---

## Group 7: Integration

| ID | Test Description | Expected Result |
|---|---|---|
| INT-01 | App launches without error | `streamlit run app.py` starts with exit code 0; no traceback |
| INT-02 | All 9 UI modules reachable via navigation | Each module renders without exception |
| INT-03 | Adding a building updates all downstream modules | Set theory, graph, priority, cost all reflect new building |
| INT-04 | Removing a building from eligible set (threshold change) | Edges touching it go inactive; graph updates; MST recomputed |
| INT-05 | Editing a building value updates sets | E recomputed; priority recomputed; all on same re-run |
| INT-06 | Adding an edge updates graph and MST | New edge visible in graph; MST re-run |
| INT-07 | "Reset to defaults" reloads reference data | session_state matches CSV after reset |
| INT-08 | No algorithm module imports Streamlit | `grep -r "import streamlit" algorithms/` returns no results |
| INT-09 | No Streamlit state stored in algorithm return values | Algorithm functions return plain Python types only |
| INT-10 | All session_state keys initialized on first load | No KeyError on fresh session |

---

## Group 8: UI / UX

| ID | Test Description | Expected Result |
|---|---|---|
| UI-01 | Dataset labelled as "illustrative" | Phrase "illustrative" appears in data source description |
| UI-02 | Priority weights labelled as "illustrative assumptions" | Visible disclaimer near priority formula |
| UI-03 | SDG section makes no claim of verified real-world impact | No absolute claim ("will reduce", "proven to"); uses hedged language |
| UI-04 | Venn diagram renders for reference data | Three circles visible; E region highlighted; legend present |
| UI-05 | MST visualization distinguishes accepted vs candidate edges | MST = thick green; candidate non-MST = dashed grey |
| UI-06 | Cost chart has both bars labeled with values | INR values annotated on chart |
| UI-07 | Algorithm explanation section includes time complexity | O(E log E) for MST, O((V+E) log V) for Dijkstra visible |
| UI-08 | Exclusion reasons shown per building | Each ineligible building shows which criteria it failed |
| UI-09 | Step-by-step MST log shown in UI | Table or list of edge decisions visible in module 5 |
| UI-10 | Shortest path displayed as node sequence | e.g., "Library → Hostel" with total cost |
| UI-11 | Inactive edge warning displayed | Message shown when edges filtered due to ineligibility |

---

## Notes for Test Implementation (Phase 14)

1. **Tests MUST compute, not hardcode.** e.g., `test_mst.py` must call `kruskal_mst(graph)` and assert the result — never assert against a pre-written list of edges.
2. **Reference data in `conftest.py`.** All test fixtures load the reference dataset from constants, not from CSV (to avoid file-path issues in CI).
3. **Boundary tests** (ST-13 through ST-19) must be parameterized with `@pytest.mark.parametrize`.
4. **DJ-02 / DJ-03 note:** The "expected" shortest path Library→Hostel is the **direct edge (18000 INR)**, not via Laboratory. This is important for correctly distinguishing MST from shortest path.
5. **MST-13 (equal cost edges):** Test must verify that the same MST is produced across multiple runs (determinism).
6. **MST-15 (|edges| == n−1):** This is the standard connectivity condition for a spanning tree.
