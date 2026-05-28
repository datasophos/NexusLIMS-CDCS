import os
import pytest
import requests

_CA_CERT = os.environ.get("CADDY_CA_CERT", "")
_USERNAME = os.environ.get("E2E_USERNAME", "e2eadmin")
_PASSWORD = os.environ.get("E2E_PASSWORD", "")
_BASE_URL = os.environ.get("PLAYWRIGHT_BASE_URL", "https://nexuslims-dev.localhost")


@pytest.fixture(scope="session")
def base_url():
    return _BASE_URL


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    if _CA_CERT:
        return {**browser_context_args, "extra_ca_certs": [_CA_CERT]}
    return browser_context_args


@pytest.fixture(scope="session")
def auth_state(browser, browser_context_args, base_url):
    """Log in once with username/password and return Playwright storage state."""
    ctx = browser.new_context(**browser_context_args)
    page = ctx.new_page()
    page.goto(f"{base_url}/accounts/login/")
    page.locator("#id_login").fill(_USERNAME)
    page.locator("#id_password").fill(_PASSWORD)
    page.locator("[type=submit]").first.click()
    page.wait_for_url(f"{base_url}/**")
    state = ctx.storage_state()
    ctx.close()
    return state


@pytest.fixture
def authenticated_page(browser, browser_context_args, auth_state):
    """Fresh page pre-loaded with auth session."""
    ctx = browser.new_context(**browser_context_args, storage_state=auth_state)
    page = ctx.new_page()
    yield page
    ctx.close()


@pytest.fixture(scope="session")
def test_record_id(auth_state, base_url):
    """Return the ID of the first record in CDCS via the REST API."""
    cookies = {c["name"]: c["value"] for c in auth_state["cookies"]}
    verify = _CA_CERT if _CA_CERT else True
    resp = requests.get(
        f"{base_url}/rest/data/",
        cookies=cookies,
        verify=verify,
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    records = resp.json()
    assert records, "No records found -- run init_environment.py first"
    return records[0]["id"]
