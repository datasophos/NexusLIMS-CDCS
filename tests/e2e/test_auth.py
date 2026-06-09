"""E2E tests for username/password authentication."""

from playwright.sync_api import expect

_USERNAME = "admin"
_PASSWORD = "admin"


def test_valid_login(unauthenticated_page, base_url):
    page = unauthenticated_page
    page.goto(f"{base_url}/login")
    page.locator("#id_username").fill(_USERNAME)
    page.locator("#id_password").fill(_PASSWORD)
    page.locator("[type=submit]").first.click()
    page.wait_for_url(lambda url: "/login" not in url)
    assert "/login" not in page.url


def test_invalid_login_shows_error(unauthenticated_page, base_url):
    page = unauthenticated_page
    page.goto(f"{base_url}/login")
    page.locator("#id_username").fill(_USERNAME)
    page.locator("#id_password").fill("definitely-wrong-password")
    page.locator("[type=submit]").first.click()
    page.wait_for_selector(".alert, .errorlist, [class*='error']")
    assert "/login" in page.url


def test_logout_clears_session(unauthenticated_page, base_url):
    # Use a dedicated context rather than the shared authenticated_page fixture.
    # Logging out invalidates the server-side session; reusing the session-scoped
    # auth_state after logout would leave other tests with stale cookies.
    page = unauthenticated_page
    page.goto(f"{base_url}/login")
    page.locator("#id_username").fill(_USERNAME)
    page.locator("#id_password").fill(_PASSWORD)
    page.locator("[type=submit]").first.click()
    page.wait_for_url(lambda url: "/login" not in url)

    # Logout is inside the #dropdownDashboard Bootstrap menu — open it first.
    page.locator("#dropdownDashboard").click()
    page.locator("a[href*='logout'].cdcs-menu-item").wait_for(state="visible")
    with page.expect_navigation():
        page.locator("a[href*='logout'].cdcs-menu-item").click()

    # Confirm the session is gone: a protected page should redirect to login.
    if "/login" not in page.url and page.locator("#id_username").count() == 0:
        page.goto(f"{base_url}/annotate/check-auth-only/")
    expect(page.locator("#id_username")).to_be_visible()


def test_next_param_redirects_after_login(unauthenticated_page, base_url):
    """Accessing a protected page while logged out then logging in lands on that page."""
    page = unauthenticated_page
    # Hit a @login_required view unauthenticated; Django appends ?next=...
    page.goto(f"{base_url}/annotate/check-auth-only/")
    assert "/login" in page.url
    assert "next=" in page.url

    page.locator("#id_username").fill(_USERNAME)
    page.locator("#id_password").fill(_PASSWORD)
    page.locator("[type=submit]").first.click()
    page.wait_for_url("**/annotate/check-auth-only/")

    # Should land at /annotate/check-auth-only/, not the default post-login page.
    assert "/annotate/check-auth-only/" in page.url


def test_nav_login_redirects_to_current_page(unauthenticated_page, base_url):
    """Logging in from the navigation returns to the page where login was clicked."""
    page = unauthenticated_page
    return_url = f"{base_url}/explore/keyword/?source=login-test"
    page.goto(return_url)
    page.locator("a.btn-custom", has_text="Log In / Sign Up").click()
    page.wait_for_url("**/login?next=*")
    assert "/login" in page.url
    assert "next=" in page.url

    page.locator("#id_username").fill(_USERNAME)
    page.locator("#id_password").fill(_PASSWORD)
    page.locator("[type=submit]").first.click()
    expect(page).to_have_url(return_url)


def test_login_page_redirects_when_already_authenticated(authenticated_page, base_url):
    """Navigating to /login while already logged in redirects away from the login form."""
    page = authenticated_page
    page.goto(f"{base_url}/login")
    page.wait_for_url(lambda url: "/login" not in url)
    assert "/login" not in page.url


def test_empty_credentials_show_error(unauthenticated_page, base_url):
    """Submitting the login form with empty fields shows a validation error."""
    page = unauthenticated_page
    page.goto(f"{base_url}/login")
    # Strip HTML5 `required` attrs so the form actually submits to the server
    # (otherwise the browser intercepts with native validation and nothing renders).
    page.evaluate(
        "document.querySelectorAll('[required]').forEach(el => el.removeAttribute('required'))"
    )
    page.locator("[type=submit]").first.click()
    page.wait_for_selector(".alert, .errorlist, [class*='error']")
    assert "/login" in page.url


def test_password_field_is_masked(unauthenticated_page, base_url):
    """The password input has type='password' so the browser masks the value."""
    page = unauthenticated_page
    page.goto(f"{base_url}/login")
    assert page.locator("#id_password[type='password']").count() > 0
