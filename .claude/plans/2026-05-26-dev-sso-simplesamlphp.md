# Dev SSO with SimpleSAMLphp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a SimpleSAMLphp container to the dev Docker Compose stack so the existing djangosaml2/pysaml2 SAML SSO pathway in CDCS can be exercised during local development without an external IdP.

**Architecture:** SimpleSAMLphp runs as a Docker service behind the existing Caddy reverse proxy at `https://sso.nexuslims-dev.localhost`. CDCS already wires up djangosaml2 when `ENABLE_SAML2_SSO_AUTH=True`; we configure it to point at SimpleSAMLphp's metadata URL. Two static test users (`user`/`user` and `admin`/`admin`) mirror the existing dev accounts. All changes are dev-only: the base compose and prod configs are untouched.

**Tech Stack:** `kenchan0130/simplesamlphp` Docker image, djangosaml2 / pysaml2 (already in virtualenv), Caddy (existing), Docker Compose (existing).

---

## Background: How the SAML stack works in this codebase

- **`ENABLE_SAML2_SSO_AUTH=True`** (in `deployment/saml2/.env`) activates djangosaml2 and adds `saml2/` URL routes via `core_main_app/utils/urls.py`.
- **SP entity ID**: `https://nexuslims-dev.localhost/saml2/metadata/` (hard-coded in `load_saml_config_from_env`).
- **SP ACS URL**: `https://nexuslims-dev.localhost/saml2/acs/`.
- **SP SLS URLs**: `https://nexuslims-dev.localhost/saml2/ls/` and `/saml2/ls/post/`.
- **Attribute mapping**: pysaml2 receives SAML attributes, passes them to djangosaml2, which applies `SAML_ATTRIBUTE_MAPPING` to populate Django user fields.
- **`required_attributes`** in the pysaml2 SP config checks for `["givenName", "sn", "mail"]`. SimpleSAMLphp must send those exact attribute names.
- The CDCS container already trusts Caddy's internal CA via `REQUESTS_CA_BUNDLE=/etc/ssl/certs/caddy-root-ca.crt`, so pysaml2's `requests`-based metadata fetch will succeed over `https://sso.nexuslims-dev.localhost`.

## File Map

| File | Action | Purpose |
|---|---|---|
| `deployment/sso/authsources.php` | **Create** | SimpleSAMLphp test user definitions |
| `deployment/sso/saml20-sp-remote.php` | **Create** | CDCS SP metadata for SimpleSAMLphp IdP |
| `deployment/saml2/.env.sso-dev.example` | **Create** | Pre-filled SAML env for this dev SSO setup |
| `deployment/docker-compose.dev.yml` | **Modify** | Add `simplesamlphp` service; add SSO domain `extra_hosts` to `cdcs` service; add `SSO_DOMAIN` env to `caddy` service |
| `deployment/caddy/Caddyfile.dev` | **Modify** | Add `https://{$SSO_DOMAIN}` reverse-proxy block |
| `deployment/.env` | **Modify** | Add `SSO_DOMAIN=sso.nexuslims-dev.localhost` |
| `deployment/dev-commands.sh` | **Modify** | Add SSO helper aliases |

---

## Task 1: Create SimpleSAMLphp config files

**Files:**
- Create: `deployment/sso/authsources.php`
- Create: `deployment/sso/saml20-sp-remote.php`

- [ ] **Step 1: Create `deployment/sso/authsources.php`**

  Attribute names `uid`, `mail`, `givenName`, `sn` match what pysaml2's `required_attributes` and `SAML_ATTRIBUTE_MAPPING` expect (see Background above).

```php
<?php
/**
 * SimpleSAMLphp auth sources for NexusLIMS dev SSO.
 *
 * Two test users mirror the default CDCS dev accounts created by
 * init_environment.py. SAML_CREATE_UNKNOWN_USER must remain False
 * (the default) so these users must already exist in CDCS.
 *
 * Credentials:
 *   user  / user   -> maps to CDCS 'user' account
 *   admin / admin  -> maps to CDCS 'admin' superuser account
 */
$config = [
    'admin' => [
        'core:AdminPassword',
    ],

    'example-userpass' => [
        'exampleauth:UserPass',

        'user:user' => [
            'uid'       => ['user'],
            'mail'      => ['user@nexuslims-dev.localhost'],
            'givenName' => ['Test'],
            'sn'        => ['User'],
        ],

        'admin:admin' => [
            'uid'       => ['admin'],
            'mail'      => ['admin@nexuslims-dev.localhost'],
            'givenName' => ['Admin'],
            'sn'        => ['User'],
        ],
    ],
];
```

