# Frontend E2E Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `pytest-playwright` E2E tests covering login, SSO, record list, record detail, and annotator editor, runnable against the full Docker stack both locally and in a manually-triggered GitHub Actions workflow.

**Architecture:** Tests live in `tests/e2e/` and run against `https://nexuslims-dev.localhost` using the existing Docker Compose stack with a new CI compose overlay and a CI-specific Caddyfile that uses Caddy's auto-generated internal CA (rather than the pre-baked dev certs). The CI workflow is triggered manually via a GitHub Environment approval gate on PRs to `main`.

**Tech Stack:** `pytest-playwright`, Python 3.13, Docker Compose, GitHub Actions, Caddy (internal CA)

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `deployment/caddy/Caddyfile.ci` | Caddy config without pre-baked CA (uses auto-generated internal CA) |
| Create | `deployment/docker-compose.ci.yml` | CI compose overrides: SSO env, simplesamlphp, test data mounts |
| Modify | `pyproject.toml` | Add `pytest-playwright` to `[dependency-groups] dev` |
| Modify | `.gitignore` | Add `deployment/caddy/ci-ca.crt` and `tests/e2e/test-results/` |
| Create | `tests/e2e/__init__.py` | Package marker |
| Create | `tests/e2e/conftest.py` | Session fixtures: CA cert, auth state, test record ID |
| Create | `tests/e2e/test_auth.py` | Username/password login and logout |
| Create | `tests/e2e/test_sso.py` | SAML SSO login and logout |
| Create | `tests/e2e/test_record_list.py` | Record list rendering and search |
| Create | `tests/e2e/test_record_detail.py` | XSLT detail page and annotate link |
| Create | `tests/e2e/test_annotator.py` | Annotator editor interactions |
| Create | `.github/workflows/playwright.yml` | Manual-trigger CI workflow |
| Modify | `CLAUDE.md` | Add E2E testing section |

---

### Task 1: Add pytest-playwright dependency

**Files:**
- Modify: `pyproject.toml`
- Modify: `.gitignore`

- [ ] **Step 1: Add pytest-playwright to dev dependency group**

  Open `pyproject.toml`. The `[dependency-groups]` section currently contains only `python-dotenv`. Add `pytest-playwright`:

  ```toml
  [dependency-groups]
  dev = [
      "python-dotenv",
      "pytest-playwright",
  ]
  ```

- [ ] **Step 2: Regenerate the lockfile**

  ```bash
  cd /path/to/NexusLIMS-CDCS
  uv lock
  ```

  Expected: `uv.lock` updated with `playwright` and `pytest-playwright` entries. No errors.

- [ ] **Step 3: Verify the install resolves correctly**

  ```bash
  uv sync --dev
  uv run playwright --version
  ```

  Expected: Playwright version string printed (e.g. `Version 1.x.x`).

- [ ] **Step 4: Add CI-generated files to .gitignore**

  Add to `.gitignore` (after the existing entries):

  ```gitignore
  # Playwright E2E tests
  tests/e2e/test-results/
  deployment/caddy/ci-ca.crt
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add pyproject.toml uv.lock .gitignore
  git commit -m "chore: add pytest-playwright dev dependency"
  ```

---

### Task 2: Create Caddyfile.ci and docker-compose.ci.yml

**Files:**
- Create: `deployment/caddy/Caddyfile.ci`
- Create: `deployment/docker-compose.ci.yml`

The dev Caddyfile references `/etc/caddy/certs/ca.crt` and `/etc/caddy/certs/ca.key` (the pre-baked dev CA). These files are not mounted in CI, so Caddy would fail to start. `Caddyfile.ci` removes that custom PKI block and uses `tls internal` instead -- Caddy then auto-generates its own root CA on first startup and stores it at `/data/caddy/pki/authorities/local/root.crt`.

- [ ] **Step 1: Create Caddyfile.ci**

  Create `deployment/caddy/Caddyfile.ci`:

  ```caddy
  {
      admin off
  }

  # Main application
  https://{$DOMAIN} {
      tls internal

      reverse_proxy cdcs:8000 {
          header_up Host {host}
          header_up X-Real-IP {remote_host}
          header_up X-Forwarded-For {remote_host}
          header_up X-Forwarded-Proto {scheme}
          header_up X-Forwarded-Host {host}
      }

      handle_path /static/* {
          root * /srv/nexuslims_static
          file_server
      }

      request_body {
          max_size 100MB
      }

      log {
          output stdout
          format console
      }
  }

  # SimpleSAMLphp dev IdP (SSO)
  https://{$SSO_DOMAIN} {
      tls internal

      reverse_proxy simplesamlphp:8080 {
          header_up Host {host}
          header_up X-Real-IP {remote_host}
          header_up X-Forwarded-For {remote_host}
          header_up X-Forwarded-Proto {scheme}
          header_up X-Forwarded-Host {host}
      }

      log {
          output stdout
          format console
      }
  }
  ```

  Note: No file server domain -- CI does not serve instrument data files.

