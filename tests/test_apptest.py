"""
test_apptest.py — AppTest smoke tests for every routed page.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from streamlit.testing.v1 import AppTest
import pytest

APP = os.path.join(os.path.dirname(__file__), "..", "app.py")

PAGES = [
    "Dashboard",
    "Campus Data",
    "Sets",
    "Relations & Functions",
    "Logic",
    "Proofs",
    "Counting",
    "Pigeonhole",
    "Inclusion–Exclusion",
    "Graph Theory",
]

TIMEOUT = 180


@pytest.fixture(scope="module")
def at_default():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    return at


@pytest.fixture(scope="module")
def at_empty():
    """Start app then clear buildings to exercise empty-data paths."""
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    import pandas as pd
    at.session_state["buildings"] = pd.DataFrame()
    at.session_state["edges"] = []
    return at


class TestSidebarPages:
    def test_no_exception_default_dashboard(self, at_default):
        assert not at_default.exception, at_default.exception

    def test_all_pages_in_radio(self, at_default):
        radio = at_default.radio[0]
        # format_func adds group headings + icons to labels, so check by containment
        all_labels = " ".join(str(opt) for opt in radio.options)
        for page in PAGES:
            assert page in all_labels, f"Page '{page}' not found in radio options: {radio.options}"


def _navigate_and_check(page_name):
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    at.radio[0].set_value(page_name).run()
    assert not at.exception, f"{page_name}: {at.exception}"


class TestPageRenders:
    @pytest.mark.parametrize("page", PAGES)
    def test_page_no_exception_default_data(self, page):
        _navigate_and_check(page)

    @pytest.mark.parametrize("page", PAGES)
    def test_page_no_exception_empty_data(self, page):
        import pandas as pd
        at = AppTest.from_file(APP, default_timeout=TIMEOUT)
        at.run()
        at.session_state["buildings"] = pd.DataFrame()
        at.session_state["edges"] = []
        at.radio[0].set_value(page).run()
        assert not at.exception, f"{page} (empty): {at.exception}"