- [ ] **Step 2: Create `deployment/sso/saml20-sp-remote.php`**

  The array key is the SP entity ID (`https://nexuslims-dev.localhost/saml2/metadata/`) which pysaml2 publishes at that URL. ACS uses HTTP-POST binding (matching `SAML_DEFAULT_BINDING = saml2.BINDING_HTTP_POST` in CDCS settings).

```php
<?php
/**
 * CDCS SP metadata for the NexusLIMS dev SimpleSAMLphp IdP.
 *
 * Entity ID = the SP metadata URL published by djangosaml2.
 * ACS = assertion consumer service (where SimpleSAMLphp POSTs the assertion).
 * SLS = single logout service.
 */
$metadata['https://nexuslims-dev.localhost/saml2/metadata/'] = [
    'AssertionConsumerService' => [
        [
            'Binding'  => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
            'Location' => 'https://nexuslims-dev.localhost/saml2/acs/',
            'index'    => 1,
        ],
    ],
    'SingleLogoutService' => [
        [
            'Binding'  => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            'Location' => 'https://nexuslims-dev.localhost/saml2/ls/',
        ],
        [
            'Binding'  => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
            'Location' => 'https://nexuslims-dev.localhost/saml2/ls/post/',
        ],
    ],
];
```

- [ ] **Step 3: Commit**

```bash
git add deployment/sso/authsources.php deployment/sso/saml20-sp-remote.php
git commit -m "feat(sso): add SimpleSAMLphp authsources and CDCS SP metadata for dev IdP"
```

---

## Task 2: Add SimpleSAMLphp service to docker-compose.dev.yml

**Files:**
- Modify: `deployment/docker-compose.dev.yml`

- [ ] **Step 1: Add the `simplesamlphp` service and supporting changes**

  Open `deployment/docker-compose.dev.yml`. Add the `simplesamlphp` service, add `SSO_DOMAIN` to the `caddy` environment, and add `extra_hosts` for the SSO domain to the `cdcs` service so pysaml2 can fetch metadata. The complete updated file should be:

```yaml
# Docker Compose override for local development
# This file mounts local source code for live development with Django runserver
#
# Usage: docker compose -f docker-compose.base.yml -f docker-compose.dev.yml up

services:
  caddy:
    volumes:
      # Dev CA certificates for local HTTPS
      - ./caddy/certs:/etc/caddy/certs:ro
      # File server test data
      - ${NX_DATA_HOST_PATH}:${NX_DATA_PATH}:ro
      - ${NX_INSTRUMENT_DATA_HOST_PATH}:${NX_INSTRUMENT_DATA_PATH}:ro
    environment:
      - SSO_DOMAIN=${SSO_DOMAIN}

  cdcs:
    # Mount local NexusLIMS-CDCS source code for live reload
    volumes:
      - ..:/srv/nexuslims:delegated
      - cdcs_media:/srv/nexuslims/media
      - cdcs_socket:/tmp/nexuslims/
      - cdcs_static:/srv/nexuslims/static.prod
      # Caddy's root CA certificate for SSL verification (mounted in base, just referencing here)
      - ./caddy/certs/ca.crt:/etc/ssl/certs/caddy-root-ca.crt:ro
      # Test data for development initialization
      - ./test-data/example_record.xml:/srv/test-data/example_record.xml:ro
      - ./test-data/example_record_large.xml:/srv/test-data/example_record_large.xml:ro
      - ./test-data/example_record_multisample.xml:/srv/test-data/example_record_multisample.xml:ro

    environment:
      # Use Caddy's root CA certificate for development
      # (allows celery and other requests to verify SSL against Caddy's self-signed cert)
      - REQUESTS_CA_BUNDLE=/etc/ssl/certs/caddy-root-ca.crt
      - CURL_CA_BUNDLE=/etc/ssl/certs/caddy-root-ca.crt

    extra_hosts:
      # Allows pysaml2 to resolve the SSO domain to Caddy when fetching IdP metadata
      - "${SSO_DOMAIN:-sso.nexuslims-dev.localhost}:host-gateway"

    # Override entrypoint and command to use Django runserver for auto-reload
    entrypoint: ["/docker-entrypoint.dev.sh"]

  simplesamlphp:
    image: kenchan0130/simplesamlphp:latest
    container_name: ${COMPOSE_PROJECT_NAME}_cdcs_sso
    environment:
      - SIMPLESAMLPHP_ADMIN_PASSWORD=admin
      - SIMPLESAMLPHP_SECRET_SALT=devonlysaltnotforsecrets123456789
    volumes:
      # Override auth sources with dev test users
      - ./sso/authsources.php:/var/www/simplesamlphp/config/authsources.php:ro
      # Register CDCS as a known SP
      - ./sso/saml20-sp-remote.php:/var/www/simplesamlphp/metadata/saml20-sp-remote.php:ro
```

