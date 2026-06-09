import fcntl
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.e2e.helpers import fetch_all_records, reset_records

_USERNAME = "admin"
_PASSWORD = "admin"
_BASE_URL = "https://nexuslims-dev.localhost"
_ACTION_TIMEOUT_MS = 10_000
_NAVIGATION_TIMEOUT_MS = 15_000

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCREENSHOT_DIR = _REPO_ROOT / "deployment" / "test-results"


def new_context(browser, browser_context_args):
    """Create a browser context with project-wide defaults applied."""
    ctx = browser.new_context(**browser_context_args)
    ctx.set_default_timeout(_ACTION_TIMEOUT_MS)
    ctx.set_default_navigation_timeout(_NAVIGATION_TIMEOUT_MS)
    return ctx


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Expose each phase's report on the item so fixtures can inspect it on teardown."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def _screenshot_on_failure(request, page):
    """Capture a full-page screenshot into _SCREENSHOT_DIR when the test's call phase failed.

    Our pages come from custom fixtures, not pytest-playwright's `page` fixture,
    so the plugin's --screenshot=only-on-failure never sees them. This helper
    bridges the gap.
    """
    rep = getattr(request.node, "rep_call", None)
    if rep is None or not rep.failed:
        return
    _SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = request.node.name.replace("/", "_").replace("::", "-")
    try:
        page.screenshot(path=str(_SCREENSHOT_DIR / f"{safe_name}.png"), full_page=True)
    except Exception:
        # Page may already be closed or in an error state; best-effort capture only.
        pass


@pytest.fixture(scope="session")
def base_url():
    return _BASE_URL


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "ignore_https_errors": True}


@pytest.fixture(scope="session")
def auth_state(browser, browser_context_args, base_url):
    """Log in once with username/password and return Playwright storage state."""
    ctx = new_context(browser, browser_context_args)
    page = ctx.new_page()
    page.goto(f"{base_url}/login")
    page.locator("#id_username").fill(_USERNAME)
    page.locator("#id_password").fill(_PASSWORD)
    page.locator("[type=submit]").first.click()
    page.wait_for_url(lambda url: "/login" not in url)
    state = ctx.storage_state()
    ctx.close()
    return state


@pytest.fixture
def authenticated_page(browser, browser_context_args, auth_state, request):
    """Fresh page pre-loaded with auth session."""
    ctx = browser.new_context(**browser_context_args, storage_state=auth_state)
    ctx.set_default_timeout(_ACTION_TIMEOUT_MS)
    ctx.set_default_navigation_timeout(_NAVIGATION_TIMEOUT_MS)
    page = ctx.new_page()
    yield page
    _screenshot_on_failure(request, page)
    ctx.close()


@pytest.fixture
def unauthenticated_page(browser, browser_context_args, request):
    """Fresh page with no auth session.

    Also used by tests that drive the login/logout flow themselves (test_auth,
    test_sso) and shouldn't reuse the session-scoped auth_state.
    """
    ctx = new_context(browser, browser_context_args)
    page = ctx.new_page()
    yield page
    _screenshot_on_failure(request, page)
    ctx.close()


@pytest.fixture
def annotator_page(authenticated_page, base_url, test_record_id):
    """Authenticated page pre-navigated to the annotator for the test record."""
    page = authenticated_page
    page.goto(f"{base_url}/annotate/{test_record_id}/", wait_until="domcontentloaded")
    expect(page.locator("#annotate-save-btn")).to_be_visible()
    return page


@pytest.fixture(scope="session")
def _reset_mutable_records(auth_state, base_url, testrun_uid):
    """Restore example records to their canonical XML before the test session runs.

    Annotator tests that save (dataset moves, title edits, sample changes) persist
    changes to the live CDCS record. Without this reset, a subsequent run sees the
    mutated state -- eventually draining activity 0's datasets and causing
    state-dependent tests (e.g. test_undo_individual_move_via_badge) to silently skip.

    Not autouse: only triggers for workers that actually use _all_records (annotator
    and detail tests). Auth/SSO/gallery/list workers skip this to avoid resetting
    the annotator's working record mid-session during parallel runs.
    """
    _SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    marker = _SCREENSHOT_DIR / f".records-reset-{testrun_uid}"
    with marker.open("a+") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        lock_file.seek(0)
        if not lock_file.read():
            cookies = {c["name"]: c["value"] for c in auth_state["cookies"]}
            reset_records(cookies, base_url)
            lock_file.write("complete")
            lock_file.flush()


@pytest.fixture(scope="session")
def _all_records(auth_state, base_url, _reset_mutable_records):
    """Fetch all records from CDCS once per session (after the reset has run)."""
    cookies = {c["name"]: c["value"] for c in auth_state["cookies"]}
    records = fetch_all_records(cookies, base_url)
    assert records, "No records found -- run init_environment.py first"
    return records


@pytest.fixture(scope="session")
def test_record_id(_all_records):
    """ID of the multisample example record used exclusively by annotator tests.

    Annotator tests mutate this record (title edits, dataset moves, sample adds).
    Using a record that detail tests never touch allows both modules to run in
    parallel without shared-state conflicts.
    """
    return _find_record_id(_all_records, "Example record multisample")


def _find_record_id(records, title):
    for r in records:
        if r.get("title") == title:
            return r["id"]
    pytest.fail(f"Record with title {title!r} not found -- run init_environment.py")


@pytest.fixture(scope="session")
def normal_record_id(_all_records):
    """ID of the standard 48-dataset example record (full interactive layout)."""
    return _find_record_id(_all_records, "Example record")


@pytest.fixture(scope="session")
def simple_display_record_id(_all_records):
    """ID of the 200-dataset example record that triggers the simple display."""
    return _find_record_id(_all_records, "Example record large")


@pytest.fixture(scope="session")
def curation_record_id(_all_records):
    """ID of the curation example record used exclusively by curation tests.

    Pre-baked curation state: dataset 0 rated 3 + featured, dataset 1 rated 5,
    dataset 2 featured only. Datasets 3-4 are clean for interactive tests.
    """
    return _find_record_id(_all_records, "Example record curation")