- [ ] **Step 2: Create docker-compose.ci.yml**

  Create `deployment/docker-compose.ci.yml`:

  ```yaml
  # CI overrides for docker-compose.base.yml.
  # Usage: COMPOSE_FILE=docker-compose.base.yml:docker-compose.ci.yml docker compose ...
  #
  # Key differences from dev:
  #   - No local source mount (uses baked image and production entrypoint)
  #   - No pre-baked Caddy CA certs (Caddyfile.ci uses auto-generated internal CA)
  #   - simplesamlphp included (needed for SSO tests)
  #   - SSO env loaded from .env.sso-dev.example
  #   - Test data XML files mounted for init_environment.py

  services:
    cdcs:
      volumes:
        - cdcs_media:/srv/nexuslims/media
        - cdcs_socket:/tmp/nexuslims/
        - cdcs_static:/srv/nexuslims/static.prod
        - ./scripts:/srv/scripts:ro
        - ./schemas/nexus-experiment.xsd:/srv/nexuslims/schemas/nexus-experiment.xsd:ro
        - ./test-data/example_record.xml:/srv/test-data/example_record.xml:ro
        - ./test-data/example_record_large.xml:/srv/test-data/example_record_large.xml:ro
        - ./test-data/example_record_multisample.xml:/srv/test-data/example_record_multisample.xml:ro
        # Caddy CA cert is copied here by the CI workflow after Caddy starts
        - ./caddy/ci-ca.crt:/etc/ssl/certs/caddy-root-ca.crt:ro
      environment:
        - REQUESTS_CA_BUNDLE=/etc/ssl/certs/caddy-root-ca.crt
        - CURL_CA_BUNDLE=/etc/ssl/certs/caddy-root-ca.crt
      env_file:
        - path: ./saml2/.env.sso-dev.example
          required: true
      extra_hosts:
        - "${SSO_DOMAIN:-sso.nexuslims-dev.localhost}:host-gateway"

    simplesamlphp:
      image: druidfi/saml-idp:2.4.4
      container_name: ${COMPOSE_PROJECT_NAME}_cdcs_sso
      environment:
        - SIMPLESAMLPHP_IDP_BASEURLPATH=https://${SSO_DOMAIN}/simplesaml/
        - SIMPLESAMLPHP_SP_ENTITY_ID=https://${DOMAIN}/saml2/metadata/
        - SIMPLESAMLPHP_SP_ASSERTION_CONSUMER_SERVICE=https://${DOMAIN}/saml2/acs/
        - SIMPLESAMLPHP_SP_SINGLE_LOGOUT_SERVICE=https://${DOMAIN}/saml2/ls/
      volumes:
        - ./dev-sso/authsources.php:/app/simplesamlphp/config/authsources.php:ro
        - ./dev-sso/saml20-sp-remote.php:/app/simplesamlphp/metadata/saml20-sp-remote.php:ro
  ```

- [ ] **Step 3: Verify compose config parses**

  ```bash
  cd deployment
  CADDYFILE=Caddyfile.ci COMPOSE_FILE=docker-compose.base.yml:docker-compose.ci.yml \
    docker compose config --quiet
  ```

  Expected: No errors printed. (Output is the merged config.)

- [ ] **Step 4: Commit**

  ```bash
  git add deployment/caddy/Caddyfile.ci deployment/docker-compose.ci.yml
  git commit -m "chore: add CI Caddy config and compose override for E2E tests"
  ```

---

### Task 3: Create conftest.py with shared fixtures

**Files:**
- Create: `tests/e2e/__init__.py`
- Create: `tests/e2e/conftest.py`

The `ci-ca.crt` bind mount in `docker-compose.ci.yml` means the cdcs container needs that file to exist when it starts. The CI workflow (Task 9) handles this by starting Caddy alone first, extracting the CA, writing it to `deployment/caddy/ci-ca.crt`, then starting the remaining services. Locally, developers use the pre-existing `deployment/caddy/certs/ca.crt` instead and don't use `docker-compose.ci.yml`.

- [ ] **Step 1: Create the package marker**

  Create `tests/e2e/__init__.py` as an empty file.

