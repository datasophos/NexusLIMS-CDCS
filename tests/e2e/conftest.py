from pathlib import Path

import pytest
import requests

_USERNAME = "admin"
_PASSWORD = "admin"
_BASE_URL = "https://nexuslims-dev.localhost"
_TIMEOUT_MS = 5_000

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCREENSHOT_DIR = _REPO_ROOT / "deployment" / "test-results"
_RESETTABLE_RECORDS = {
    "Example record": _REPO_ROOT / "deployment/test-data/example_record.xml",
    "Example record large": _REPO_ROOT / "deployment/test-data/example_record_large.xml",
    "Example record multisample": _REPO_ROOT
    / "deployment/test-data/example_record_multisample.xml",
}


def new_context(browser, browser_context_args):
    """Create a browser context with project-wide defaults applied."""
    ctx = browser.new_context(**browser_context_args)
    ctx.set_default_timeout(_TIMEOUT_MS)
    ctx.set_default_navigation_timeout(_TIMEOUT_MS)
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
    ctx.set_default_timeout(_TIMEOUT_MS)
    ctx.set_default_navigation_timeout(_TIMEOUT_MS)
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


def _fetch_records(cookies, base_url):
    resp = requests.get(
        f"{base_url}/rest/data/",
        cookies=cookies,
        verify=False,
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", data) if isinstance(data, dict) else data


@pytest.fixture(scope="session", autouse=True)
def _reset_mutable_records(auth_state, base_url):
    """Restore example records to their canonical XML before the test session runs.

    Annotator tests that save (dataset moves, title edits, sample changes) persist
    changes to the live record. Without this reset, later runs see the mutated
    state from prior runs -- eventually draining activity 0's datasets and
    causing state-dependent tests (e.g. test_undo_individual_move_via_badge)
    to silently skip.
    """
    cookies = {c["name"]: c["value"] for c in auth_state["cookies"]}
    csrf = cookies.get("csrftoken", "")
    headers = {"X-CSRFToken": csrf, "Referer": base_url}

    records = _fetch_records(cookies, base_url)
    by_title = {r["title"]: r["id"] for r in records if isinstance(r, dict)}

    for title, xml_path in _RESETTABLE_RECORDS.items():
        rid = by_title.get(title)
        if rid is None or not xml_path.exists():
            continue
        content = xml_path.read_text(encoding="utf-8")
        resp = requests.patch(
            f"{base_url}/rest/data/{rid}/",
            cookies=cookies,
            verify=False,
            headers=headers,
            json={"content": content},
        )
        resp.raise_for_status()


@pytest.fixture(scope="session")
def _all_records(auth_state, base_url, _reset_mutable_records):
    """Fetch all records from CDCS once per session (after the reset has run)."""
    cookies = {c["name"]: c["value"] for c in auth_state["cookies"]}
    records = _fetch_records(cookies, base_url)
    assert records, "No records found -- run init_environment.py first"
    return records


@pytest.fixture(scope="session")
def test_record_id(_all_records):
    """Return the ID of the first record in CDCS via the REST API."""
    return _all_records[0]["id"]


def _find_record_id(records, title):
    for r in records:
        if r.get("title") == title:
            return r["id"]
    pytest.skip(f"Record with title {title!r} not found -- run init_environment.py")


@pytest.fixture(scope="session")
def normal_record_id(_all_records):
    """ID of the standard 48-dataset example record (full interactive layout)."""
    return _find_record_id(_all_records, "Example record")


@pytest.fixture(scope="session")
def simple_display_record_id(_all_records):
    """ID of the 200-dataset example record that triggers the simple display."""
    return _find_record_id(_all_records, "Example record large")
