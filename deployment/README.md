# NexusLIMS-CDCS Deployment

This directory contains unified deployment configuration for both development and production environments of NexusLIMS-CDCS.

## Overview

The deployment uses a three-layer Docker Compose approach:
- **`docker-compose.base.yml`** - Shared configuration for all environments
- **`docker-compose.dev.yml`** - Development-specific overrides
- **`docker-compose.prod.yml`** - Production-specific overrides

This architecture maximizes code reuse while allowing environment-specific customization.

## Quick Start - Development

1. **Navigate to deployment directory:**
   ```bash
   cd deployment
   ```

2. **Set up environment:**
   ```bash
   cp .env.dev .env
   ```

3. **Load development helper commands:**
   ```bash
   source dev-commands.sh
   ```
   This loads convenient aliases for common development tasks.

4. **Start the development environment:**
   ```bash
   dev-up
   # Automatically extracts test data, builds CDCS image, pulls supporting images, and starts all services
   ```

5. **Trust the development CA certificate** (one-time setup):

   The development environment uses a local Certificate Authority (CA) to generate secure HTTPS certificates. To avoid browser warnings, you need to trust the CA certificate once.

   **On macOS:**
   ```bash
   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain caddy/certs/ca.crt
   ```

   **On Linux (Ubuntu/Debian):**
   ```bash
   sudo cp caddy/certs/ca.crt /usr/local/share/ca-certificates/nexuslims-dev-ca.crt
   sudo update-ca-certificates
   ```

   **On Linux (Fedora/RHEL):**
   ```bash
   sudo cp caddy/certs/ca.crt /etc/pki/ca-trust/source/anchors/nexuslims-dev-ca.crt
   sudo update-ca-trust
   ```

   **On Windows:**
   1. Open `certmgr.msc`
   2. Navigate to "Trusted Root Certification Authorities" → "Certificates"
   3. Right-click → "All Tasks" → "Import"
   4. Select `caddy/certs/ca.crt`

   **Alternative - Browser-specific import:**

   If you prefer not to add the certificate system-wide, you can import it directly into your browser:
   - **Chrome/Edge**: Settings → Privacy and security → Security → Manage certificates → Authorities → Import
   - **Firefox**: Settings → Privacy & Security → Certificates → View Certificates → Authorities → Import
   - **Safari**: Safari → Settings → Privacy → Manage Website Data (uses system keychain on macOS)

6. **Access the application:**
   - Main app: https://nexuslims-dev.localhost
   - File server: https://files.nexuslims-dev.localhost/data/ and https://files.nexuslims-dev.localhost/instrument-data/
   - Default super user credentials: admin/admin
   - Default regular user credentials: user/user
   
7. **Development features:**

   The development environment includes several features to streamline development:

   - **Hot-reload enabled** - Application code is mounted into the container, so changes to Python files automatically reload the application
   - **Local HTTPS with self-signed certificates** - Uses Caddy with a local CA for secure HTTPS connections (requires one-time certificate trust setup)
   - **File server for test data** - Serves instrument data and preview/metadata files via `files.nexuslims-dev.localhost` to simulate production file access
   - **Pre-populated test data** - Automatically extracts and configures sample instrument data and metadata for testing
   - **Development helper commands** - Convenient aliases loaded via `source dev-commands.sh` for common tasks (see inline documentation in the script)
   - **Direct database access** - PostgreSQL and Redis exposed on host ports for debugging and inspection

## Quick Start - Production

See [`PRODUCTION.md`](PRODUCTION.md) for comprehensive production deployment guide.

**Quick setup:**
```bash
cd deployment
cp .env.prod.example .env
# Edit .env with your production values (domains, passwords, etc.)
source admin-commands.sh
dc-prod up -d
```

## Directory Structure

