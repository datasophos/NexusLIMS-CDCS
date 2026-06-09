"""E2E tests for SAML SSO authentication."""

from playwright.sync_api import expect

# Dev IdP test credentials -- hardcoded in deployment/dev-sso/authsources.php
_IDP_USERNAME = "admin"
_IDP_PASSWORD = "admin"


def _sso_login(page, base_url, username=_IDP_USERNAME, password=_IDP_PASSWORD):
    """Walk through the full SSO flow starting from /login. Caller owns the page."""
    page.goto(f"{base_url}/login")
    page.locator("a.btn-lge, a[href*='saml2/login']").first.click()
    expect(page.locator("input[name='username']")).to_be_visible()
    page.locator("input[name='username']").fill(username)
    page.locator("input[name='password']").fill(password)
    page.locator("[type=submit]").first.click()
    page.wait_for_url(f"{base_url}/**")


def test_sso_login_redirects_to_idp(unauthenticated_page, base_url):
    """Clicking the SSO button redirects to the SimpleSAMLphp IdP."""
    page = unauthenticated_page
    page.goto(f"{base_url}/login")
    sso_btn = page.locator("a.btn-lge, a[href*='saml2/login']").first
    sso_btn.click()
    expect(page.locator("input[name='username']")).to_be_visible()
    assert "sso.nexuslims-dev.localhost" in page.url or "saml" in page.url.lower()


def test_sso_login_full_flow(unauthenticated_page, base_url):
    """Full SSO flow: login page -> IdP -> CDCS logged in as admin."""
    page = unauthenticated_page
    page.goto(f"{base_url}/login")
    sso_btn = page.locator("a.btn-lge, a[href*='saml2/login']").first
    sso_btn.click()
    expect(page.locator("input[name='username']")).to_be_visible()

    page.locator("input[name='username']").fill(_IDP_USERNAME)
    page.locator("input[name='password']").fill(_IDP_PASSWORD)
    page.locator("[type=submit]").first.click()

    page.wait_for_url(f"{base_url}/**")
    assert "/login" not in page.url
    assert "sso.nexuslims-dev.localhost" not in page.url


def test_sso_login_user_visible_in_nav(unauthenticated_page, base_url):
    """After SSO login, the username appears in the navigation."""
    page = unauthenticated_page
    _sso_login(page, base_url)
    assert page.locator(f"text={_IDP_USERNAME}").count() > 0


def test_sso_button_present_on_login_page(unauthenticated_page, base_url):
    """The SSO login button is rendered on the login page when SSO is enabled."""
    page = unauthenticated_page
    page.goto(f"{base_url}/login")
    assert page.locator("a.btn-lge, a[href*='saml2/login']").count() > 0


def test_sso_invalid_credentials_stays_on_idp(unauthenticated_page, base_url):
    """A wrong password at the IdP keeps the user on the IdP, not back at CDCS."""
    page = unauthenticated_page
    page.goto(f"{base_url}/login")
    page.locator("a.btn-lge, a[href*='saml2/login']").first.click()
    expect(page.locator("input[name='username']")).to_be_visible()
    page.locator("input[name='username']").fill(_IDP_USERNAME)
    page.locator("input[name='password']").fill("definitely-wrong-password")
    page.locator("[type=submit]").first.click()
    expect(page.locator("input[name='username']")).to_be_visible()
    # Should still be on the IdP host, not redirected back to the CDCS app.
    assert "sso.nexuslims-dev.localhost" in page.url
    assert "/login" not in page.url or "sso.nexuslims-dev.localhost" in page.url


def test_sso_logout_clears_session(unauthenticated_page, base_url):
    """Logging out after SSO login invalidates the Django session."""
    page = unauthenticated_page
    _sso_login(page, base_url)

    # Logout via the user dropdown.
    page.locator("#dropdownDashboard").click()
    page.locator("a[href*='logout'].cdcs-menu-item").wait_for(state="visible")
    with page.expect_navigation():
        page.locator("a[href*='logout'].cdcs-menu-item").click()

    # Visiting a @login_required page should now bounce back to login.
    if "/login" not in page.url and page.locator("#id_username").count() == 0:
        page.goto(f"{base_url}/annotate/check-auth-only/")
    expect(page.locator("#id_username")).to_be_visible()


def test_sso_next_param_redirects_after_login(unauthenticated_page, base_url):
    """SSO from the navigation returns to the page where login was clicked."""
    page = unauthenticated_page
    return_url = f"{base_url}/explore/keyword/?source=sso-login-test"
    page.goto(return_url)
    page.locator("a.btn-custom", has_text="Log In / Sign Up").click()
    page.wait_for_url("**/login?next=*")
    assert "/login" in page.url
    assert "next=" in page.url

    page.locator("a.btn-lge, a[href*='saml2/login']").first.click()
    expect(page.locator("input[name='username']")).to_be_visible()
    page.locator("input[name='username']").fill(_IDP_USERNAME)
    page.locator("input[name='password']").fill(_IDP_PASSWORD)
    page.locator("[type=submit]").first.click()
    page.wait_for_url(f"{base_url}/**")

    assert page.url == return_url


def test_sso_admin_user_has_staff_access(unauthenticated_page, base_url):
    """The SAML 'admin' user maps to the CDCS admin account with staff privileges."""
    page = unauthenticated_page
    _sso_login(page, base_url)

    # Staff users see the 'Administration' link in the user dropdown.
    page.locator("#dropdownDashboard").click()
    admin_link = (
        page.locator("#dropdownDashboard")
        .locator("xpath=following-sibling::ul")
        .locator("a:has-text('Administration')")
    )
    admin_link.wait_for(state="visible")
    assert admin_link.count() > 0


def test_sso_when_already_authenticated_preserves_session(
    unauthenticated_page, base_url
):
    """Visiting /login (or re-clicking the SSO button) while authenticated keeps the session."""
    page = unauthenticated_page
    _sso_login(page, base_url)

    # CDCS redirects authenticated users away from /login outright.
    page.goto(f"{base_url}/login")
    page.wait_for_url(lambda url: "/login" not in url)
    assert "/login" not in page.url
    # Confirm session still intact: the user dropdown is still present.
    assert page.locator("#dropdownDashboard").count() > 0