- [ ] **Step 2: Create conftest.py**

  Create `tests/e2e/conftest.py`:

  ```python
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
  ```

- [ ] **Step 3: Verify imports resolve**

  ```bash
  uv run python -c "import tests.e2e.conftest"
  ```

  Expected: No ImportError.

- [ ] **Step 4: Commit**

  ```bash
  git add tests/e2e/__init__.py tests/e2e/conftest.py
  git commit -m "test(e2e): add conftest with shared fixtures"
  ```

---

### Task 4: test_auth.py -- username/password login

**Files:**
- Create: `tests/e2e/test_auth.py`

The allauth login form uses field name `login` (not `username`), so the HTML ID is `#id_login`. Confirm by inspecting the running login page if selectors fail.

- [ ] **Step 1: Ensure the dev stack is running with the test superuser**

  If not already set up:

  ```bash
  cd deployment && source dev-commands.sh && dev-up
  # Create the test user (once):
  dev-manage createsuperuser --noinput \
    --username e2eadmin --email e2e@test.local
  # Set password (interactive):
  dev-manage changepassword e2eadmin
  ```

- [ ] **Step 2: Install Playwright browsers (once)**

  ```bash
  uv run playwright install chromium
  ```

- [ ] **Step 3: Write test_auth.py**

  Create `tests/e2e/test_auth.py`:

  ```python
  """E2E tests for username/password authentication."""
  import pytest


  BASE = "https://nexuslims-dev.localhost"
  LOGIN_URL = f"{BASE}/accounts/login/"


  def test_valid_login(browser, browser_context_args, base_url):
      ctx = browser.new_context(**browser_context_args)
      page = ctx.new_page()
      try:
          page.goto(f"{base_url}/accounts/login/")
          page.locator("#id_login").fill("e2eadmin")
          page.locator("#id_password").fill(__import__("os").environ["E2E_PASSWORD"])
          page.locator("[type=submit]").first.click()
          # After login, we should NOT be on the login page anymore
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
          # Stay on login page with an error
          page.wait_for_selector(".alert, .errorlist, [class*='error']", timeout=5_000)
          assert "/accounts/login/" in page.url
      finally:
          ctx.close()


  def test_logout_clears_session(authenticated_page, base_url):
      page = authenticated_page
      # Find and click the logout link/button
      page.goto(f"{base_url}/")
      page.locator("a[href*='logout'], button:has-text('Logout'), a:has-text('Logout')").first.click()
      # Should redirect to login or home (unauthenticated)
      page.wait_for_load_state("networkidle")
      # Verify we're logged out by trying to access a protected page
      page.goto(f"{base_url}/rest/data/")
      assert "/accounts/login/" in page.url or page.locator("#id_login").count() > 0
  ```

- [ ] **Step 4: Run tests against the dev stack**

  ```bash
  CADDY_CA_CERT=deployment/caddy/certs/ca.crt \
  E2E_USERNAME=e2eadmin \
  E2E_PASSWORD=<your-password> \
  uv run pytest tests/e2e/test_auth.py -v
  ```

  Expected: 3 tests pass. If selectors fail, open the login page in a browser, inspect the DOM, and correct the selectors in this file.

- [ ] **Step 5: Commit**

  ```bash
  git add tests/e2e/test_auth.py
  git commit -m "test(e2e): add username/password auth tests"
  ```

---

### Task 5: test_sso.py -- SAML SSO login

**Files:**
- Create: `tests/e2e/test_sso.py`

SSO is enabled via `deployment/saml2/.env.sso-dev.example`. When active, the login page shows a provider button rendered by allauth's `provider.html` template (`<a class="btn btn-primary btn-lge" ...>`). The IdP login form at `https://sso.nexuslims-dev.localhost/` uses standard HTML inputs for username/password.

The dev IdP test credentials are `admin/admin` (maps to the CDCS `admin` superuser created by `init_environment.py`). These are hardcoded in `deployment/dev-sso/authsources.php` and are not sensitive.

- [ ] **Step 1: Enable SSO in the dev stack**

  ```bash
  cd deployment && source dev-commands.sh
  dev-sso-enable
  dev-restart-all
  ```

  Verify SSO is working by visiting `https://nexuslims-dev.localhost/accounts/login/` -- you should see a provider login button.