```
deployment/
├── docker-compose.base.yml    # Shared configuration
├── docker-compose.dev.yml     # Development overrides
├── docker-compose.prod.yml    # Production overrides
├── Dockerfile                 # Application image
├── docker-entrypoint.sh       # Container startup script
├── .gitignore                 # Git ignore rules
│
├── .env                       # Active environment config (gitignored, copy from .env.dev or .env.prod.example)
├── .env.dev                   # Development defaults (tracked)
├── .env.prod.example          # Production template (tracked)
│
├── caddy/
│   ├── Dockerfile             # Custom Caddy with plugins
│   ├── Caddyfile.dev          # Development file server and reverse proxy (local CA with self-signed certs)
│   ├── Caddyfile.prod         # Production file server and reverse proxy (using ACME/Let's Encrypt)
│   └── certs/                 # Dev CA certificates
│
├── scripts/
│   ├── init_environment.py    # Complete environment setup (superuser + schema + XSLT)
│   ├── update-xslt.sh         # Update XSLT stylesheets in database
│   ├── update-schema.sh       # Update nexus-experiment.xsd from canonical source
│   ├── setup-test-data.sh     # Extract test data (dev only)
│   ├── backup_cdcs.py         # Backup system data
│   ├── restore_cdcs.py        # Restore system data from backup
│   └── show_stats.py          # Display system statistics
│
├── schemas/
│   └── nexus-experiment.xsd   # NexusLIMS schema (synced from NexusLIMS repo)
│
├── test-data/                      # Development test data (gitignored when extracted)
│   └── nexuslims-test-data.tar.gz  # Example test data that will be extracted as needed
│
├── extra/                     # Optional extra configuration
│   └── .env                   # Extra environment variables
├── handle/                    # Handle system configuration
│   └── .env                   # Handle-related environment variable 
├── saml2/                     # SAML2 authentication configuration
│   └── .env                   # SAML2-related environment variables
│
├── dev-commands.sh            # Development helper aliases
├── admin-commands.sh          # Administrative commands aliases
├── README.md                  # This file
└── PRODUCTION.md              # Comprehensive production deployment guide
```

**Repository root also contains:**
```
xslt/                          # XSLT stylesheets
├── detail_stylesheet.xsl
└── list_stylesheet.xsl

config/                        # Application configuration
└── settings/
    ├── dev_settings.py        # Settings for local development
    └── prod_settings.py       # Settings for production deployment
```

## Environment Configuration

All environment-specific settings are controlled via `.env` files:

### Development (`.env.dev`)
- Use by copying to `.env`: `$ cp .env.dev .env`
- Safe defaults for local development; no changes needed to get a working deployment
- Uses `.localhost` domains (no DNS needed)
- Test data, metadata, and records included and configured for access by caddy fileserver
- Development secret keys
- Tracked in git

### Production (`.env.prod.example`)
- Template for production setup
- Real domain names
- Strong passwords must be set
- Production file paths
- **Copy to `.env` and customize** (never commit `.env`!)

## Services

| Service | Purpose | Port (internal) | Port (host) |
|---------|---------|-----------------|-------------|
| **caddy** | Reverse proxy with HTTPS | 80, 443 | 80, 443 |
| **postgres** | PostgreSQL database | 5432 | 5532 |
| **redis** | Cache and session store | 6379 | 6479 |
| **cdcs** | Django application | 8000 | - |

## Development Features

### Live Code Reload
The development setup mounts your local source code, enabling:
- ✅ Live code reload - Django runserver automatically detects changes
- ✅ No rebuild needed - Edit code locally, see changes immediately
- ✅ Full debugging - Django debug mode enabled

### Test Data
Development includes sample microscopy data (~1.4MB compressed, ~149MB extracted):
- Preview images and metadata: `https://files.nexuslims-dev.localhost/data`
- Raw instrument data: `https://files.nexuslims-dev.localhost/instrument-data`
- Example XML records

Test data is automatically extracted by `dev-up` and is gitignored.

### Development Commands

Load with: `source dev-commands.sh`

**Lifecycle:**
- `dev-up` - Start all services
- `dev-down` - Stop all services
- `dev-restart` - Restart CDCS app
- `dev-clean` - Stop and remove all data (clean slate)

**Viewing:**
- `dev-logs` - View all logs
- `dev-logs-app` - CDCS app logs only
- `dev-logs-caddy` - Caddy proxy logs

**Shell Access:**
- `dev-shell` - Bash in CDCS container
- `dev-djshell` - Django Python shell
- `dev-dbshell` - PostgreSQL shell

**Database:**
- `dev-migrate` - Run migrations
- `dev-makemigrations` - Create migrations

