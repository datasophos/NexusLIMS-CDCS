"""E2E tests for SAML SSO authentication."""
import pytest
from tests.e2e.conftest import new_context

# Dev IdP test credentials -- hardcoded in deployment/dev-sso/authsources.php
_IDP_USERNAME = "admin"
_IDP_PASSWORD = "admin"


def test_sso_login_redirects_to_idp(browser, browser_context_args, base_url):
    """Clicking the SSO button redirects to the SimpleSAMLphp IdP."""
    ctx = new_context(browser, browser_context_args)
    page = ctx.new_page()
    try:
        page.goto(f"{base_url}/login")
        sso_btn = page.locator("a.btn-lge, a[href*='saml2/login']").first
        sso_btn.click()
        page.wait_for_load_state("networkidle")
        assert "sso.nexuslims-dev.localhost" in page.url or "saml" in page.url.lower()
    finally:
        ctx.close()


def test_sso_login_full_flow(browser, browser_context_args, base_url):
    """Full SSO flow: login page -> IdP -> CDCS logged in as admin."""
    ctx = new_context(browser, browser_context_args)
    page = ctx.new_page()
    try:
        page.goto(f"{base_url}/login")
        sso_btn = page.locator("a.btn-lge, a[href*='saml2/login']").first
        sso_btn.click()
        page.wait_for_load_state("networkidle")

        page.locator("input[name='username']").fill(_IDP_USERNAME)
        page.locator("input[name='password']").fill(_IDP_PASSWORD)
        page.locator("[type=submit]").first.click()

        page.wait_for_url(f"{base_url}/**")
        assert "/login" not in page.url
        assert "sso.nexuslims-dev.localhost" not in page.url
    finally:
        ctx.close()


def test_sso_login_user_visible_in_nav(browser, browser_context_args, base_url):
    """After SSO login, the username appears in the navigation."""
    ctx = new_context(browser, browser_context_args)
    page = ctx.new_page()
    try:
        page.goto(f"{base_url}/login")
        sso_btn = page.locator("a.btn-lge, a[href*='saml2/login']").first
        sso_btn.click()
        page.wait_for_load_state("networkidle")
        page.locator("input[name='username']").fill(_IDP_USERNAME)
        page.locator("input[name='password']").fill(_IDP_PASSWORD)
        page.locator("[type=submit]").first.click()
        page.wait_for_url(f"{base_url}/**")

        assert page.locator(f"text={_IDP_USERNAME}").count() > 0
    finally:
        ctx.close()
