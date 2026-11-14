"""
validation.py — Input validation helpers for buildings, thresholds and edges.
All validators are pure functions: they never raise on bad user data and
always return (clean_result, list[str]) where the list contains plain-English
error messages.
No Streamlit imports allowed in this module.
"""

import math
import pandas as pd

# ---------------------------------------------------------------------------
# Column-name constants (canonical DataFrame schema)
# ---------------------------------------------------------------------------
COL_NAME   = "name"
COL_DEMAND = "energy_demand_kwh_day"
COL_AREA   = "rooftop_area_m2"
COL_SOLAR  = "solar_potential_pct"

REQUIRED_COLUMNS = [COL_NAME, COL_DEMAND, COL_AREA, COL_SOLAR]

NUMERIC_REQUIRED = [COL_DEMAND, COL_AREA, COL_SOLAR]  # must be non-NaN after coercion

# ---------------------------------------------------------------------------
# Default thresholds
# ---------------------------------------------------------------------------
DEFAULT_THRESHOLDS = {
    "min_demand": 400.0,
    "min_area":   800.0,
    "min_solar":  75.0,
}

# ---------------------------------------------------------------------------
# Default candidate connections — unordered building-name pairs (u, v) with
# u < v alphabetically, so a pair and its reverse are the same connection.
# ---------------------------------------------------------------------------
def canonicalize_edge(u: str, v: str) -> tuple:
    """Return (min_name, max_name) with the two names in alphabetical order."""
    u = str(u).strip()
    v = str(v).strip()
    if u > v:
        u, v = v, u
    return (u, v)


DEFAULT_EDGES: list = [
    canonicalize_edge("Hostel",         "Laboratory"),
    canonicalize_edge("Hostel",         "Library"),
    canonicalize_edge("Laboratory",     "Library"),
    canonicalize_edge("Canteen",        "Hostel"),
    canonicalize_edge("Auditorium",     "Library"),
    canonicalize_edge("Administration", "Laboratory"),
]


# ---------------------------------------------------------------------------
# Empty typed DataFrame helper
# ---------------------------------------------------------------------------
def _empty_buildings_df() -> pd.DataFrame:
    """Return an empty DataFrame with the correct column dtypes."""
    return pd.DataFrame(
        columns=REQUIRED_COLUMNS,
    ).astype(
        {
            COL_NAME:   str,
            COL_DEMAND: float,
            COL_AREA:   float,
            COL_SOLAR:  float,
        }
    )