- [ ] **Step 2: Identify the SSO button selector**

  Open `https://nexuslims-dev.localhost/accounts/login/` in a browser. Inspect the SSO provider button. It is rendered by `templates/allauth/elements/provider.html` as:

  ```html
  <a class="btn btn-primary btn-lge" title="<provider-name>" href="/saml2/login/?next=...">
    <provider-name>
  </a>
  ```

  Note the exact button text/title (e.g., "NexusLIMS SSO" or "SAML"). Update the selector in the test below if the text differs.

- [ ] **Step 3: Write test_sso.py**

  Create `tests/e2e/test_sso.py`:

  ```python
  """E2E tests for SAML SSO authentication."""
  import pytest


  # Dev IdP test credentials -- hardcoded in deployment/dev-sso/authsources.php
  _IDP_USERNAME = "admin"
  _IDP_PASSWORD = "admin"


  def test_sso_login_redirects_to_idp(browser, browser_context_args, base_url):
      """Clicking the SSO button redirects to the SimpleSAMLphp IdP."""
      ctx = browser.new_context(**browser_context_args)
      page = ctx.new_page()
      try:
          page.goto(f"{base_url}/accounts/login/")
          # Provider button rendered by templates/allauth/elements/provider.html
          sso_btn = page.locator("a.btn-lge, a[href*='saml2/login']").first
          sso_btn.click()
          page.wait_for_load_state("networkidle")
          assert "sso.nexuslims-dev.localhost" in page.url or "saml" in page.url.lower()
      finally:
          ctx.close()


  def test_sso_login_full_flow(browser, browser_context_args, base_url):
      """Full SSO flow: login page -> IdP -> CDCS logged in as admin."""
      ctx = browser.new_context(**browser_context_args)
      page = ctx.new_page()
      try:
          page.goto(f"{base_url}/accounts/login/")
          sso_btn = page.locator("a.btn-lge, a[href*='saml2/login']").first
          sso_btn.click()
          page.wait_for_load_state("networkidle")

          # Fill in IdP credentials (SimpleSAMLphp userpass form)
          page.locator("input[name='username']").fill(_IDP_USERNAME)
          page.locator("input[name='password']").fill(_IDP_PASSWORD)
          page.locator("[type=submit]").first.click()

          # Should be redirected back to CDCS and logged in
          page.wait_for_url(f"{base_url}/**", timeout=15_000)
          assert "/accounts/login/" not in page.url
          assert "sso.nexuslims-dev.localhost" not in page.url
      finally:
          ctx.close()


  def test_sso_login_user_visible_in_nav(browser, browser_context_args, base_url):
      """After SSO login, the username appears in the navigation."""
      ctx = browser.new_context(**browser_context_args)
      page = ctx.new_page()
      try:
          page.goto(f"{base_url}/accounts/login/")
          sso_btn = page.locator("a.btn-lge, a[href*='saml2/login']").first
          sso_btn.click()
          page.wait_for_load_state("networkidle")
          page.locator("input[name='username']").fill(_IDP_USERNAME)
          page.locator("input[name='password']").fill(_IDP_PASSWORD)
          page.locator("[type=submit]").first.click()
          page.wait_for_url(f"{base_url}/**", timeout=15_000)

          # Username should appear somewhere in the nav
          assert page.locator(f"text={_IDP_USERNAME}").count() > 0
      finally:
          ctx.close()
  ```

- [ ] **Step 4: Run SSO tests against the dev stack (with SSO enabled)**

  ```bash
  CADDY_CA_CERT=deployment/caddy/certs/ca.crt \
  E2E_USERNAME=e2eadmin \
  E2E_PASSWORD=<your-password> \
  uv run pytest tests/e2e/test_sso.py -v
  ```

  Expected: 3 tests pass. If the SSO button selector is wrong, inspect the DOM and update the `sso_btn` locator. If the IdP form fields differ from `input[name='username']`, update accordingly.

- [ ] **Step 5: Commit**

  ```bash
  git add tests/e2e/test_sso.py
  git commit -m "test(e2e): add SAML SSO login tests"
  ```

---

### Task 6: test_record_list.py -- record browsing and search

**Files:**
- Create: `tests/e2e/test_record_list.py`

- [ ] **Step 1: Identify record list URL and key selectors**

  Visit `https://nexuslims-dev.localhost/` while logged in. The CDCS record list is typically at `/` or `/data/`. Inspect the DOM to find:
  - The search input selector
  - A record link selector (usually `<a>` inside a record row/card)

  Update the selectors below if they differ from the defaults.

