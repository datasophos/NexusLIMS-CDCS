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
   # Or use the existing .env if already configured
   ```

3. **Load development helper commands:**
   ```bash
   source dev-commands.sh
   ```
   This loads convenient aliases for common development tasks.

4. **Start the development environment:**
   ```bash
   dev-up
   # Automatically extracts test data and starts all services
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

6. **Access the application:**
   - Main app: https://nexuslims-dev.localhost
   - File server: https://files.nexuslims-dev.localhost
   - Default super user credentials: admin/admin
   - Default regular user credentials: user/user

## Quick Start - Production

See [`PRODUCTION.md`](PRODUCTION.md) for comprehensive production deployment guide.

**Quick setup:**
```bash
cd deployment
cp .env.prod.example .env
# Edit .env with your production values (domains, passwords, etc.)
docker compose -f docker-compose.base.yml -f docker-compose.prod.yml up -d
```

## Directory Structure

```
deployment/
├── docker-compose.base.yml    # Shared configuration
├── docker-compose.dev.yml     # Development overrides
├── docker-compose.prod.yml    # Production overrides
├── Dockerfile                 # Application image
├── docker-entrypoint.sh       # Container startup script
│
├── .env                       # Active environment config (gitignored)
├── .env.dev                   # Development defaults (tracked)
├── .env.example               # All variables documented (tracked)
├── .env.prod.example          # Production template (tracked)
│
├── caddy/
│   ├── Dockerfile             # Custom Caddy with plugins
│   ├── Caddyfile.dev          # Development (local CA)
│   ├── Caddyfile.prod         # Production (ACME/Let's Encrypt)
│   └── certs/                 # Dev CA certificates (gitignored)
│
├── scripts/
│   ├── init_environment.py    # Environment initialization
│   ├── update-xslt.sh         # Update XSLT in database
│   ├── setup-test-data.sh     # Extract test data (dev)
│   ├── backup_cdcs.py         # Backup system data
│   └── show_stats.py          # System statistics
│
├── test-data/                 # Development test data
│   ├── nexuslims-test-data.tar.gz
│   ├── nexus-experiment.xsd
│   ├── example_record.xml
│   └── nx-data/               # Extracted (gitignored)
│
├── dev-commands.sh            # Development helper aliases
├── admin-commands.sh          # Administrative commands
└── README.md                  # This file
```

**Repository root also contains:**
```
xslt/                          # XSLT stylesheets
├── detail_stylesheet.xsl
└── list_stylesheet.xsl

config/                        # Application configuration
└── settings/
    ├── dev_settings.py
    └── prod_settings.py
```

## Environment Configuration

All environment-specific settings are controlled via `.env` files:

### Development (`.env.dev`)
- Safe defaults for local development
- Uses `.localhost` domains (no DNS needed)
- Test data paths
- Development secret keys
- Tracked in git

### Production (`.env.prod.example`)
- Template for production setup
- Real domain names
- Strong passwords (must be set)
- Production file paths
- **Copy to `.env` and customize** (never commit `.env`!)

### Key Environment Variables

| Variable | Purpose | Dev Default | Prod Example |
|----------|---------|-------------|--------------|
| `COMPOSE_PROJECT_NAME` | Container name prefix | `nexuslims_dev` | `nexuslims_prod` |
| `DOMAIN` | Main application domain | `nexuslims-dev.localhost` | `nexuslims.example.com` |
| `FILES_DOMAIN` | File server domain | `files.nexuslims-dev.localhost` | `files.nexuslims.example.com` |
| `DJANGO_SETTINGS_MODULE` | Django settings | `config.settings.dev_settings` | `config.settings.prod_settings` |
| `CADDYFILE` | Which Caddyfile to use | `Caddyfile.dev` | `Caddyfile.prod` |
| `NX_DATA_HOST_PATH` | File server data path | `./test-data/nx-data` | `/mnt/nexuslims/data` |
| `XSLT_DATASET_BASE_URL` | XSLT URL for datasets | `https://files.nexuslims-dev.localhost/instrument-data` | `https://files.nexuslims.example.com/instrument-data` |

See `.env.example` for complete documentation of all variables.

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
- `dev-init` - Complete setup (users + schema)
- `dev-init-schema` - Schema only
- `dev-update-xslt` - Update XSLT stylesheets in database

## Administrative Commands

Load with: `source admin-commands.sh`

Works for both dev and production (reads `COMPOSE_PROJECT_NAME` from `.env`).

**Backup & Restore:**
- `admin-backup` - Backup all data (templates, records, blobs, users, XSLT)
- `admin-restore` - Restore from backup
- `admin-db-dump` - PostgreSQL dump
- `admin-db-restore` - Restore PostgreSQL

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

## Architecture

### Development
```
Browser → Caddy (HTTPS :443) → Django runserver (:8000) → Application
         (Local CA)                  ↓
                          ┌──────────┼──────────┐
                          ↓          ↓          ↓
                     PostgreSQL   Redis    File Server
                      (:5432)    (:6379)   (via Caddy)

Host Access:
  PostgreSQL: localhost:5532
  Redis:      localhost:6479
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
# Creates: /srv/curator/backups/backup_YYYYMMDD_HHMMSS/
```

### Database Dump
```bash
admin-db-dump
# Creates: backup_YYYYMMDD_HHMMSS.sql
```

### Restore
```bash
# From CDCS backup
admin-restore

# From SQL dump
cat backup_20260109_120000.sql | admin-db-restore
```

See backup script documentation for details on backup structure and contents.

## Next Steps

After deployment:
1. ✅ Access application at configured domain
2. ✅ Create superuser (dev: already exists as admin/admin)
3. ✅ Initialize schema with `dev-init` or `dev-init-schema`
4. ✅ Upload data records via web interface
5. ✅ Verify XSLT rendering
6. ✅ Test file downloads
7. ✅ Configure backups (production)

## Additional Resources

- **XSLT Documentation**: [`../CLAUDE.md`](../CLAUDE.md)
- **Production Guide**: [`PRODUCTION.md`](PRODUCTION.md)
- **NexusLIMS Customizations**: [`../nexuslims_overrides/README.md`](../nexuslims_overrides/README.md)
- **MDCS Documentation**: https://github.com/usnistgov/MDCS

## Support

For issues or questions:
- Check troubleshooting section above
- Review logs: `dev-logs` or `docker compose logs`
- Check container status: `docker compose ps`
- View system stats: `admin-stats`