**NexusLIMS:**
- `dev-update-xslt` - Update XSLT stylesheets in database

## Administrative Commands

Load with: `source admin-commands.sh`

Meant to be used to administer production deployments.

**Backup & Restore:**
- `admin-backup` - Backup all data (templates, records, blobs, users, XSLT)
- `admin-restore` - Restore from backup
- `admin-db-dump` - PostgreSQL dump
- `admin-db-restore` - Restore PostgreSQL (admin-backup/admin-restore is preferred)

**User Management:**
- `admin-list-users` - List all users
- `admin-export-users` - Export to JSON
- `admin-import-users` - Import from JSON

**Maintenance:**
- `admin-clean-sessions` - Remove expired sessions
- `admin-clean-cache` - Clear Redis cache
- `admin-stats` - System statistics

## XSLT Stylesheet Management

**CRITICAL**: XSLT stylesheets are stored in the Django database, not just as files.

### Files Location
- `xslt/detail_stylesheet.xsl` (at repo root)
- `xslt/list_stylesheet.xsl` (at repo root)

### Update Process

1. Edit the XSL file in `xslt/`
2. Update the database:
   ```bash
   cd deployment
   source dev-commands.sh
   dev-update-xslt
   ```

The update script automatically patches URLs based on environment variables:
- `XSLT_DATASET_BASE_URL` - Base URL for instrument data
- `XSLT_PREVIEW_BASE_URL` - Base URL for preview images

See [`../CLAUDE.md`](../CLAUDE.md) for more details.

## Dependency Management