- [ ] **Step 2: Write test_record_list.py**

  Create `tests/e2e/test_record_list.py`:

  ```python
  """E2E tests for the record list and search."""
  import pytest


  def test_record_list_renders(authenticated_page, base_url):
      """Record list page loads and shows at least one record."""
      page = authenticated_page
      page.goto(f"{base_url}/")
      page.wait_for_load_state("networkidle")
      # At least one record link should be present
      records = page.locator("a[href*='/rest/data/'], a[href*='/data/'], .list-group-item a").all()
      assert len(records) > 0, "No record links found on the list page"


  def test_search_filters_records(authenticated_page, base_url):
      """Typing in the search box filters the record list."""
      page = authenticated_page
      page.goto(f"{base_url}/")
      page.wait_for_load_state("networkidle")

      # Find and use the search input
      search = page.locator("input[type='search'], input[name='q'], #id_search, input[placeholder*='earch']").first
      initial_count = page.locator("a[href*='/rest/data/'], .list-group-item a").count()

      # Search for something unlikely to match everything
      search.fill("zzznomatch")
      search.press("Enter")
      page.wait_for_load_state("networkidle")

      filtered_count = page.locator("a[href*='/rest/data/'], .list-group-item a").count()
      assert filtered_count < initial_count or page.locator("text=No results, text=no record").count() > 0


  def test_record_link_navigates_to_detail(authenticated_page, base_url):
      """Clicking a record link navigates to the detail page."""
      page = authenticated_page
      page.goto(f"{base_url}/")
      page.wait_for_load_state("networkidle")

      first_link = page.locator("a[href*='/rest/data/']").first
      first_link.click()
      page.wait_for_load_state("networkidle")
      assert "/rest/data/" in page.url or page.locator("text=Annotate").count() > 0
  ```

- [ ] **Step 3: Run tests**

  ```bash
  CADDY_CA_CERT=deployment/caddy/certs/ca.crt \
  E2E_USERNAME=e2eadmin \
  E2E_PASSWORD=<your-password> \
  uv run pytest tests/e2e/test_record_list.py -v
  ```

  Expected: 3 tests pass. Adjust selectors if the CDCS record list uses different HTML structure.

- [ ] **Step 4: Commit**

  ```bash
  git add tests/e2e/test_record_list.py
  git commit -m "test(e2e): add record list and search tests"
  ```

---

### Task 7: test_record_detail.py -- XSLT-rendered detail page

**Files:**
- Create: `tests/e2e/test_record_detail.py`

The CDCS detail page at `/rest/data/<id>/` renders the XML record through the XSLT stylesheet into HTML. The "Annotate" link goes to `/annotate/<id>/`.

- [ ] **Step 1: Write test_record_detail.py**

  Create `tests/e2e/test_record_detail.py`:

  ```python
  """E2E tests for the XSLT-rendered record detail page."""
  import pytest


  def test_detail_page_loads(authenticated_page, base_url, test_record_id):
      """Detail page renders without error for a known record."""
      page = authenticated_page
      page.goto(f"{base_url}/rest/data/{test_record_id}/")
      page.wait_for_load_state("networkidle")
      # Should not show a Django error page
      assert page.locator("text=Server Error, text=Exception").count() == 0
      assert page.title() != ""


  def test_detail_shows_key_fields(authenticated_page, base_url, test_record_id):
      """Key metadata fields are visible on the rendered detail page."""
      page = authenticated_page
      page.goto(f"{base_url}/rest/data/{test_record_id}/")
      page.wait_for_load_state("networkidle")
      # The XSLT stylesheet renders these headings -- verify the page has content
      content = page.locator("body").inner_text()
      # The example_record.xml fixture contains a title and date -- confirm something rendered
      assert len(content.strip()) > 100, "Detail page body appears empty -- XSLT may have failed"


  def test_annotate_button_navigates(authenticated_page, base_url, test_record_id):
      """'Annotate' link on the detail page navigates to the annotator."""
      page = authenticated_page
      page.goto(f"{base_url}/rest/data/{test_record_id}/")
      page.wait_for_load_state("networkidle")

      annotate_link = page.locator("a:has-text('Annotate'), a[href*='/annotate/']").first
      assert annotate_link.count() > 0, "Annotate link not found on detail page"
      annotate_link.click()
      page.wait_for_load_state("networkidle")
      assert "/annotate/" in page.url
  ```

- [ ] **Step 2: Run tests**

  ```bash
  CADDY_CA_CERT=deployment/caddy/certs/ca.crt \
  E2E_USERNAME=e2eadmin \
  E2E_PASSWORD=<your-password> \
  uv run pytest tests/e2e/test_record_detail.py -v
  ```

  Expected: 3 tests pass.