- [ ] **Step 2: Commit**

```bash
git add deployment/docker-compose.dev.yml
git commit -m "feat(sso): add SimpleSAMLphp service to dev docker-compose"
```

---

## Task 3: Add SSO domain to Caddy and .env

**Files:**
- Modify: `deployment/caddy/Caddyfile.dev`
- Modify: `deployment/.env`

- [ ] **Step 1: Add `SSO_DOMAIN` to `deployment/.env`**

  Add this line near the `FILES_DOMAIN` entry:

```
SSO_DOMAIN=sso.nexuslims-dev.localhost
```

- [ ] **Step 2: Add the SSO reverse-proxy block to `deployment/caddy/Caddyfile.dev`**

  Append this block at the end of the file (after the file-server block):

```
# SimpleSAMLphp dev IdP
https://{$SSO_DOMAIN} {
    # Auto-generate short-lived certificates from custom CA
    tls {
        issuer internal {
            ca local
        }
    }

    # Reverse proxy to SimpleSAMLphp container
    # X-Forwarded-Proto and X-Forwarded-Host let SimpleSAMLphp auto-detect
    # its public URL so it generates correct https:// URLs in SAML messages.
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

- [ ] **Step 3: Commit**

```bash
git add deployment/caddy/Caddyfile.dev deployment/.env
git commit -m "feat(sso): add SSO_DOMAIN to .env and Caddy reverse-proxy block for SimpleSAMLphp"
```

---

## Task 4: Create the pre-filled SAML env example

**Files:**
- Create: `deployment/saml2/.env.sso-dev.example`

- [ ] **Step 1: Create `deployment/saml2/.env.sso-dev.example`**

  This file can be copied directly to `deployment/saml2/.env` to activate SAML SSO against the local SimpleSAMLphp IdP. Key points:
  - `SAML_ATTRIBUTES_MAP_CN_FIELD=givenName` — SimpleSAMLphp sends `givenName`; this must match so djangosaml2 maps it to `first_name` and pysaml2's `required_attributes` check passes.
  - `SAML_WANT_RESPONSE_SIGNED=False` / `SAML_WANT_ASSERTIONS_SIGNED=False` — avoids needing to set up SP signing certificates for dev; SimpleSAMLphp still signs assertions with its own cert (verified automatically via the IdP metadata).
  - `SAML_CREATE_UNKNOWN_USER=False` — forces the user to already exist; the default dev users (`admin`, `user`) created by `init_environment.py` are sufficient.

```bash
cat > deployment/saml2/.env.sso-dev.example << 'EOF'
# =============================================================================
# Dev SAML SSO configuration for local SimpleSAMLphp IdP
# =============================================================================
# Copy this file to deployment/saml2/.env, then restart the dev environment:
#
#   cp deployment/saml2/.env.sso-dev.example deployment/saml2/.env
#   dev-restart-all
#
# Two test accounts are available (credentials = username/password):
#   user  / user   (standard user)
#   admin / admin  (superuser)
#
# These must already exist in CDCS. The default dev init creates them.
# =============================================================================

ENABLE_ALLAUTH=False
ENABLE_ALLAUTH_LOCAL_MFA=False
ENABLE_SAML2_SSO_AUTH=True

# IdP metadata URL (SimpleSAMLphp running via Caddy)
SAML_METADATA_REMOTE=https://sso.nexuslims-dev.localhost/simplesaml/saml2/idp/metadata.php
# SAML_METADATA_REMOTE_CERT is intentionally unset: pysaml2 uses requests which
# respects REQUESTS_CA_BUNDLE (already set to Caddy's CA in the container).

