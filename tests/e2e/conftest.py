import pytest
import requests

_USERNAME = "admin"
_PASSWORD = "admin"
_BASE_URL = "https://nexuslims-dev.localhost"
_TIMEOUT_MS = 5_000


def new_context(browser, browser_context_args):
    """Create a browser context with project-wide defaults applied."""
    ctx = browser.new_context(**browser_context_args)
    ctx.set_default_timeout(_TIMEOUT_MS)
    ctx.set_default_navigation_timeout(_TIMEOUT_MS)
    return ctx


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
def authenticated_page(browser, browser_context_args, auth_state):
    """Fresh page pre-loaded with auth session."""
    ctx = browser.new_context(**browser_context_args, storage_state=auth_state)
    ctx.set_default_timeout(_TIMEOUT_MS)
    ctx.set_default_navigation_timeout(_TIMEOUT_MS)
    page = ctx.new_page()
    yield page
    ctx.close()


@pytest.fixture
def unauthenticated_page(browser, browser_context_args):
    """Fresh page with no auth session, for testing public/anonymous access."""
    ctx = new_context(browser, browser_context_args)
    page = ctx.new_page()
    yield page
    ctx.close()


@pytest.fixture(scope="session")
def test_record_id(auth_state, base_url):
    """Return the ID of the first record in CDCS via the REST API."""
    cookies = {c["name"]: c["value"] for c in auth_state["cookies"]}
    resp = requests.get(
        f"{base_url}/rest/data/",
        cookies=cookies,
        verify=False,
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    data = resp.json()
    records = data.get("results", data) if isinstance(data, dict) else data
    assert records, "No records found -- run init_environment.py first"
    return records[0]["id"]