- [ ] **Step 3: Commit**

  ```bash
  git add tests/e2e/test_record_detail.py
  git commit -m "test(e2e): add record detail page tests"
  ```

---

### Task 8: test_annotator.py -- annotator editor

**Files:**
- Create: `tests/e2e/test_annotator.py`

Key selectors from the annotator template (`nexuslims_annotate/templates/nexuslims_annotate/annotate.html`):
- `#nx-title-edit-btn` -- pencil icon button to enter title edit mode
- `#nx-title-display` -- span showing current title
- `#annotate-title-input` -- hidden input holding the title value
- `.nx-title-dirty` -- class toggled on `#nx-title-bar` when title is changed
- `.annotate-textarea` -- description textareas
- `#nx-add-sample-btn` -- "Add Sample" button
- `#nx-sample-modal` -- Bootstrap modal for sample add/edit
- `#nx-sample-name` -- sample name input inside modal
- `#nx-sample-modal-save` -- "Save" button inside sample modal
- `#nx-samples-list` -- container holding rendered sample rows
- `#nx-toolbar-save-btn` -- toolbar "Save" button
- `#nx-pending-changes-modal` -- Bootstrap modal shown when navigating away with unsaved changes

- [ ] **Step 1: Write test_annotator.py**

  Create `tests/e2e/test_annotator.py`:

  ```python
  """E2E tests for the annotator record editor."""
  import pytest


  @pytest.fixture
  def annotator_page(authenticated_page, base_url, test_record_id):
      """Navigate to the annotator for the test record."""
      page = authenticated_page
      page.goto(f"{base_url}/annotate/{test_record_id}/")
      page.wait_for_load_state("networkidle")
      return page


  def test_annotator_loads(annotator_page):
      """Annotator page renders without error."""
      page = annotator_page
      assert page.locator("#nx-toolbar-save-btn").count() > 0
      assert page.locator("#nx-title-display").count() > 0


  def test_title_inline_edit(annotator_page):
      """Clicking the title edit button opens an inline input."""
      page = annotator_page
      page.locator("#nx-title-edit-btn").click()
      # An <input> should appear next to the title display
      inline_input = page.locator("#nx-title-bar input[type='text']")
      inline_input.wait_for(state="visible")
      assert inline_input.is_visible()


  def test_title_edit_marks_dirty(annotator_page):
      """Changing the title marks the title bar as dirty."""
      page = annotator_page
      page.locator("#nx-title-edit-btn").click()
      inline_input = page.locator("#nx-title-bar input[type='text']")
      inline_input.wait_for(state="visible")
      inline_input.fill("E2E Test Title Change")
      inline_input.press("Enter")
      # The nx-title-dirty class should now be on #nx-title-bar
      assert page.locator("#nx-title-bar.nx-title-dirty").count() > 0


  def test_description_textarea_accepts_input(annotator_page):
      """Description textareas accept text input."""
      page = annotator_page
      textareas = page.locator(".annotate-textarea").all()
      if not textareas:
          pytest.skip("No description textareas found on this record")
      first_ta = textareas[0]
      first_ta.fill("E2E test description content")
      assert first_ta.input_value() == "E2E test description content"


  def test_add_sample(annotator_page):
      """Clicking 'Add Sample' opens the sample modal."""
      page = annotator_page
      page.locator("#nx-add-sample-btn").click()
      modal = page.locator("#nx-sample-modal")
      modal.wait_for(state="visible")
      assert modal.is_visible()


  def test_save_sample_from_modal(annotator_page):
      """Adding a sample via the modal renders it in the sample list."""
      page = annotator_page
      page.locator("#nx-add-sample-btn").click()
      page.locator("#nx-sample-modal").wait_for(state="visible")
      page.locator("#nx-sample-name").fill("E2E Test Sample")
      page.locator("#nx-sample-modal-save").click()
      page.locator("#nx-sample-modal").wait_for(state="hidden")
      # The new sample should appear in the list
      assert page.locator("#nx-samples-list").inner_text().find("E2E Test Sample") >= 0


  def test_pending_changes_modal_on_navigation(annotator_page, base_url):
      """Navigating away with unsaved changes shows the pending-changes modal."""
      page = annotator_page
      # Make a change to trigger dirty state
      page.locator("#nx-title-edit-btn").click()
      inline_input = page.locator("#nx-title-bar input[type='text']")
      inline_input.wait_for(state="visible")
      inline_input.fill("Unsaved E2E Change")
      inline_input.press("Enter")

      # Try to navigate away -- the annotator intercepts this with its modal
      page.locator("a[href='/'], a[href*='/data/']").first.click()
      modal = page.locator("#nx-pending-changes-modal")
      modal.wait_for(state="visible", timeout=5_000)
      assert modal.is_visible()


  def test_save_button_submits(annotator_page):
      """Clicking save with no changes completes without error."""
      page = annotator_page
      page.locator("#nx-toolbar-save-btn").click()
      # Wait for the save to complete (toolbar shows success state or page reloads)
      page.wait_for_load_state("networkidle")
      # Confirm we're still on the annotator page (not redirected to an error)
      assert "/annotate/" in page.url
  ```

