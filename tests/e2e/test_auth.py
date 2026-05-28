"""E2E tests for username/password authentication."""
import pytest

_USERNAME = "admin"
_PASSWORD = "admin"


def test_valid_login(browser, browser_context_args, base_url):
    ctx = browser.new_context(**browser_context_args)
    page = ctx.new_page()
    try:
        page.goto(f"{base_url}/accounts/login/")
        page.locator("#id_login").fill(_USERNAME)
        page.locator("#id_password").fill(_PASSWORD)
        page.locator("[type=submit]").first.click()
        page.wait_for_url(lambda url: "/accounts/login/" not in url, timeout=10_000)
        assert "/accounts/login/" not in page.url
    finally:
        ctx.close()


def test_invalid_login_shows_error(browser, browser_context_args, base_url):
    ctx = browser.new_context(**browser_context_args)
    page = ctx.new_page()
    try:
        page.goto(f"{base_url}/accounts/login/")
        page.locator("#id_login").fill("e2eadmin")
        page.locator("#id_password").fill("definitely-wrong-password")
        page.locator("[type=submit]").first.click()
        page.wait_for_selector(".alert, .errorlist, [class*='error']", timeout=5_000)
        assert "/accounts/login/" in page.url
    finally:
        ctx.close()


def test_logout_clears_session(authenticated_page, base_url):
    page = authenticated_page
    page.goto(f"{base_url}/")
    page.locator("a[href*='logout'], button:has-text('Logout'), a:has-text('Logout')").first.click()
    page.wait_for_load_state("networkidle")
    page.goto(f"{base_url}/rest/data/")
    assert "/accounts/login/" in page.url or page.locator("#id_login").count() > 0