# Attribute map directory (relative to Django BASE_DIR = /srv/nexuslims)
SAML_ATTRIBUTE_MAP_DIR=attr-maps

# Attribute name format sent by SimpleSAMLphp
SAML_ATTRIBUTES_MAP_IDENTIFIER=urn:oasis:names:tc:SAML:2.0:attrname-format:basic

# Attribute field names (must match what SimpleSAMLphp sends in authsources.php)
# NOTE: CN_FIELD must be 'givenName' so it satisfies pysaml2's required_attributes
# check AND so djangosaml2 maps it correctly to Django's first_name field.
SAML_ATTRIBUTES_MAP_UID_FIELD=uid
SAML_ATTRIBUTES_MAP_EMAIL_FIELD=mail
SAML_ATTRIBUTES_MAP_CN_FIELD=givenName
SAML_ATTRIBUTES_MAP_SN_FIELD=sn

# Corresponding OID URNs (used by the attr-maps/attr-map.py for OID→name translation)
SAML_ATTRIBUTES_MAP_UID=urn:oid:0.9.2342.19200300.100.1.1
SAML_ATTRIBUTES_MAP_EMAIL=urn:oid:1.2.840.113549.1.9.1
SAML_ATTRIBUTES_MAP_CN=urn:oid:2.5.4.42
SAML_ATTRIBUTES_MAP_SN=urn:oid:2.5.4.4

# Django user model field for the primary identifier
SAML_DJANGO_USER_MAIN_ATTRIBUTE=username
SAML_USE_NAME_ID_AS_USERNAME=False

# Do not auto-create users on first SAML login (use existing dev accounts)
SAML_CREATE_UNKNOWN_USER=False

# xmlsec1 binary path inside the container
SAML_XMLSEC_BIN_PATH=/usr/bin/xmlsec1

# No signing requirements for dev — keeps setup simple.
# SimpleSAMLphp still signs assertions; pysaml2 verifies via the IdP cert
# embedded in the metadata XML it fetches from SAML_METADATA_REMOTE.
SAML_WANT_RESPONSE_SIGNED=False
SAML_WANT_ASSERTIONS_SIGNED=False
SAML_LOGOUT_REQUESTS_SIGNED=False

# Minimal contact info (required by pysaml2 config builder)
CONTACT_PERSON_1=Dev,Admin,NexusLIMS,admin@nexuslims-dev.localhost,technical
EOF
```

- [ ] **Step 2: Commit**

```bash
git add deployment/saml2/.env.sso-dev.example
git commit -m "feat(sso): add pre-filled SAML env example for SimpleSAMLphp dev IdP"
```

---

## Task 5: Add SSO helper aliases to dev-commands.sh

**Files:**
- Modify: `deployment/dev-commands.sh`

- [ ] **Step 1: Add SSO aliases**

  In `deployment/dev-commands.sh`, add the following alias block and echo lines. Place the alias block after the existing XSLT aliases section, and the echo lines in the final usage printout block.

  Add this alias block after the `dev-uv-add` alias:

```bash
# SSO / SimpleSAMLphp helpers
alias dev-sso-enable='cp "$_DEV_DIR/saml2/.env.sso-dev.example" "$_DEV_DIR/saml2/.env" && echo "SAML SSO enabled. Run dev-restart-all to apply."'
alias dev-sso-disable='printf "ENABLE_ALLAUTH=False\nENABLE_ALLAUTH_LOCAL_MFA=False\nENABLE_SAML2_SSO_AUTH=False\n" > "$_DEV_DIR/saml2/.env" && echo "SAML SSO disabled. Run dev-restart-all to apply."'
alias dev-sso-logs='docker logs -f ${COMPOSE_PROJECT_NAME}_cdcs_sso'
alias dev-sso-shell='docker exec -it ${COMPOSE_PROJECT_NAME}_cdcs_sso bash'
```

  Add this section to the echo block at the bottom:

```bash
echo "  🔐 SSO (SimpleSAMLphp):"
echo "    dev-sso-enable      - Copy sso-dev example to saml2/.env (enables SAML SSO)"
echo "    dev-sso-disable     - Reset saml2/.env to disable SAML SSO"
echo "    dev-sso-logs        - View SimpleSAMLphp container logs"
echo "    dev-sso-shell       - Open shell in SimpleSAMLphp container"
echo "    Admin UI: https://sso.nexuslims-dev.localhost/simplesaml/ (password: admin)"
echo ""
```

- [ ] **Step 2: Commit**

```bash
git add deployment/dev-commands.sh
git commit -m "feat(sso): add dev-sso-enable/disable/logs/shell aliases to dev-commands.sh"
```

---

## Task 6: End-to-end verification

These are manual steps to confirm the SSO flow works. No code changes.

- [ ] **Step 1: Enable SSO and restart**

```bash
cd deployment
source dev-commands.sh
dev-sso-enable
dev-restart-all
```

Expected: all containers start without errors. Check with:
```bash
dev-logs  # watch for Django startup errors related to SAML config
```

- [ ] **Step 2: Verify IdP is reachable**

  In a browser, navigate to `https://sso.nexuslims-dev.localhost/simplesaml/`.

  Expected: SimpleSAMLphp admin page loads (certificate warning may appear if the Caddy CA is not trusted in your browser; proceed past it).