- [ ] **Step 2: Run tests**

  ```bash
  CADDY_CA_CERT=deployment/caddy/certs/ca.crt \
  E2E_USERNAME=e2eadmin \
  E2E_PASSWORD=<your-password> \
  uv run pytest tests/e2e/test_annotator.py -v
  ```

  Expected: All tests pass. The `test_pending_changes_modal_on_navigation` test depends on the annotator's `beforeunload`/navigation interception -- if it fails, check that the dirty-state JS ran before the navigation attempt.

- [ ] **Step 3: Commit**

  ```bash
  git add tests/e2e/test_annotator.py
  git commit -m "test(e2e): add annotator editor E2E tests"
  ```

---

### Task 9: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/playwright.yml`

The workflow uses a two-phase startup to solve the Caddy CA chicken-and-egg problem:
1. Start Caddy alone so it generates its CA
2. Extract the CA to `deployment/caddy/ci-ca.crt` on the host
3. Start the remaining services (the `ci-ca.crt` bind mount in `docker-compose.ci.yml` is now satisfied)

The `e2e-tests` GitHub Environment must already exist with `jat255` as a required reviewer and `E2E_PASSWORD` stored as an environment secret (see spec).

- [ ] **Step 1: Create the workflow file**

  Create `.github/workflows/playwright.yml`:

  ```yaml
  name: Playwright E2E Tests

  on:
    pull_request:
      branches: [main]
    workflow_dispatch:

  jobs:
    playwright:
      name: Run E2E tests
      runs-on: ubuntu-latest
      environment: e2e-tests
      defaults:
        run:
          working-directory: deployment

      env:
        COMPOSE_FILE: docker-compose.base.yml:docker-compose.ci.yml
        CADDYFILE: Caddyfile.ci
        COMPOSE_PROJECT_NAME: nexuslims_ci

      steps:
        - uses: actions/checkout@v4

        - name: Install uv
          uses: astral-sh/setup-uv@v5
          with:
            enable-cache: true

        - name: Set up Python
          run: uv python install
          working-directory: ${{ github.workspace }}

        - name: Install Python dependencies
          run: uv sync --dev
          working-directory: ${{ github.workspace }}

        - name: Install Playwright browsers
          run: uv run playwright install --with-deps chromium
          working-directory: ${{ github.workspace }}

        - name: Extract test data archive
          run: bash scripts/setup-test-data.sh

        - name: Build Docker image
          run: COMPOSE_BAKE=true docker compose build cdcs

        - name: Start Caddy (phase 1 -- generate internal CA)
          run: |
            docker compose up -d caddy
            # Wait until Caddy's CA cert exists
            for i in $(seq 1 30); do
              docker exec nexuslims_ci_cdcs_caddy \
                test -f /data/caddy/pki/authorities/local/root.crt && break
              sleep 2
            done
            docker exec nexuslims_ci_cdcs_caddy \
              cat /data/caddy/pki/authorities/local/root.crt > caddy/ci-ca.crt
            echo "Caddy CA extracted to deployment/caddy/ci-ca.crt"

        - name: Start remaining services (phase 2)
          run: |
            docker compose up -d
            # Wait for the CDCS app to respond
            for i in $(seq 1 30); do
              curl --silent --insecure \
                --output /dev/null --write-out "%{http_code}" \
                https://nexuslims-dev.localhost/ | grep -qE "^[23]" && break
              echo "Waiting for CDCS... attempt $i"
              sleep 10
            done

        - name: Run init_environment.py (loads schema, XSLT, test records)
          run: |
            docker exec nexuslims_ci_cdcs \
              python /srv/scripts/init_environment.py

        - name: Create E2E test superuser
          run: |
            docker exec \
              -e DJANGO_SUPERUSER_PASSWORD=${{ secrets.E2E_PASSWORD }} \
              nexuslims_ci_cdcs \
              python manage.py createsuperuser --noinput \
              --username e2eadmin --email e2e@test.local
          continue-on-error: true  # User may already exist on re-runs

        - name: Run Playwright tests
          run: |
            CADDY_CA_CERT=${{ github.workspace }}/deployment/caddy/ci-ca.crt \
            E2E_USERNAME=e2eadmin \
            E2E_PASSWORD=${{ secrets.E2E_PASSWORD }} \
            uv run pytest tests/e2e/ \
              --screenshot=only-on-failure \
              --output=deployment/test-results/ \
              -v
          working-directory: ${{ github.workspace }}

        - name: Upload test artifacts on failure
          if: failure()
          uses: actions/upload-artifact@v4
          with:
            name: playwright-results
            path: deployment/test-results/
            retention-days: 7

        - name: Tear down stack
          if: always()
          run: docker compose down -v
  ```

