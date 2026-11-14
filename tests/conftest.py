"""
conftest.py — Shared pytest configuration and fixtures.
Adds the repository root to sys.path so that 'algorithms' and 'components'
packages can be imported by all test modules without installation.
"""

import sys
import os

# Insert the repository root (one level above this tests/ directory) at the
# front of sys.path.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