- [ ] **Step 3: Verify IdP metadata is reachable from inside the CDCS container**

```bash
docker exec nexuslims_dev_cdcs curl -s \
  https://sso.nexuslims-dev.localhost/simplesaml/saml2/idp/metadata.php \
  | head -5
```

Expected: XML starting with `<md:EntityDescriptor ...`.

  If this fails with a certificate error, check that the Caddy CA cert is properly mounted and `REQUESTS_CA_BUNDLE` is set:
```bash
docker exec nexuslims_dev_cdcs env | grep REQUESTS_CA_BUNDLE
```

- [ ] **Step 4: Verify SP metadata is reachable**

```bash
curl -sk https://nexuslims-dev.localhost/saml2/metadata/ | head -5
```

Expected: XML starting with `<ns0:EntityDescriptor ...` or similar, containing `entityID="https://nexuslims-dev.localhost/saml2/metadata/"`.

- [ ] **Step 5: Test the SSO login flow**

  1. Open an incognito/private browser window.
  2. Navigate to `https://nexuslims-dev.localhost`.
  3. Click **Login** → you should see a "Sign in with SSO" option alongside the local login form.
  4. Click the SSO option.
  5. Browser redirects to `https://sso.nexuslims-dev.localhost/simplesaml/...`.
  6. Enter credentials `user` / `user`.
  7. SimpleSAMLphp POSTs the SAML assertion back to `https://nexuslims-dev.localhost/saml2/acs/`.
  8. You are logged in as the `user` account in CDCS.

- [ ] **Step 6: Test admin SSO login**

  Repeat Step 5 using credentials `admin` / `admin`. Verify you are logged in as the superuser.

- [ ] **Step 7: Test SSO logout**

  While logged in via SSO, click **Logout** in CDCS. Verify you are redirected to the login page and the session is ended.

- [ ] **Step 8: Disable SSO and verify local login still works**

```bash
dev-sso-disable
dev-restart-all
```

  Navigate to `https://nexuslims-dev.localhost` and verify local username/password login works normally with no SAML option shown.

---

## Troubleshooting Reference

**"No SSO option on login page"**
- Check `docker exec nexuslims_dev_cdcs env | grep ENABLE_SAML2` → should be `True`.
- Check CDCS logs for SAML config import errors: `dev-logs-app | grep -i saml`.

**"Error fetching IdP metadata"**
- Verify the SSO container is running: `docker ps | grep sso`.
- Test connectivity from inside CDCS: `docker exec nexuslims_dev_cdcs curl -v https://sso.nexuslims-dev.localhost/simplesaml/saml2/idp/metadata.php`.
- If SSL fails: check `REQUESTS_CA_BUNDLE` and that the Caddy CA cert is correctly mounted.

**"SAML assertion error / attribute missing"**
- Check CDCS logs during the ACS callback: `dev-logs-app`.
- Verify `required_attributes` in pysaml2: these are `["givenName", "sn", "mail"]` (hard-coded in `core_main_app`). The SimpleSAMLphp `authsources.php` sends exactly these names.
- If there is a `givenName` mismatch, check `SAML_ATTRIBUTES_MAP_CN_FIELD=givenName` in `saml2/.env`.

**"User not found after SSO login"**
- `SAML_CREATE_UNKNOWN_USER=False` means the user must pre-exist. The `uid` attribute must match a CDCS username.
- Confirm the `user` and `admin` accounts exist: `dev-manage shell` → `from django.contrib.auth.models import User; list(User.objects.values_list('username', flat=True))`.