# ---------------------------------------------------------------------------
# validate_buildings
# ---------------------------------------------------------------------------
def validate_buildings(df) -> tuple:
    """
    Validate a buildings DataFrame.

    Parameters
    ----------
    df : any
        Expected to be a pd.DataFrame with the canonical columns.

    Returns
    -------
    (clean_df, errors)
        clean_df : DataFrame with only valid rows (typed correctly).
        errors   : list[str] of plain-English error messages.
    """
    errors = []

    # --- guard: not a DataFrame ---
    if not isinstance(df, pd.DataFrame):
        errors.append(
            f"Expected a DataFrame but received {type(df).__name__}. "
            "Returning empty dataset."
        )
        return _empty_buildings_df(), errors

    # --- guard: empty DataFrame ---
    if df.empty:
        return _empty_buildings_df(), errors

    # --- check required columns (extra columns in the file are ignored) ---
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(
            f"Missing required column(s): {', '.join(missing_cols)}. "
            "Cannot validate rows without them."
        )
        return _empty_buildings_df(), errors

    # Work on a copy to avoid mutating the caller's frame.
    work = df[REQUIRED_COLUMNS].copy()

    # --- name column: trim whitespace ---
    work[COL_NAME] = work[COL_NAME].astype(str).str.strip()

    # Track which rows are invalid (True = bad, exclude from output).
    bad_rows = pd.Series(False, index=work.index)

    # --- blank / missing names ---
    blank_name_mask = work[COL_NAME].isin(["", "nan", "None", "NaN"])
    for idx in work.index[blank_name_mask]:
        errors.append(
            f"Row {idx}: name is blank or missing — row excluded."
        )
    bad_rows |= blank_name_mask

    # --- duplicate names (case-insensitive, among still-valid rows) ---
    valid_so_far = work[~bad_rows].copy()
    lowered = valid_so_far[COL_NAME].str.lower()
    dup_mask = lowered.duplicated(keep="first")
    for idx in valid_so_far.index[dup_mask]:
        orig_name = work.at[idx, COL_NAME]
        errors.append(
            f"Row {idx}: duplicate building name '{orig_name}' "
            "(case-insensitive match with an earlier row) — row excluded."
        )
    bad_rows.loc[valid_so_far.index[dup_mask]] = True

    # --- coerce numeric columns ---
    for col in NUMERIC_REQUIRED:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    # --- required numeric: NaN after coercion is an error ---
    for col in NUMERIC_REQUIRED:
        nan_mask = work[col].isna() & ~bad_rows
        for idx in work.index[nan_mask]:
            name_label = work.at[idx, COL_NAME] or f"row {idx}"
            errors.append(
                f"Row {idx} ('{name_label}'): '{col}' is not a valid number — "
                "row excluded."
            )
        bad_rows |= nan_mask

    # --- reject inf values in required numeric columns ---
    for col in NUMERIC_REQUIRED:
        inf_mask = work[col].apply(
            lambda x: isinstance(x, float) and math.isinf(x)
        ) & ~bad_rows
        for idx in work.index[inf_mask]:
            name_label = work.at[idx, COL_NAME] or f"row {idx}"
            errors.append(
                f"Row {idx} ('{name_label}'): '{col}' is infinite — row excluded."
            )
        bad_rows |= inf_mask

    # --- demand: >= 0 (zero allowed) ---
    neg_demand = (work[COL_DEMAND] < 0) & ~bad_rows
    for idx in work.index[neg_demand]:
        name_label = work.at[idx, COL_NAME]
        errors.append(
            f"Row {idx} ('{name_label}'): '{COL_DEMAND}' must be >= 0 "
            f"(got {work.at[idx, COL_DEMAND]}) — row excluded."
        )
    bad_rows |= neg_demand

    # --- area: >= 0 (zero allowed) ---
    neg_area = (work[COL_AREA] < 0) & ~bad_rows
    for idx in work.index[neg_area]:
        name_label = work.at[idx, COL_NAME]
        errors.append(
            f"Row {idx} ('{name_label}'): '{COL_AREA}' must be >= 0 "
            f"(got {work.at[idx, COL_AREA]}) — row excluded."
        )
    bad_rows |= neg_area

    # --- solar_potential_pct: 0–100 inclusive ---
    bad_solar = ((work[COL_SOLAR] < 0) | (work[COL_SOLAR] > 100)) & ~bad_rows
    for idx in work.index[bad_solar]:
        name_label = work.at[idx, COL_NAME]
        errors.append(
            f"Row {idx} ('{name_label}'): '{COL_SOLAR}' must be between 0 and 100 "
            f"(got {work.at[idx, COL_SOLAR]}) — row excluded."
        )
    bad_rows |= bad_solar

    # --- build clean output ---
    clean = work[~bad_rows].copy()
    clean[COL_NAME] = clean[COL_NAME].astype(str)
    for col in NUMERIC_REQUIRED:
        clean[col] = clean[col].astype(float)
    clean = clean.reset_index(drop=True)

    return clean, errors


