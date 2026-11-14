"""
state.py — Streamlit session_state initialisation and reset.
Centralises all default-data loading so every page reads from the same keys.
"""

import streamlit as st

from algorithms.data_loader import (
    load_buildings,
    get_default_thresholds,
    get_default_edges,
)

_KEYS = ("buildings", "thresholds", "edges", "load_errors", "initialized")


def init_state() -> None:
    """
    Initialize st.session_state with default data on first run.
    Does nothing if the 'initialized' sentinel is already set.
    """
    if st.session_state.get("initialized"):
        return

    _load_into_state()
    st.session_state["initialized"] = True


def reset_state() -> None:
    """
    Wipe all managed keys and reload defaults.
    """
    for key in _KEYS:
        st.session_state.pop(key, None)
    _load_into_state()
    st.session_state["initialized"] = True


def _load_into_state() -> None:
    """Internal: populate session_state from CSV and defaults."""
    df, errors = load_buildings()
    st.session_state["buildings"]   = df
    st.session_state["thresholds"]  = get_default_thresholds()
    st.session_state["edges"]       = get_default_edges()
    st.session_state["load_errors"] = errors
