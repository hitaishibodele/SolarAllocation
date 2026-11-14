# Architecture Plan — Sustainable Solar Energy Allocation Using Set Theory and Graph Optimization
## Using Set Theory and Graph Optimization
**Application:** Sustainable Solar Energy Allocation Using Set Theory and Graph Optimization  
**Date planned:** 2026-10-16  
**Phase:** 1 — Requirements & Architecture (no code written yet)

---

## Table of Contents
1. [Folder / File Structure](#1-folder--file-structure)
2. [Dependencies](#2-dependencies)
3. [Data Model](#3-data-model)
4. [State Management](#4-state-management)
5. [Algorithm Plan](#5-algorithm-plan)
6. [Edge Cases](#6-edge-cases)
7. [Validation Plan](#7-validation-plan)
8. [Eligible Buildings → Graph Pipeline](#8-eligible-buildings--graph-pipeline)
9. [Visualization Plan](#9-visualization-plan)
10. [Phased Roadmap](#10-phased-roadmap)
11. [Risks and Ambiguities](#11-risks-and-ambiguities)

---

## 1. Folder / File Structure

```
solar-campus-planner/
│
├── app.py                          # Streamlit entry point; imports all components, manages session_state
│
├── data/
│   └── campus_buildings.csv        # Illustrative seed dataset (6 reference buildings + 3 candidate edges)
│
├── algorithms/
│   ├── __init__.py                 # Makes algorithms a package (empty)
│   ├── set_theory.py               # Set operations (A, B, C, E, union, diff, complement, membership)
│   ├── mst.py                      # Kruskal's algorithm + Union-Find; returns step log
│   └── shortest_path.py            # Dijkstra's algorithm; returns path + distance
│
├── components/
│   ├── __init__.py                 # Makes components a package (empty)
│   ├── dashboard.py                # Campus summary dashboard (module 1)
│   ├── building_manager.py         # Add / remove / edit buildings, thresholds, costs, edges (module 2)
│   ├── set_theory_ui.py            # Set theory analysis display + exclusion reasons (module 3)
│   ├── venn_diagram.py             # Matplotlib Venn diagram renderer (used by set_theory_ui)
│   ├── priority_ranking.py         # Priority scoring display (module 4)
│   ├── network_graph.py            # NetworkX + matplotlib graph + MST visualizer (module 5)
│   ├── shortest_path_ui.py         # Dijkstra source/destination selector and result display (module 6)
│   ├── cost_analysis.py            # Cost comparison, savings, chart (module 7)
│   ├── algorithm_explanations.py   # Pseudocode, complexity, and SDG text (modules 8 & 9)
│   └── sdg_relevance.py            # SDG 7, 11, 12 relevance section (module 9)
│
├── tests/
│   ├── __init__.py                 # Makes tests a package (empty)
│   ├── conftest.py                 # Shared pytest fixtures (reference dataset, thresholds, edges)
│   ├── test_sets.py                # Unit tests for set_theory.py
│   ├── test_mst.py                 # Unit tests for mst.py
│   └── test_shortest_path.py       # Unit tests for shortest_path.py
│
├── requirements.txt                # Pinned dependencies (created in Phase 2)
└── README.md                       # Setup, usage, and project description (created in Phase 16)
```

### Why this structure (any deviation from the brief is justified here)

| Decision | Reason |
|---|---|
| `building_manager.py` instead of unnamed component | Gives a clear single-responsibility home for all CRUD + edge management that the brief groups under "module 2" |
| `set_theory_ui.py` + `venn_diagram.py` split | Keeps pure rendering logic (venn_diagram) separable and testable without Streamlit |
| `shortest_path_ui.py` explicit name | Avoids confusion with `shortest_path.py` in algorithms/ |
| `sdg_relevance.py` kept separate from `algorithm_explanations.py` | Different concern; allows each to grow independently |
| `conftest.py` in tests/ | Standard pytest fixture sharing; avoids duplication across test files |
| `__init__.py` files | Required for Python package imports used by app.py and tests |

**Separation rules honoured:**
- All files under `algorithms/` contain **zero** Streamlit imports.
- Validation logic lives in a `validators.py` module within `algorithms/` (see §7).
- MST (`mst.py`) and Dijkstra (`shortest_path.py`) are separate files.
- Visualization code is in `components/`; algorithm code is in `algorithms/`.

*(One additional file is added: `algorithms/validators.py` — see §7 for justification.)*

Updated structure addition:
```
algorithms/
    validators.py   # Input validation helpers; no Streamlit; called by components before passing data to algorithms
```

---

## 2. Dependencies

| Package | Version pin strategy | Reason |
|---|---|---|
| `streamlit` | `>=1.28,<2.0` | Web app framework; session_state API is stable in 1.x |
| `pandas` | `>=2.0,<3.0` | DataFrame for building table; 2.x has improved nullable dtypes |
| `matplotlib` | `>=3.7,<4.0` | Venn diagrams and cost charts; 3.7+ required for `matplotlib-venn` compat |
| `matplotlib-venn` | `>=0.11.9` | Three-set Venn diagram rendering; pure matplotlib, no extra runtime |
| `networkx` | `>=3.1,<4.0` | Graph data structure, layout algorithms for visualization |
| `pytest` | `>=7.4,<8.0` | Unit testing; 7.x is stable and widely supported on Python 3.9 |
| `numpy` | `>=1.24,<2.0` | Normalization arithmetic; already a transitive dep of pandas/matplotlib |

**Version pinning rationale:** Use `>=X.Y,<(X+1).0` (compatible-release style) to allow patch updates while guarding against breaking major-version changes. Exact pins will be locked with `pip freeze` after Phase 2 setup and recorded in `requirements.txt`.

**Deliberately excluded:**
- No database (SQLite, etc.) — session_state + CSV is sufficient for a single-user local app.
- No auth — local-only, no multi-user scenario.
- No scipy — normalization is a simple min-max formula; no scientific library needed.
- No external APIs or cloud services.

---

## 3. Data Model

### 3.1 Building (canonical representation)

Used as the shared format across ALL modules. Algorithm modules accept this dict; components display it.

```python
# Python dataclass (for documentation — the actual type used is dict for Streamlit compatibility)
@dataclass
class Building:
    name:                str         # Unique; no leading/trailing whitespace; non-empty
    demand_kwh_day:      float       # kWh/day; valid range: > 0
    rooftop_area_m2:     float       # m²;      valid range: > 0
    solar_potential_pct: float       # %;       valid range: 0 < value <= 100
    install_cost_inr:    float       # INR;     valid range: >= 0; 0 means "not estimated"
```

**Pandas DataFrame columns** (canonical for CSV load and session_state storage):

| Column name | dtype | Notes |
|---|---|---|
| `name` | `str` | Primary key; enforced unique in validators |
| `demand_kwh_day` | `float64` | kWh/day |
| `rooftop_area_m2` | `float64` | m² |
| `solar_potential_pct` | `float64` | 0–100 |
| `install_cost_inr` | `float64` | 0 = not estimated |

The DataFrame is the authoritative store. Algorithm functions receive it as a parameter and return plain Python structures (sets, lists, dicts) — never a modified DataFrame.

### 3.2 Threshold Config

```python
@dataclass
class ThresholdConfig:
    min_demand_kwh_day:      float   # >= 0; default 400
    min_rooftop_area_m2:     float   # >= 0; default 800
    min_solar_potential_pct: float   # 0–100; default 75
```

Stored as a dict in `st.session_state["thresholds"]`.

### 3.3 Candidate Edge

```python
@dataclass
class Edge:
    node_a: str     # Building name (alphabetically first — see undirected canonicalization below)
    node_b: str     # Building name (alphabetically second)
    cost_inr: float # >= 0; connection cost in INR
```

**Undirected edge canonicalization rule:** When an edge is added (programmatically or by the user), always store `node_a = min(name1, name2)` and `node_b = max(name1, name2)` (lexicographic order). This ensures A–B and B–A are identical tuples and duplicate detection is a simple equality check.

Stored as a list of dicts in `st.session_state["edges"]`. The graph modules always sort endpoints before lookup.

**Pandas representation for edges** (used in cost_analysis and display):

| Column | dtype | Notes |
|---|---|---|
| `node_a` | str | Alphabetically first endpoint |
| `node_b` | str | Alphabetically second endpoint |
| `cost_inr` | float64 | Connection cost |

### 3.4 Shared Graph Representation

NetworkX `Graph` object (undirected, weighted) is **constructed on demand** by `network_graph.py` from the current session_state edges — it is **not stored** in session_state (avoids pickling issues with Streamlit). The builder function signature:

```python
def build_graph(buildings_df: pd.DataFrame, edges: list[dict]) -> nx.Graph:
    """Returns a NetworkX Graph with node attributes from buildings_df
    and edge attribute 'cost' (float). Only nodes present in buildings_df
    and edges where both endpoints are in buildings_df are included."""
```

MST and Dijkstra functions receive this `nx.Graph` object.

---

## 4. State Management

All mutable state lives in `st.session_state`. Initialized once in `app.py` on first load (guarded by `if "initialized" not in st.session_state`).

| Key | Type | Description |
|---|---|---|
| `st.session_state["buildings"]` | `pd.DataFrame` | Editable table of buildings (canonical columns from §3.1) |
| `st.session_state["thresholds"]` | `dict` | `{min_demand, min_rooftop, min_solar}` (§3.2) |
| `st.session_state["edges"]` | `list[dict]` | Candidate edges (§3.3); sorted node_a < node_b |
| `st.session_state["initialized"]` | `bool` | Prevents re-initialization on re-run |

**Sharing across pages:** All Streamlit pages (sidebar nav via `st.sidebar.radio` or `st.tabs`) import and read from `st.session_state` directly. No global variables. No file I/O between pages.

**Re-computation:** There is no cached derived state (eligible set, graph, MST, etc.). Every component computes what it needs from `st.session_state` at render time. This guarantees consistency when data changes. For performance, use `@st.cache_data` only if profiling reveals a bottleneck (Phase 15).

**CSV initialization:** On first load, `app.py` reads `data/campus_buildings.csv` and `data/candidate_edges.csv` into session_state. Users can then add/edit/remove data in the UI. A "Reset to defaults" button in the building manager reloads from CSV.

*(Note: `candidate_edges.csv` is a second data file not listed in the original brief. It is added because seed edges must be loadable separately from buildings. This is the only structural addition.)*

---

## 5. Algorithm Plan

### 5.1 Set Theory (`algorithms/set_theory.py`)

**Notation clarification:**  
- `E` = eligible set (set theory result)  
- `Eg` = graph edges (NetworkX / session_state edges) — these never overlap in code

#### Functions

```python
def compute_sets(
    buildings_df: pd.DataFrame,
    thresholds: dict
) -> dict:
    """
    Returns:
        {
          "U":        set[str],   # universal set — all building names
          "A":        set[str],   # high demand
          "B":        set[str],   # sufficient area
          "C":        set[str],   # good solar potential
          "E":        set[str],   # eligible = A ∩ B ∩ C
          "A_union_B":    set[str],
          "A_union_C":    set[str],
          "B_union_C":    set[str],
          "A_union_B_union_C": set[str],
          "A_diff_B":     set[str],   # A − B
          "B_diff_A":     set[str],
          "complement_A": set[str],   # U − A
          "complement_B": set[str],
          "complement_C": set[str],
          "complement_E": set[str],
          "exclusion_reasons": dict[str, list[str]]  # building → list of reasons not in E
        }
    """
    # Pseudocode:
    # U = set of all building names in buildings_df
    # A = {b.name for b in buildings if b.demand >= thresholds["min_demand"]}
    # B = {b.name for b in buildings if b.area   >= thresholds["min_area"]}
    # C = {b.name for b in buildings if b.solar  >= thresholds["min_solar"]}
    # E = A & B & C
    # exclusion_reasons: for each b in U not in E, record which conditions failed
    # Return all sets as a dict
```

**Time complexity:** O(n) where n = number of buildings. One pass per criterion.

**Predicate-defined sets:** A, B, C are defined by predicates (threshold comparisons), not hardcoded membership — thus they recompute correctly when thresholds or building data change.

**Membership:** `b ∈ A` is tested as `b in compute_sets(...)["A"]` — standard Python set membership, O(1).

---

### 5.2 Priority Ranking (`algorithms/set_theory.py` — same module, separate function)

**Formula (illustrative, not scientifically validated):**
```
P(b) = 0.5 × D_norm(b) + 0.3 × R_norm(b) + 0.2 × S_norm(b)
```
where D, R, S are normalized to [0, 100] using min-max normalization:
```
X_norm(b) = 100 × (X(b) − X_min) / (X_max − X_min)
```

**Normalization edge case (all values equal):** If `X_max == X_min`, set `X_norm = 100` for all buildings (all are equal; giving max score is more conservative than 0, and avoids division by zero).

**Tie-break rule:** Ties in P(b) are broken alphabetically by building name (ascending). This makes ranking deterministic and reproducible.

```python
def compute_priority(
    buildings_df: pd.DataFrame,
    eligible_set: set[str]
) -> list[tuple[str, float]]:
    """
    Returns a list of (building_name, priority_score) sorted by score desc,
    then name asc for ties. Only buildings in eligible_set are ranked.
    Scores are rounded to 4 decimal places to avoid float display noise.
    Weights (0.5, 0.3, 0.2) are illustrative assumptions only.
    """
    # Pseudocode:
    # Filter buildings_df to eligible rows only
    # Compute D_norm, R_norm, S_norm for D=demand, R=area, S=solar
    # Handle equal-value edge case (set all norms to 100)
    # P = 0.5*D_norm + 0.3*R_norm + 0.2*S_norm
    # Sort by (-P, name)
    # Return list of (name, score)
```

**Time complexity:** O(n log n) for sort; O(n) for normalization. n = |eligible_set|.

---

### 5.3 MST via Kruskal's Algorithm (`algorithms/mst.py`)

#### Union-Find (Disjoint Set Union)

```python
class UnionFind:
    def __init__(self, nodes: list[str]):
        self.parent = {n: n for n in nodes}
        self.rank   = {n: 0  for n in nodes}

    def find(self, x: str) -> str:
        # Path compression
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> bool:
        # Union by rank; returns True if merged, False if already connected
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False  # would form a cycle
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True
```

#### Kruskal's Main Function

```python
def kruskal_mst(
    graph: nx.Graph
) -> dict:
    """
    Parameters:
        graph: nx.Graph with edge attribute 'cost' (float, non-negative).
               Nodes are building names (str).
    Returns:
        {
          "mst_edges":    list[tuple[str, str, float]],  # (node_a, node_b, cost)
          "mst_cost":     float,
          "step_log":     list[dict],  # one entry per edge considered
          "is_connected": bool,        # False if graph has > 1 connected component
          "status":       str          # "success" | "insufficient_nodes" | "disconnected"
        }
    step_log entry format:
        {
          "edge":     (str, str),
          "cost":     float,
          "action":   "ACCEPTED" | "REJECTED",
          "reason":   str   # e.g., "Added to MST" | "Would form a cycle"
        }
    """
    # Pseudocode:
    # n = graph.number_of_nodes()
    # if n == 0: return status="insufficient_nodes", mst_edges=[], mst_cost=0
    # if n == 1: return status="success" (trivial MST, single node, no edges)
    # Sort all edges by cost ascending
    # Initialize UnionFind with all nodes
    # For each edge (u, v, cost) in sorted order:
    #   log: edge considered
    #   if union(u, v) returns True:
    #     add to mst_edges; log ACCEPTED "Added to MST"
    #   else:
    #     log REJECTED "Would form a cycle"
    # if len(mst_edges) == n-1: is_connected=True, status="success"
    # else: is_connected=False, status="disconnected"
    # return result dict
```

**Time complexity:** O(E log E) for sort + O(E α(V)) for union-find operations ≈ O(E log E) overall, where E = edges, V = nodes.

---

### 5.4 Dijkstra's Algorithm (`algorithms/shortest_path.py`)

```python
def dijkstra(
    graph: nx.Graph,
    source: str,
    destination: str
) -> dict:
    """
    Parameters:
        graph:       nx.Graph with edge attribute 'cost' (float, non-negative).
        source:      Starting node name.
        destination: Target node name.
    Returns:
        {
          "path":      list[str] | None,    # ordered node list; None if unreachable
          "distance":  float | None,        # total cost; None if unreachable
          "status":    str,                 # "success" | "unreachable" | "invalid_source"
                                            #   | "invalid_destination" | "same_node"
          "visited_order": list[str]        # nodes settled in order (for explanation display)
        }
    """
    # Pseudocode:
    # Validate source and destination are in graph — if not, return appropriate status
    # If source == destination: return path=[source], distance=0, status="same_node"
    # Initialize dist = {n: inf for all n}; dist[source] = 0
    # prev = {n: None for all n}
    # min-heap: [(0, source)]
    # visited = set()
    # While heap not empty:
    #   (d, u) = heappop
    #   if u in visited: continue
    #   visited.add(u); visited_order.append(u)
    #   if u == destination: break
    #   for each neighbor v of u:
    #     weight = graph[u][v]["cost"]
    #     if weight < 0: raise ValueError (should be caught in validation)
    #     if dist[u] + weight < dist[v]:
    #       dist[v] = dist[u] + weight
    #       prev[v] = u
    #       heappush(heap, (dist[v], v))
    # if dist[destination] == inf: status="unreachable", path=None, distance=None
    # else: reconstruct path via prev; status="success"
    # return result dict
```

**Time complexity:** O((V + E) log V) with a binary heap.

**Non-negative weight enforcement:** Validation (§7) rejects negative edge costs before they reach this function. The function itself also checks and raises `ValueError` as a defensive second layer.

---

## 6. Edge Cases

### Set Theory
| Scenario | Handling |
|---|---|
| Empty building list | U = ∅, A = B = C = E = ∅; Venn diagram shows empty sets |
| All thresholds set to 0 | All buildings qualify for A, B, C; E = U |
| Threshold so high that E = ∅ | E = ∅; graph section shows "No eligible buildings" message |
| Value exactly equal to threshold | **Included** (`>=` comparison, not `>`); explicit boundary note in UI |
| All buildings identical values | Normalization sets all D_norm/R_norm/S_norm = 100 |

### Priority Ranking
| Scenario | Handling |
|---|---|
| Eligible set has 0 buildings | Return empty list; component shows informational message |
| Eligible set has 1 building | Score computed normally (norm = 100 for all dims); ranked first |
| All eligible buildings have equal P score | Tied — sort alphabetically ascending |
| install_cost_inr not in formula | Installation cost is displayed alongside priority but **not** included in P(b) calculation (it is a different dimension — see §11, Risk R4) |

### MST (Kruskal)
| Scenario | Handling |
|---|---|
| 0 eligible buildings | status="insufficient_nodes"; step_log=[]; no graph rendered |
| 1 eligible building | Trivial MST (single node, 0 edges); status="success"; message shown |
| 2+ buildings, no edges | status="disconnected"; MST = ∅; all edges rejected for cycle |
| Disconnected graph | status="disconnected"; partial MST returned for each component |
| Equal-cost edges | Order of iteration determines which is accepted first; tie-breaking by sorted node names (lex) at the sorting step ensures reproducibility |
| All edges same cost | MST is valid but not unique; a note is displayed in the UI |
| Negative cost edge | Rejected at validation layer (§7); never reaches mst.py |

### Dijkstra
| Scenario | Handling |
|---|---|
| Source == destination | status="same_node"; distance=0; path=[source] |
| Source not in graph | status="invalid_source" |
| Destination not in graph | status="invalid_destination" |
| Destination unreachable | status="unreachable"; path=None |
| Negative weight (defensive) | ValueError raised (should be blocked by validation first) |
| Graph with 1 node | Only valid if source == destination |

---

## 7. Validation Plan

All validation lives in `algorithms/validators.py`. Component code calls validators **before** passing data to algorithm functions. This keeps algorithm functions clean and testable independently.

```python
# algorithms/validators.py  (signature plan)

def validate_building(row: dict) -> list[str]:
    """Returns list of error strings. Empty list = valid."""
    # Check: name is non-empty string, no leading/trailing whitespace
    # Check: demand_kwh_day is numeric, > 0
    # Check: rooftop_area_m2 is numeric, > 0
    # Check: solar_potential_pct is numeric, 0 < value <= 100
    # Check: install_cost_inr is numeric, >= 0

def validate_no_duplicate_name(name: str, existing_names: list[str]) -> list[str]:
    """Returns error if name already exists (case-insensitive comparison)."""

def validate_threshold(key: str, value: float) -> list[str]:
    """Returns error if value is not numeric or out of allowed range."""
    # min_demand >= 0; min_area >= 0; min_solar in [0, 100]

def validate_edge(node_a: str, node_b: str, cost: float, existing_nodes: list[str], existing_edges: list[dict]) -> list[str]:
    """
    Checks:
    - node_a and node_b exist in building list
    - node_a != node_b (no self-loops)
    - cost is numeric and >= 0  (negative costs rejected here)
    - edge (sorted) not already in existing_edges
    """
```

**Error message format:** Plain English, specific field mentioned, e.g.:
- `"demand_kwh_day must be a positive number (got: -50)"`
- `"Building name 'Library' already exists"`
- `"solar_potential_pct must be between 0 and 100 (got: 110)"`
- `"Edge cost must be >= 0 (negative weights not supported)"`
- `"Building 'X' does not exist in the current building list"`

Validation errors are displayed via `st.error(msg)` in the relevant component — never silently ignored.

---

## 8. Eligible Buildings → Graph Pipeline

**Rule:** The candidate edge list (`session_state["edges"]`) stores all user-defined edges regardless of eligibility. The graph shown in modules 5, 6, and 7 is **filtered at render time**:

```
eligible_nodes = compute_sets(buildings_df, thresholds)["E"]
active_edges   = [e for e in session_state["edges"]
                  if e["node_a"] in eligible_nodes
                  and e["node_b"] in eligible_nodes]
graph = build_graph(filtered_buildings_df, active_edges)
```

**What happens to edges touching ineligible buildings:**
- They remain stored in `session_state["edges"]` (not deleted automatically).
- They are **filtered out** of the graph passed to MST and Dijkstra.
- The UI shows a notice: "N candidate edge(s) are inactive because one or both endpoints are not in the eligible set."
- When a building later becomes eligible again (threshold changed), its edges are automatically re-included.

**Rationale:** Permanent deletion on threshold change would be destructive and surprising to the user. Soft-filtering is safer and reversible.

**What happens when eligible set changes:**
- All derived structures (graph, MST, priority ranking, cost analysis) recompute automatically on the next Streamlit render — because none are cached in session_state (see §4).

---

## 9. Visualization Plan

### 9.1 Venn Diagram (`components/venn_diagram.py`)

- **Library:** `matplotlib-venn` (`venn3` for three sets A, B, C)
- **Sets shown:** A (demand), B (area), C (solar potential) — three circles
- **Labels:** Each region labeled with building name abbreviations; a legend maps abbreviation → full name
- **E highlight:** The A∩B∩C region is filled with a distinct color (e.g., gold) to make E immediately visible
- **Empty sets:** If a set is empty, its circle is drawn with dashed border and "∅" label
- **Rendering:** `plt.figure()` → `venn3(...)` → `st.pyplot(fig)` → `plt.close(fig)` (prevent memory leak)

### 9.2 Network Graph (`components/network_graph.py`)

- **Library:** NetworkX (`spring_layout` for node positions) + Matplotlib
- **Node rendering:**
  - Eligible buildings: filled circle, color #2196F3 (blue)
  - Ineligible buildings (shown as background reference, optional toggle): grey, smaller
- **Edge rendering:**
  - Candidate edges (not in MST): thin grey dashed line
  - MST edges: thick green solid line
  - Rejected by cycle detection: not distinguished visually (logged in step-log table instead)
- **Labels:** Node labels = building name; Edge labels = cost in INR (abbreviated, e.g., "12K")
- **Shortest path:** When Dijkstra result exists, path edges are overlaid in orange (thicker than MST, different color)
- **Legend:** Color legend always shown (eligible node / MST edge / candidate edge / shortest path)
- **Rendering:** Single `plt.figure(figsize=(10,7))` per render; `st.pyplot(fig)` + `plt.close(fig)`

### 9.3 Cost Chart (`components/cost_analysis.py`)

- **Type:** Horizontal grouped bar chart (matplotlib)
- **Bars:**
  1. Total candidate network cost
  2. MST cost (minimum)
- **Annotation:** Savings amount (INR) and percentage labeled on chart
- **Colors:** Candidate = `#EF5350` (red-ish), MST = `#66BB6A` (green-ish)
- **Zero baseline guard:** If candidate total = 0, savings % displayed as "N/A" not divide-by-zero
- **Title disclaimer:** "Note: These are modeled network connection costs, not electricity bill savings."

---

## 10. Phased Roadmap

| Phase | Name | Files Touched | Key Deliverable |
|---|---|---|---|
| 1 | Requirements & Architecture | `docs/` | This document + ACCEPTANCE_CRITERIA.md |
| 2 | Environment Setup | `requirements.txt`, `.venv/` (not committed) | Virtual env + all packages installed; `pytest` passes with 0 tests |
| 3 | Dataset & Validation | `data/campus_buildings.csv`, `data/candidate_edges.csv`, `algorithms/validators.py`, `tests/conftest.py` | CSV files + validator unit tests |
| 4 | Set Theory Algorithms | `algorithms/set_theory.py`, `tests/test_sets.py` | `compute_sets`, `compute_priority`; all unit tests pass |
| 5 | Venn Diagram + Set Theory UI | `components/venn_diagram.py`, `components/set_theory_ui.py` | Venn diagram renders correctly for reference data |
| 6 | Dashboard | `app.py`, `components/dashboard.py` | Streamlit app launches; sidebar nav; campus overview |
| 7 | Priority Ranking | `components/priority_ranking.py` | Priority table renders; tied-score ordering verified |
| 8 | Weighted Graph Construction | `algorithms/mst.py` (graph builder), `algorithms/shortest_path.py` (graph builder) | `build_graph` function; no UI yet |
| 9 | MST (Kruskal) | `algorithms/mst.py`, `tests/test_mst.py` | Kruskal + Union-Find; step log; all MST tests pass |
| 10 | Graph Visualization | `components/network_graph.py` | Network renders; MST edges highlighted; candidate edges shown |
| 11 | Dijkstra | `algorithms/shortest_path.py`, `tests/test_shortest_path.py`, `components/shortest_path_ui.py` | Shortest path computed and displayed |
| 12 | Cost Analysis + SDG | `components/cost_analysis.py`, `components/sdg_relevance.py` | Cost bar chart; savings; SDG section |
| 13 | Integration | `app.py`, all components | All 9 UI modules wired; session_state flows verified end-to-end |
| 14 | Testing & Debugging | `tests/test_sets.py`, `tests/test_mst.py`, `tests/test_shortest_path.py` | All acceptance criteria tests pass; boundary cases covered |
| 15 | UI Refinement | All `components/` | Layout polished; mobile-friendly; disclaimers added; error messages reviewed |
| 16 | Documentation | `README.md`, `algorithms/algorithm_explanations.py` | Setup guide; algorithm explanation section complete |

---

## 11. Risks and Ambiguities

| ID | Risk / Ambiguity | Recommended Resolution |
|---|---|---|
| R1 | **Normalization when all eligible buildings have equal values in one dimension.** Min-max denominator = 0 → division by zero. | Set all normalized values to 100 (everyone is equally at max). Document this rule in UI and code. |
| R2 | **MST meaning with < 2 eligible buildings.** 0 nodes: no graph. 1 node: trivial MST with no edges. | For 0 nodes: show message "No eligible buildings — cannot build graph." For 1 node: show "Only 1 eligible building — MST is trivial (single node, total cost = 0)." No edges returned. |
| R3 | **Does installation cost (`install_cost_inr`) affect the priority score?** The brief specifies P = 0.5D + 0.3R + 0.2S with no cost term. | Keep installation cost **out of P(b)**. Display it in a separate column in the priority table as reference information. Document clearly that cost and priority are separate dimensions. |
| R4 | **Graph edges vs. eligible set — should edges be deleted or soft-filtered?** | Soft-filter (§8). Edges persist in session_state; only excluded from graph if endpoints not eligible. User is notified. |
| R5 | **Are `candidate_edges.csv` reference edge weights (12000, 18000, 10000) in INR?** The brief says "INR" for the expected MST. | Assume INR throughout. Label all cost values as "INR" in the UI. |
| R6 | **Python 3.9 compatibility.** `list[str]` type hints require Python 3.9+; `dict[str, ...]` likewise. | Use `list[str]`, `dict[str, ...]` directly (Python 3.9 supports built-in generics). No `from __future__ import annotations` needed. Confirm in Phase 2 setup. |
| R7 | **`matplotlib-venn` only supports up to 3 sets natively.** If future requirements add a 4th criterion set, `venn3` won't work. | Acceptable for current scope. Document as known limitation in README. |
| R8 | **Streamlit session_state and pytest.** Streamlit-specific code cannot be unit-tested directly without a running Streamlit server. | Algorithm modules (`algorithms/`) contain zero Streamlit code — these are fully unit-testable. Component functions are tested indirectly via integration (Phase 13–14). |
| R9 | **Equal-cost MST edges — which is chosen?** With edges of equal cost (e.g., two edges both costing 10000), the MST result may vary by sort order. | Before Kruskal sort, apply a secondary sort key: `(cost, node_a, node_b)` (lex). This makes output deterministic and testable. |
| R10 | **"Savings" terminology.** Users may misinterpret "cost savings" as electricity bill reduction. | Add explicit disclaimer in cost_analysis component: "These figures represent modeled network connection cost differences, not electricity or energy bill savings." Repeat in SDG section. |
| R11 | **Canteen edge case in reference data.** Canteen (demand=350, area=600, solar=75) is NOT in E with default thresholds (demand < 400, area < 800). Its solar=75 qualifies it for C. Confirm expected C set includes Canteen.** | Per the brief: C = {Library, Laboratory, Hostel, Canteen, Administration} — this confirms solar threshold is `>= 75` (Canteen's solar=75 qualifies). Demand threshold is `>= 400` (Canteen's 350 does not qualify for A). Resolution: use `>=` for all threshold comparisons. |
| R12 | **Administration in reference data.** Administration (demand=300, area=700, solar=85): demand=300 < 400 (not in A), area=700 < 800 (not in B), solar=85 >= 75 (in C). So Administration is in C but not in A or B — it is not in E. This is consistent with the brief's expected results.** | No action needed. Verify in test_sets.py with exact membership assertions. |