# ---------------------------------------------------------------------------
# validate_thresholds
# ---------------------------------------------------------------------------
def validate_thresholds(t) -> tuple:
    """
    Validate a threshold dict.

    Expected keys: 'min_demand', 'min_area', 'min_solar'.
    Invalid values are replaced with the corresponding defaults.

    Returns
    -------
    (clean_dict, errors)
    """
    errors = []
    defaults = DEFAULT_THRESHOLDS.copy()

    if not isinstance(t, dict):
        errors.append(
            f"Thresholds must be a dict but received {type(t).__name__}. "
            "Using all defaults."
        )
        return defaults, errors

    clean = {}
    required_keys = {
        "min_demand": (0.0, None),
        "min_area":   (0.0, None),
        "min_solar":  (0.0, 100.0),
    }

    for key, (lo, hi) in required_keys.items():
        if key not in t:
            errors.append(
                f"Threshold key '{key}' is missing — using default "
                f"{defaults[key]}."
            )
            clean[key] = defaults[key]
            continue

        raw = t[key]
        try:
            val = float(raw)
        except (TypeError, ValueError):
            errors.append(
                f"Threshold '{key}' is not numeric (got {raw!r}) — "
                f"using default {defaults[key]}."
            )
            clean[key] = defaults[key]
            continue

        if math.isnan(val) or math.isinf(val):
            errors.append(
                f"Threshold '{key}' is not a finite number (got {val}) — "
                f"using default {defaults[key]}."
            )
            clean[key] = defaults[key]
            continue

        if val < lo:
            errors.append(
                f"Threshold '{key}' must be >= {lo} (got {val}) — "
                f"using default {defaults[key]}."
            )
            clean[key] = defaults[key]
            continue

        if hi is not None and val > hi:
            errors.append(
                f"Threshold '{key}' must be <= {hi} (got {val}) — "
                f"using default {defaults[key]}."
            )
            clean[key] = defaults[key]
            continue

        clean[key] = val

    return clean, errors


# ---------------------------------------------------------------------------
# validate_edges  — unordered building-name pairs
# ---------------------------------------------------------------------------
def validate_edges(edges, building_names) -> tuple:
    """
    Validate a list of candidate connections (unordered name pairs).

    Parameters
    ----------
    edges : any
        Expected list/tuple of (u, v) items. Any extra element in an item is
        ignored; a connection is an unordered pair.
    building_names : collection of str
        The set of valid building names (trimmed, exact-match after trim).

    Returns
    -------
    (clean_edges, errors)
        clean_edges : list of canonical (u, v) tuples, sorted by (u, v).
        errors      : list[str]
    """
    errors = []

    if edges is None:
        return [], []

    if not hasattr(edges, "__iter__") or isinstance(edges, (str, dict)):
        errors.append(
            f"Edges must be a list/iterable of (u, v) pairs "
            f"(got {type(edges).__name__}) — returning empty edge list."
        )
        return [], errors

    valid_names = set(str(n).strip() for n in building_names)
    seen: dict = {}   # canonical (u,v) -> first-seen index for duplicate detection
    clean = []

    for i, edge in enumerate(edges):
        label = f"Edge {i}"

        # Must be indexable with 2 or 3 elements
        try:
            edge = tuple(edge)
            if len(edge) < 2:
                errors.append(
                    f"{label}: expected (u, v) but got {len(edge)} "
                    "element(s) — skipped."
                )
                continue
            raw_u, raw_v = edge[0], edge[1]
        except (TypeError, ValueError):
            errors.append(
                f"{label}: cannot unpack as (u, v) — skipped."
            )
            continue

        u = str(raw_u).strip()
        v = str(raw_v).strip()

        # Endpoints must exist in building_names
        unknown = []
        if u not in valid_names:
            unknown.append(u)
        if v not in valid_names:
            unknown.append(v)
        if unknown:
            errors.append(
                f"{label} ('{u}' — '{v}'): building(s) not found in current "
                f"building list: {', '.join(repr(n) for n in unknown)} — skipped."
            )
            continue

        # No self-loops
        if u == v:
            errors.append(
                f"{label}: self-loop on '{u}' — edge endpoints must be different "
                "buildings — skipped."
            )
            continue

        # Canonicalize: u < v
        cu, cv = (u, v) if u < v else (v, u)
        key = (cu, cv)

        # Duplicate undirected edge check (A-B same as B-A)
        if key in seen:
            errors.append(
                f"{label} ('{raw_u}' — '{raw_v}'): duplicate undirected edge "
                f"already seen at index {seen[key]} — skipped (keeping first)."
            )
            continue

        seen[key] = i
        clean.append((cu, cv))

    # Deterministic order: (u, v)
    clean.sort(key=lambda e: (e[0], e[1]))
    return clean, errors