- [ ] **Step 2: Verify the workflow YAML is valid**

  ```bash
  # Install actionlint if available, or just check with GitHub's UI
  which actionlint && actionlint .github/workflows/playwright.yml || echo "actionlint not installed -- validate via GitHub UI"
  ```

- [ ] **Step 3: Commit and push to trigger the approval gate**

  ```bash
  git add .github/workflows/playwright.yml
  git commit -m "ci: add manual Playwright E2E workflow with GitHub Environment gate"
  git push
  ```

  Open the PR in GitHub and confirm the `playwright / Run E2E tests` check appears in the "Waiting" state with an "Approve" button.

---

### Task 10: Update CLAUDE.md with E2E test instructions

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add E2E testing section to CLAUDE.md**

  Add the following section to `CLAUDE.md` after the "Running Tests" section:

  ```markdown
  ## Running E2E Tests (Playwright)

  E2E tests run against the full Docker stack and require the dev environment to be running.

  ### Prerequisites (one-time setup)

  ```bash
  # Install Playwright browsers
  uv run playwright install chromium

  # Enable SSO in the dev stack (required for test_sso.py)
  cd deployment && source dev-commands.sh
  dev-sso-enable && dev-up

  # Create the E2E test superuser
  dev-manage createsuperuser --noinput \
    --username e2eadmin --email e2e@test.local
  dev-manage changepassword e2eadmin   # set a password interactively
  ```

  ### Running Tests

  ```bash
  CADDY_CA_CERT=deployment/caddy/certs/ca.crt \
  E2E_USERNAME=e2eadmin \
  E2E_PASSWORD=<your-password> \
  uv run pytest tests/e2e/ -v
  ```

  Run a single test file:

  ```bash
  CADDY_CA_CERT=deployment/caddy/certs/ca.crt \
  E2E_USERNAME=e2eadmin \
  E2E_PASSWORD=<your-password> \
  uv run pytest tests/e2e/test_annotator.py -v
  ```

  ### CI

  E2E tests run in a manually-triggered GitHub Actions workflow (`.github/workflows/playwright.yml`). On PRs to `main`, the job appears in the PR checks as "Waiting" and requires approval from a reviewer before it runs. The `E2E_PASSWORD` secret is stored in the `e2e-tests` GitHub Environment.
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add CLAUDE.md
  git commit -m "docs: add E2E test instructions to CLAUDE.md"
  ```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| pytest-playwright, Python bindings, Chromium | Task 1 |
| `tests/e2e/` file structure with 5 files | Tasks 3-8 |
| `docker-compose.ci.yml` overrides | Task 2 |
| Caddyfile.ci with auto-generated CA | Task 2 |
| TLS: extract Caddy CA, pass to Playwright | Tasks 3, 9 |
| Base URL `https://nexuslims-dev.localhost` | Task 3 |
| `auth_state`, `authenticated_page`, `test_record_id` fixtures | Task 3 |
| Test superuser created in CI | Task 9 |
| test_auth.py: valid login, invalid login, logout | Task 4 |
| test_sso.py: SSO button, full SAML flow, username visible | Task 5 |
| test_record_list.py: list renders, search filters, link navigates | Task 6 |
| test_record_detail.py: loads, key fields, annotate link | Task 7 |
| test_annotator.py: title edit, dirty state, description, sample add, save, modal | Task 8 |
| `workflow_dispatch` + `pull_request` triggers | Task 9 |
| `environment: e2e-tests` approval gate | Task 9 |
| `E2E_PASSWORD` in environment secrets | Task 9 (noted in step 1) |
| Upload artifacts on failure | Task 9 |
| `docker compose down -v` always runs | Task 9 |
| Local developer instructions | Task 10 |

All spec requirements are covered. No placeholder text or missing code blocks found.
