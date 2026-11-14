"""
data_loader.py — CSV loading and default data helpers.
Reads campus_buildings.csv, runs validate_buildings, and returns a clean DataFrame.
No Streamlit imports allowed in this module.
"""

import os
import copy
import pandas as pd

from algorithms.validation import (
    validate_buildings,
    _empty_buildings_df,
    DEFAULT_THRESHOLDS,
    DEFAULT_EDGES,
    REQUIRED_COLUMNS,
)

# Default CSV path relative to the repository root.
_DEFAULT_CSV = os.path.join(
    os.path.dirname(__file__), "..", "data", "campus_buildings.csv"
)


def load_buildings(path: str = None) -> tuple:
    """
    Load and validate the buildings CSV file.

    Returns
    -------
    (df, errors)
        df     : pd.DataFrame with canonical columns and valid rows only.
                 Empty typed DataFrame if the file is missing or unreadable.
        errors : list[str] — empty on full success, non-empty otherwise.
    """
    if path is None:
        path = os.path.normpath(_DEFAULT_CSV)

    errors: list = []

    if not os.path.exists(path):
        errors.append(f"File not found: '{path}'. Returning empty dataset.")
        return _empty_buildings_df(), errors

    try:
        raw_df = pd.read_csv(path, dtype=str)
    except Exception as exc:                    # noqa: BLE001
        errors.append(
            f"Could not read CSV file '{path}': {exc}. Returning empty dataset."
        )
        return _empty_buildings_df(), errors

    # Ensure required columns are present (add missing as NaN); extra
    # columns in the file are simply ignored.
    for col in REQUIRED_COLUMNS:
        if col not in raw_df.columns:
            raw_df[col] = None

    clean_df, val_errors = validate_buildings(raw_df)
    errors.extend(val_errors)

    return clean_df, errors


def get_default_thresholds() -> dict:
    """Return a fresh copy of the default threshold configuration."""
    return copy.deepcopy(DEFAULT_THRESHOLDS)


def get_default_edges() -> list:
    """Return a fresh copy of the default candidate edges list."""
    return list(DEFAULT_EDGES)
