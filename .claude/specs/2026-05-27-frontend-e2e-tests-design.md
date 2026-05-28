# Frontend E2E Tests Design

**Date:** 2026-05-27
**Issue:** #8
**Status:** Approved

## Overview

Add Playwright-based end-to-end tests that run against the full Docker stack to protect
against UI regressions in the annotator editor, record list, record detail (XSLT), and
authentication flows. Tests are triggered manually via a GitHub Environment approval gate
on PRs targeting `main`.

## Framework

`pytest-playwright` (Python bindings). No Node.js toolchain required. Single browser
(Chromium) for CI. Fits the existing `uv`/`pytest` setup.

## Test Location

```
tests/e2e/
├── conftest.py           # shared fixtures
├── test_auth.py          # login / logout
├── test_record_list.py   # record browsing and search
├── test_record_detail.py # XSLT-rendered detail page
└── test_annotator.py     # annotator editor interactions
```

Kept separate from `tests/` (unit tests) so `runtests.py` continues to run only unit
tests. E2E tests are run with `pytest tests/e2e/` directly.

## Stack in CI

### Docker Compose

Three compose files:

| File | Purpose |
|---|---|
| `deployment/docker-compose.base.yml` | Existing base (Caddy, Postgres, Redis, Django) |
| `deployment/docker-compose.dev.yml` | Existing dev overrides (source mount, dev certs, SSO) |
| `deployment/docker-compose.ci.yml` | New CI overrides (no source mount, no dev certs, no SSO) |

`docker-compose.ci.yml` overrides from dev:
- Removes local source code mount (uses baked image)
- Removes `deployment/caddy/certs/` mount (Caddy generates its own CA fresh)
- Removes `simplesamlphp` service
- Exposes Caddy port 443 on `127.0.0.1:443`

### TLS / HTTPS

Caddy generates a fresh root CA on first startup. After `docker compose up -d`, the CI
workflow extracts it:

```bash
docker exec ${COMPOSE_PROJECT_NAME}_cdcs_caddy \
  cat /data/caddy/pki/authorities/local/root.crt > /tmp/caddy-root.crt
```

The cert path is passed to Playwright via the `CADDY_CA_CERT` env var. Tests use
`extra_ca_certs=[os.environ["CADDY_CA_CERT"]]` in the browser context. No
`ignore_https_errors`. The `.localhost` domain resolves to `127.0.0.1` natively on
Linux (ubuntu-latest).

### Base URL

`https://nexuslims-dev.localhost` -- same domain as local dev. Overridable via
`PLAYWRIGHT_BASE_URL` env var so developers can point at their own running stack.

## Test Fixtures (`conftest.py`)

Session-scoped where possible to avoid repeated logins/setups; `authenticated_page` is function-scoped to give each test a fresh page.

| Fixture | Scope | Description |
|---|---|---|
| `base_url` | session | `PLAYWRIGHT_BASE_URL` env var, defaults to `https://nexuslims-dev.localhost` |
| `browser_context` | session | Chromium context with `CADDY_CA_CERT` trusted |
| `auth_state` | session | Logs in once, saves Playwright storage state (cookies) to temp file |
| `authenticated_page` | function | Fresh page pre-loaded with `auth_state`; used by all tests needing auth |
| `test_record_id` | session | Queries CDCS REST API to return the ID of the first loaded record |

## Test Superuser

Created in the CI workflow before tests run:

```bash
docker exec -e DJANGO_SUPERUSER_PASSWORD=$E2E_PASSWORD \
  ${COMPOSE_PROJECT_NAME}_cdcs \
  python manage.py createsuperuser --noinput \
  --username e2eadmin --email e2e@test.local
```

Credentials are provided to tests via `E2E_USERNAME=e2eadmin` and `E2E_PASSWORD` env
vars. The same approach works locally: developers run `dev-manage createsuperuser` once
with the same credentials and export the env vars.

## Test Coverage

### `test_auth.py`
- Valid login with correct credentials redirects to home
- Invalid credentials shows error message
- Logout clears session and redirects to login

### `test_record_list.py`
- List page renders and contains at least one record
- Search input filters the displayed records
- Clicking a record link navigates to the detail page

### `test_record_detail.py`
- Detail page loads for a known record ID (XSLT-rendered)
- Key fields visible (title, date, instrument)
- "Annotate" button is present and navigates to the annotator

### `test_annotator.py`
- Title inline edit: clicking title activates input, typing changes value
- Dirty state: editing title shows pending-changes indicator
- Description edit: activity or dataset description textarea accepts input
- Sample add: "Add sample" creates a new sample row
- Sample reorder: drag-and-drop changes order (Sortable.js)
- Activity add: "Add activity" appends a new activity
- Activity delete: deleting an activity removes it from the DOM
- Pending-changes modal: navigating away while dirty shows confirmation modal
- Save: submitting saves changes and shows success state; reloaded page reflects changes

## CI Workflow (`.github/workflows/playwright.yml`)

### Triggers

```yaml
on:
  pull_request:
    branches: [main]
  workflow_dispatch:
```

The `playwright` job references `environment: e2e-tests`, which has `jat255` as a
required reviewer. Every PR push to `main` queues the job; it does not run until a
reviewer approves via the GitHub PR checks UI. `workflow_dispatch` allows manual runs on
any branch from the Actions tab.

### Steps

All `docker compose` commands run from `deployment/` with `COMPOSE_FILE=docker-compose.base.yml:docker-compose.ci.yml`.

1. Checkout repo
2. Install uv + Python, `uv sync --dev`
3. `uv run playwright install --with-deps chromium`
4. `COMPOSE_BAKE=true docker compose build cdcs`
5. `docker compose up -d` + retry health check loop (`curl --insecure https://nexuslims-dev.localhost/` -- `--insecure` only here since the CA cert hasn't been extracted yet)
6. Extract Caddy CA cert to `/tmp/caddy-root.crt`
7. `docker exec ... python /srv/scripts/init_environment.py` (loads schema, XSLT, test records)
8. Create test superuser via `createsuperuser --noinput`
9. `uv run pytest tests/e2e/ --screenshot=only-on-failure --output=test-results/`
10. `actions/upload-artifact` with `test-results/` (runs on failure only)
11. `docker compose down -v` (always runs)

### Secrets

One secret stored in the `e2e-tests` GitHub Environment (not as a repo secret):

| Name | Value |
|---|---|
| `E2E_PASSWORD` | Password for the `e2eadmin` test superuser |

## Dependencies

Add to `pyproject.toml` dev dependencies:

```toml
[dependency-groups]
dev = [
    "pytest-playwright",
    ...
]
```

No other new dependencies. `playwright` is a transitive dependency of `pytest-playwright`.

## Local Developer Usage

To run E2E tests locally against the dev stack:

```bash
# Start dev stack (if not already running)
cd deployment && source dev-commands.sh && dev-up

# Create test superuser (once)
dev-manage createsuperuser --noinput \
  --username e2eadmin --email e2e@test.local

# Install Playwright browsers (once)
uv run playwright install chromium

# Run E2E tests
CADDY_CA_CERT=deployment/caddy/certs/ca.crt \
E2E_USERNAME=e2eadmin \
E2E_PASSWORD=<your-password> \
uv run pytest tests/e2e/ -v
```
