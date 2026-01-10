# Docker Development Environment - Setup Complete ✅

## Current State

The Docker development environment for NexusLIMS-CDCS upgrade to v3.18.0 is ready.

### What's Been Created

**Branch**: `upgrade/v3.18.0-working` (based on MDCS v3.18.0)

**Docker Environment** (`.dev-deployment/`):
- ✅ Dockerfile for NexusLIMS-CDCS
- ✅ Docker Compose files (base + dev override)
- ✅ MongoDB, PostgreSQL, Redis configurations  
- ✅ Caddy reverse proxy with HTTPS
- ✅ Helper command aliases (`dev-commands.sh`)
- ✅ Development settings file
- ✅ Non-standard ports (no conflicts)

### Next Steps

#### 1. Build and Test Base v3.18.0

Before migrating NexusLIMS customizations, test the clean MDCS v3.18.0 base:

```bash
cd .dev-deployment

# Build the image (first time)
docker compose build

# Start all services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Watch logs
docker compose logs -f cdcs

# Check if it starts successfully
```

**Expected outcome**: The base MDCS v3.18.0 should start, but won't have NexusLIMS customizations yet.

#### 2. Begin Migration (Phase 3+)

Once the base works, we'll systematically migrate NexusLIMS customizations:

- **Phase 3**: Copy self-contained files (XSLT, JavaScript, CSS, templates)
- **Phase 4**: XSLT architecture decision (eliminate parameter system - recommended)
- **Phase 5**: Merge configuration files (settings.py, urls.py)
- **Phase 6**: Update dependencies
- **Phase 7**: Migrate modified templates and static files
- **Phase 8**: Run database migrations
- **Phase 9**: Comprehensive testing

### Access URLs (After Build & Start)

- **Application**: https://nexuslims-dev.localhost:8443
- **PostgreSQL**: localhost:5532
- **MongoDB**: localhost:27117
- **Redis**: localhost:6479

### Quick Commands

```bash
# Load helper aliases
source dev-commands.sh

# Lifecycle
dev-up              # Start all services
dev-down            # Stop all services
dev-restart         # Restart app

# Logs
dev-logs            # All logs
dev-logs-app        # App logs only

# Shell access
dev-shell           # Bash in container
dev-djshell         # Django shell

# Database
dev-migrate         # Run migrations
dev-superuser       # Create admin user
```

### Git State

**Current branch**: `upgrade/v3.18.0-working`  
**Branches created**:
- `upgrade/v3.18.0-preparation` (from NexusLIMS_master)
- `upgrade/v3.18.0-working` (from tag 3.18.0) ← you are here

**Backup tag**: `nexuslims-cdcs-pre-upgrade-20251230`

**Reference files**: Exported to `reference/` directory
- `reference/v2.21.0/` - Original MDCS base
- `reference/main/` - Current NexusLIMS customizations
- `reference/v3.18.0/` - New MDCS target

## Troubleshooting

### If build fails
Check that you're on the `upgrade/v3.18.0-working` branch with clean v3.18.0 code.

### If containers fail to start
Check the logs with `dev-logs` or `docker compose logs -f`.

### Port conflicts
Edit `.dev-deployment/.env` to change port mappings if needed.

## Documentation

- **Full setup guide**: `.dev-deployment/README.md`
- **Upgrade plan**: `.claude/planning/UPGRADE_PLAN_v3.18.0.md`
- **Changes reference**: `.claude/planning/CHANGES_FROM_MDCS_2.21.0.md`
- **Conflicts guide**: `.claude/planning/POTENTIAL_UPGRADE_CONFLICTS.md`
