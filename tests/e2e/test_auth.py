"""E2E tests for username/password authentication."""
from tests.e2e.conftest import new_context

_USERNAME = "admin"
_PASSWORD = "admin"


def test_valid_login(browser, browser_context_args, base_url):
    ctx = new_context(browser, browser_context_args)
    page = ctx.new_page()
    try:
        page.goto(f"{base_url}/login")
        page.locator("#id_username").fill(_USERNAME)
        page.locator("#id_password").fill(_PASSWORD)
        page.locator("[type=submit]").first.click()
        page.wait_for_url(lambda url: "/login" not in url)
        assert "/login" not in page.url
    finally:
        ctx.close()


def test_invalid_login_shows_error(browser, browser_context_args, base_url):
    ctx = new_context(browser, browser_context_args)
    page = ctx.new_page()
    try:
        page.goto(f"{base_url}/login")
        page.locator("#id_username").fill(_USERNAME)
        page.locator("#id_password").fill("definitely-wrong-password")
        page.locator("[type=submit]").first.click()
        page.wait_for_selector(".alert, .errorlist, [class*='error']")
        assert "/login" in page.url
    finally:
        ctx.close()


def test_logout_clears_session(browser, browser_context_args, base_url):
    # Use a dedicated context rather than the shared authenticated_page fixture.
    # Logging out invalidates the server-side session; reusing the session-scoped
    # auth_state after logout would leave other tests with stale cookies.
    ctx = new_context(browser, browser_context_args)
    page = ctx.new_page()
    try:
        page.goto(f"{base_url}/login")
        page.locator("#id_username").fill(_USERNAME)
        page.locator("#id_password").fill(_PASSWORD)
        page.locator("[type=submit]").first.click()
        page.wait_for_url(lambda url: "/login" not in url)

        # Logout is inside the #dropdownDashboard Bootstrap menu — open it first.
        page.locator("#dropdownDashboard").click()
        page.locator("a[href*='logout'].cdcs-menu-item").wait_for(state="visible")
        page.locator("a[href*='logout'].cdcs-menu-item").click()
        page.wait_for_load_state("networkidle")

        # Confirm the session is gone: a protected page should redirect to login.
        if "/login" not in page.url and page.locator("#id_username").count() == 0:
            page.goto(f"{base_url}/annotate/check-auth-only/")
            page.wait_for_load_state("networkidle")
        assert "/login" in page.url or page.locator("#id_username").count() > 0
    finally:
        ctx.close()


def test_next_param_redirects_after_login(browser, browser_context_args, base_url):
    """Accessing a protected page while logged out then logging in lands on that page."""
    ctx = new_context(browser, browser_context_args)
    page = ctx.new_page()
    try:
        # Hit a @login_required view unauthenticated; Django appends ?next=...
        page.goto(f"{base_url}/annotate/check-auth-only/")
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url
        assert "next=" in page.url

        page.locator("#id_username").fill(_USERNAME)
        page.locator("#id_password").fill(_PASSWORD)
        page.locator("[type=submit]").first.click()
        page.wait_for_load_state("networkidle")

        # Should land at /annotate/check-auth-only/, not the default post-login page.
        assert "/annotate/check-auth-only/" in page.url
    finally:
        ctx.close()


def test_login_page_redirects_when_already_authenticated(authenticated_page, base_url):
    """Navigating to /login while already logged in redirects away from the login form."""
    page = authenticated_page
    page.goto(f"{base_url}/login")
    page.wait_for_url(lambda url: "/login" not in url)
    assert "/login" not in page.url


def test_empty_credentials_show_error(browser, browser_context_args, base_url):
    """Submitting the login form with empty fields shows a validation error."""
    ctx = new_context(browser, browser_context_args)
    page = ctx.new_page()
    try:
        page.goto(f"{base_url}/login")
        # Strip HTML5 `required` attrs so the form actually submits to the server
        # (otherwise the browser intercepts with native validation and nothing renders).
        page.evaluate(
            "document.querySelectorAll('[required]').forEach(el => el.removeAttribute('required'))"
        )
        page.locator("[type=submit]").first.click()
        page.wait_for_selector(".alert, .errorlist, [class*='error']")
        assert "/login" in page.url
    finally:
        ctx.close()


def test_password_field_is_masked(browser, browser_context_args, base_url):
    """The password input has type='password' so the browser masks the value."""
    ctx = new_context(browser, browser_context_args)
    page = ctx.new_page()
    try:
        page.goto(f"{base_url}/login")
        assert page.locator("#id_password[type='password']").count() > 0
    finally:
        ctx.close()
