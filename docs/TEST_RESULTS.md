# Test Results — Phase 12 (Integration Audit, End-to-End Tests, Bug Fixes)

All figures below were produced by actually running the commands in this session.

## 1. Environment

| Component | Version |
| --- | --- |
| Date of run | 2026-10-18 |
| Python | 3.9.6 |
| streamlit | 1.50.0 |
| pandas | 2.3.3 |
| numpy | 2.0.2 |
| matplotlib | 3.9.4 |
| networkx | 3.2.1 |
| pytest | 8.4.2 |

Commands run from the project root with the project virtualenv (`.venv`).

## 2. Full test suite

Command:

```
.venv/bin/python -m pytest -v
```

Result:

```
================= 469 passed, 14 warnings in 374.54s (0:06:14) =================
```

Collection count (from real output):

```
.venv/bin/python -m pytest --co -q | tail -n 5
...
469 tests collected in 3.87s
```

No tests were skipped: 469 collected, 469 passed, 0 skipped, 0 failed, 0 errors.

### Tests per file (from the real `-v` output)

| Test file | Tests |
| --- | --- |
| tests/test_validation.py | 84 |
| tests/test_sets.py | 76 |
| tests/test_app_smoke.py | 72 |
| tests/test_shortest_path.py | 41 |
| tests/test_integration.py (new this phase) | 38 |
| tests/test_stats.py | 35 |
| tests/test_cost.py | 32 |
| tests/test_priority.py | 22 |
| tests/test_network_graph.py | 21 |
| tests/test_mst.py | 19 |
| tests/test_e2e_app.py (new this phase) | 19 |
| tests/test_network.py | 10 |
| **Total** | **469** |

### New tests added in this phase

* `tests/test_integration.py` — 38 plain-pytest tests. A single full-pipeline
  helper runs `load → thresholds → sets → priority → network → kruskal → cost →
  dijkstra` using only `algorithms/` functions. Coverage includes: default
  reference values; edited buildings (Canteen joined to E); threshold changes
  (min_demand 600 removes Library); empty and single-building eligible sets;
  edge-weight changes that alter or do not alter the MST; ineligible-touching
  edges excluded from candidate and MST totals; disconnected graphs; validation
  integration (never raises, downstream never called with invalid data); and a
  seeded random stress test of 50 datasets (MST has n−1 edges when connected,
  MST total ≤ candidate total, Dijkstra equals NetworkX, E == A ∩ B ∩ C,
  ranking ⊆ E, and eligibility never changes with the weights).
* `tests/test_e2e_app.py` — 19 AppTest tests. All 9 pages render with default
  data and produce no `st.exception` elements; one full workflow edits
  buildings, thresholds and an edge weight and cross-checks the values shown by
  Dashboard, Set Theory, Priority Ranking, Network & MST, Shortest Path and Cost
  Analysis against the same `algorithms/` functions computed independently from
  the same `session_state`; invalid inputs (empty buildings, no edges, duplicate
  names via the validation path, weights that do not sum to 1, zero eligible)
  never crash any page; the "Reset to defaults" button restores the reference
  values.

## 3. Streamlit app start-up

Command:

```
.venv/bin/python -m streamlit run app.py --server.headless true --server.port 8601
```

Result: started with no traceback; the process served the app and was then
stopped.

```
Local URL: http://localhost:8601
health check: HTTP 200
```

## 4. Audit findings

The audit covered `algorithms/`, `components/`, `app.py` and the test files.