This project uses **[UV](https://github.com/astral-sh/uv)** for fast, reliable Python dependency management.

### Key Files

- **`pyproject.toml`** - Project configuration and dependencies (replaces requirements.txt)
- **`uv.lock`** - Lockfile ensuring reproducible builds across all environments
- **`.python-version`** - Specifies required Python version (3.13)

### Dependency Groups

Dependencies are organized into optional groups in `pyproject.toml`:

- **Main dependencies**: `celery`, `Django`, `django-redis` (core application)
- **`[core]` group**: 21 CDCS/MDCS packages pinned to `2.20.*`
- **`[server]` group**: Production servers (`psycopg2-binary`, `uwsgi`, `gunicorn`)

### Docker Build Process

The Dockerfile uses native UV commands for fast, reproducible builds:

```dockerfile
# Copy dependency files (separate layer for caching)
COPY pyproject.toml uv.lock ./

# Install from lockfile (no dependency resolution needed)
RUN uv sync --frozen --no-dev --extra core --extra server
```

**Benefits:**
- **Fast**: UV is 10-100x faster than pip
- **Reproducible**: Lockfile ensures identical dependencies everywhere
- **Cached**: Docker layer caching speeds up rebuilds

### Adding New Dependencies

1. **Add to pyproject.toml**:
   ```bash
   # For a main dependency
   uv add package-name

   # For a specific group
   uv add --optional server new-server-package
   ```

2. **Update lockfile**:
   ```bash
   uv lock
   ```

3. **Rebuild Docker image**:
   ```bash
   dev-build-clean
   ```

### Updating Dependencies

**Update all packages (respecting version constraints):**
```bash
uv lock --upgrade
```

**Update specific package:**
```bash
uv lock --upgrade-package django
```

**IMPORTANT**: Always commit `uv.lock` changes with your dependency updates.

### Upgrading CDCS Core Packages

CDCS core packages are pinned to `2.20.*` for stability. To upgrade to a new CDCS version:

1. **Edit `pyproject.toml`**:
   ```toml
   [project.optional-dependencies]
   core = [
       "core_main_app[auth]==2.21.*",  # Change version
       "core_composer_app==2.21.*",     # Change version
       # ... update all core packages
   ]
   ```

2. **Update lockfile**:
   ```bash
   uv lock --upgrade
   ```

3. **Test thoroughly** before deploying to production

### Local Development (Optional)

UV supports local development outside Docker:

```bash
# Create virtual environment and install dependencies
# Note: --no-install-project skips building the project itself (it's a Django app, not a package)
uv sync --no-install-project --extra core --extra server

# Activate environment
source .venv/bin/activate

# Run Django commands
python manage.py runserver
```

**Alternative:** Use the convenience alias (from deployment directory):
```bash
source dev-commands.sh
dev-uv-sync  # Creates .venv and installs all dependencies
```

However, **Docker is the recommended development workflow** as it matches production more closely.

## Architecture

### Development
```
Browser → Caddy (HTTPS :443) → Django runserver (:8000) → Application
         (Local CA)                  ↓
                          ┌──────────┼──────────┐
                          ↓          ↓          ↓
                     PostgreSQL   Redis    File Server
                      (:5432)    (:6379)   (via Caddy)

```

### Production
```
Browser → Caddy (HTTPS :443) → Gunicorn (:8000) → Application
      (Let's Encrypt)              ↓
                        ┌──────────┼──────────┐
                        ↓          ↓          ↓
                   PostgreSQL   Redis    File Server
                    (:5432)    (:6379)   (via Caddy)

Production file paths mounted from host:
  NX_DATA_HOST_PATH → /srv/nx-data
  NX_INSTRUMENT_DATA_HOST_PATH → /srv/nx-instrument-data
```

## Troubleshooting

### Certificate Warnings (Development)
Trust the CA certificate once (see Quick Start step 5). After trusting `caddy/certs/ca.crt`, all HTTPS connections will work with no warnings.

### Database Connection Errors
Wait for services to fully start. The Django container waits for PostgreSQL to be ready.

### Port Conflicts
Edit port mappings in `.env`:
```bash
POSTGRES_HOST_PORT=5532  # Change if needed
REDIS_HOST_PORT=6479     # Change if needed
```

### Permission Errors
Ensure scripts are executable:
```bash
chmod +x dev-commands.sh admin-commands.sh
chmod +x scripts/*.sh scripts/*.py
```

### Test Data Not Loading
Run extraction manually:
```bash
bash scripts/setup-test-data.sh
```

### XSLT Changes Not Appearing
XSLT files must be loaded into the database:
```bash
dev-update-xslt
```
Then refresh your browser.

## Production Deployment

For production deployment:
1. See [`PRODUCTION.md`](PRODUCTION.md) for complete guide
2. Key differences from dev:
   - Uses real domains with Let's Encrypt certificates
   - No test data
   - Gunicorn instead of runserver
   - No source code mounting
   - Production-ready settings and security
   - Health checks enabled

## Backup and Recovery

### Quick Backup
```bash
source admin-commands.sh
admin-backup
# Creates: /srv/nexuslims/backups/backup_YYYYMMDD_HHMMSS/
#   which is mapped into ${NX_CDCS_BACKUPS_HOST_PATH}
```

### Database Dump
```bash
admin-db-dump
# Creates: backup_YYYYMMDD_HHMMSS.sql
```

### Restore
```bash
# From CDCS backup
admin-restore ${NX_CDCS_BACKUPS_HOST_PATH}/backup_YYYYMMDD_HHMMSS

# From SQL dump
admin-db-restore ${NX_CDCS_BACKUPS_HOST_PATH}/backup_20260109_120000.sql
```

See backup script documentation for details on backup structure and contents.

## Next Steps

After deployment:
1. ✅ Access application at configured domain
2. ✅ Schema automatically initialized on first startup (creates admin/admin user)
3. ✅ Upload data records via web interface
4. ✅ Verify XSLT rendering
6. ✅ Test file downloads
7. ✅ Configure backups (production)

## Additional Resources

- **Production Guide**: [`PRODUCTION.md`](PRODUCTION.md)
- **NexusLIMS Customizations**: [`../nexuslims_overrides/CUSTOMIZATION.md`](../nexuslims_overrides/CUSTOMIZATION.md)

## Support

For issues or questions:
- Check troubleshooting section above
- Review logs: `dev-logs` or `docker compose logs`
- Check container status: `docker compose ps`
- View system stats: `admin-stats`

## Professional Assistance

💼 **Need help with NexusLIMS?** Datasophos offers:

- 🚀 **Deployment & Integration** - Expert configuration for your lab environment
- 🔧 **Custom Development** - Custom extractors, harvesters, and workflow extensions
- 🎓 **Training & Support** - Team onboarding and ongoing technical support

**Contact**: [josh@datasophos.co](mailto:josh@datasophos.co) | [datasophos.co](https://datasophos.co)