| # | Check | Finding |
| --- | --- | --- |
| 1 | Hardcoded results (`22000`, `40000`, `18000`, `45`, `"Library"`, `"Hostel"`, `"Laboratory"`) | No computed result is hardcoded. `algorithms/validation.py:49-51` holds the 10000/18000/12000 literals in `DEFAULT_EDGES` — shipped default data, not a result. `components/cost_analysis.py:24`, `components/network_page.py:22` and `components/shortest_path_page.py:24` contain `22000`/`18000` only inside `_fmt_inr` docstrings as formatting examples. `components/explanations.py:293-326` uses `Library`/`Hostel` only in the explicitly labelled "Live example" branch, with a static "Generic example" fallback. All are explained, none required a fix. |
| 2 | Duplicated set / priority / MST / cost / canonicalization logic | None outside `algorithms/`. Components only call `algorithms/` functions. The Dashboard's network overview was changed in Phase 11 to call `network_cost_summary` instead of recomputing the totals. |
| 3 | `streamlit` imported inside `algorithms/` | Zero matches (grep for `import streamlit` / `from streamlit` in `algorithms/`). |
| 4 | Pages reading data other than `st.session_state`, or computing eligibility differently | Every page reads the `buildings`, `thresholds`, `edges`, `weights` session keys, and eligibility is always computed with `algorithms.set_theory.build_sets` / `eligible_set`. |
| 5 | Matplotlib figures not closed after `st.pyplot` | All six call sites are immediately followed by `plt.close(fig)`: `cost_analysis.py:148-149`, `network_page.py:158-159` and `164-165`, `dashboard.py:175-176` and `185-186`, `shortest_path_page.py:164-165`, `priority_page.py:198-199`, `set_page.py:191-192`. |
| 6 | Unvalidated input paths writing into `session_state` | All writes go through `algorithms.validation` (`validate_buildings`, `validate_thresholds`, `validate_edges`, `validate_priority_weights`) before being stored. |
| 7 | Inconsistent units/labels and missing "Illustrative sample data" caption | Units are consistent: INR (cost), kWh/day (demand), m² (area), % (solar and savings %). The caption "Illustrative sample data, not real measurements" is present on all 9 pages (plus the Data Management tab caption). |
| 8 | Unsupported claims | No page claims verified savings, verified environmental impact or electricity-bill savings; the Cost, Explanations and SDG pages all hedge these explicitly. |

## 5. Fixes applied (minimal, non-behavioural)

1. `algorithms/data_loader.py` — removed unused imports `validate_thresholds`, `validate_edges`.
2. `algorithms/stats.py` — removed unused `import math`.
3. `components/data_page.py` — removed unused `import math` and unused `DEFAULT_THRESHOLDS` import.
4. `components/network_page.py` — removed unused `candidate_total` import (now `from algorithms.network import build_network` only).
5. `components/set_page.py` — removed unused `build_sets`, `eligible_set` imports (kept `set_operations_summary`, `explain_building`, `classification_table`, `venn_regions`).
6. `components/venn_diagram.py` — removed unused `import math`.
7. `components/dashboard.py` — corrected a stale docstring that still referred to "placeholder sections for features coming in later phases".
8. `tests/test_app_smoke.py` — renamed the stale `test_default_page_is_dashboard_placeholder` to `test_default_page_is_dashboard` and corrected its docstring.

No algorithm behaviour was changed. After the fixes an AST scan reported
`files with unused imports: 0` and `import app` succeeds cleanly.

## 6. Known limitations

* `st.data_editor` (the Data Management building/edge editors) cannot be driven
  by AppTest, so the Data Management **validation path** is exercised by calling
  the same `validate_*` functions the page calls, on the same data, and writing
  the validated result into `session_state` exactly as the page does.
* `st.pyplot` figures are not introspectable through AppTest; figure closing is
  covered by the component-level tests and by the source audit in section 4.
* AppTest does not expose `st.dataframe` values in every Streamlit version; the
  Priority Ranking page test falls back to text assertions in that case (the
  fallback is only used when the dataframe is unavailable and is reported, not
  silently skipped).
* The 14 warnings in the suite are pre-existing (matplotlib
  `PyparsingDeprecationWarning`; Streamlit `use_container_width` deprecation) and
  were not introduced by this phase.
