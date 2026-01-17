# Claude Code Context

Important information for working with this codebase.

## XSLT Stylesheet Updates

**CRITICAL**: XSLT stylesheets are stored in the Django database, not just as files on disk.

### Files Location
- Detail stylesheet: `xslt/detail_stylesheet.xsl` (at repo root)
- List stylesheet: `xslt/list_stylesheet.xsl` (at repo root)

### Update Process

1. **Edit the XSL file** in `xslt/`

2. **Update the database** (REQUIRED - changes won't appear otherwise):

```bash
# From the deployment directory:
cd deployment
source dev-commands.sh
dev-update-xslt        # Updates both detail and list stylesheets
# OR
dev-update-xslt-detail # Updates only detail_stylesheet.xsl
dev-update-xslt-list   # Updates only list_stylesheet.xsl
```

The update script (`deployment/scripts/update-xslt.sh`) automatically:
- Loads the XSL file from the mounted `xslt/` directory
- Patches the `datasetBaseUrl` and `previewBaseUrl` variables using environment variables
- Updates the stylesheet in the Django database
- Verifies the changes were applied

### Environment Configuration

URLs in XSLT are patched from environment variables:
- `XSLT_DATASET_BASE_URL` - Base URL for instrument data files
- `XSLT_PREVIEW_BASE_URL` - Base URL for preview images/metadata

These are configured in your `.env` file (defaults for development):
- `XSLT_DATASET_BASE_URL=https://files.nexuslims-dev.localhost/instrument-data`
- `XSLT_PREVIEW_BASE_URL=https://files.nexuslims-dev.localhost/data`

### Notes
- Just editing the file is NOT enough - you must update the database
- The XSLT transforms XML records to HTML for display in the browser
- The init script loads these on initial setup but doesn't auto-reload on changes
- Template files use placeholders: `https://CHANGE.THIS.VALUE`
- Update script automatically patches URLs based on your `.env` configuration
- For production, update the environment variables to match your production domains

## NexusLIMS Schema (nexus-experiment.xsd)

The NexusLIMS XML schema file defines the structure for experiment records in CDCS.

### Schema Location and Management

**File Location**: `deployment/schemas/nexus-experiment.xsd`

**Canonical Source**: https://github.com/datasophos/NexusLIMS/blob/main/nexusLIMS/schemas/nexus-experiment.xsd

The schema file is tracked in this repository for self-contained deployments, but the canonical version lives in the main NexusLIMS repository. When the upstream schema is updated, you need to sync it here.

### Updating the Schema

**Automatic Update**:
```bash
cd deployment
bash scripts/update-schema.sh
```

This script:
- Downloads the latest schema from the NexusLIMS repository
- Saves it to `deployment/schemas/nexus-experiment.xsd`
- Verifies the download was successful

**Manual Update**:
```bash
curl -L -o deployment/schemas/nexus-experiment.xsd \
  https://raw.githubusercontent.com/datasophos/NexusLIMS/main/nexusLIMS/schemas/nexus-experiment.xsd
```

### Applying Schema Updates

After updating the schema file, you must update it in the database:

**Development Environment**:
```bash
cd deployment
dev-down && dev-up  # Restart to apply changes
```

**Production Environment**:
```bash
docker exec <container-name> python /srv/scripts/init_environment.py
```

### How It Works

- The schema file is mounted into containers at `/srv/nexuslims/schemas/nexus-experiment.xsd`
- During initialization, `init_environment.py` reads this file and uploads it to the CDCS database
- The database stores the schema for validating and rendering XML records
- Just updating the file on disk doesn't change the database - you must re-run initialization
- `init_environment.py` is idempotent and safely skips items that already exist

## UV Dependency Management

This project uses [UV](https://github.com/astral-sh/uv) for Python dependency management. UV provides fast, reliable dependency resolution with reproducible builds via lockfiles.

### Key Principles

**CRITICAL RULES:**
1. **ALWAYS commit `uv.lock`** - The lockfile ensures reproducible builds across dev, staging, and production
2. **NEVER edit `uv.lock` manually** - It's generated from `pyproject.toml` via `uv lock`
3. **Update `pyproject.toml` first, then regenerate lockfile** - This is the proper workflow
4. **Rebuild Docker after dependency changes** - Use `dev-build-clean` to apply changes

### File Structure

- **`pyproject.toml`** - Single source of truth for all dependencies
  - Main dependencies: Core application packages (celery, Django, django-redis)
  - `[project.optional-dependencies.core]`: CDCS/MDCS packages pinned to `2.18.*`
  - `[project.optional-dependencies.server]`: Production servers (psycopg2-binary, uwsgi, gunicorn)
- **`uv.lock`** - Lockfile with exact versions (MUST be committed)
- **`.python-version`** - Required Python version (3.13)

### Common Workflows

#### Adding a New Dependency

**For main application dependencies:**
```bash
cd /path/to/NexusLIMS-CDCS  # Repository root
uv add package-name
# This automatically updates pyproject.toml and uv.lock
```

**For optional group dependencies (manual edit required):**
```bash
# 1. Edit pyproject.toml manually to add to the appropriate group
# 2. Regenerate lockfile
uv lock
```

**Apply changes to Docker:**
```bash
cd deployment
source dev-commands.sh
dev-build-clean  # Clean rebuild with new dependencies
dev-up           # Start services
```

**For local development (outside Docker):**
```bash
# Install/sync dependencies locally
# IMPORTANT: Use --no-install-project flag (this is a Django app, not a package)
uv sync --no-install-project --extra core --extra server

# Or use the convenience alias from deployment directory
cd deployment
source dev-commands.sh
dev-uv-sync
```

#### Updating Dependencies

**Update all packages (respecting version constraints):**
```bash
uv lock --upgrade
```

**Update a specific package:**
```bash
uv lock --upgrade-package package-name
```

**IMPORTANT**: After updating, commit both `pyproject.toml` and `uv.lock`.

#### Upgrading CDCS Core Packages

CDCS core packages are strictly pinned to `2.18.*` for stability. To upgrade to a new CDCS version:

1. **Edit `pyproject.toml`** - Update all `core_*_app` packages to new version:
   ```toml
   [project.optional-dependencies]
   core = [
       "core_main_app[auth]==2.19.*",  # Changed from 2.18.*
       "core_composer_app==2.19.*",     # Changed from 2.18.*
       # ... update all 21 core packages
   ]
   ```

2. **Regenerate lockfile with upgraded packages:**
   ```bash
   uv lock --upgrade
   ```

3. **Review changes:**
   ```bash
   git diff uv.lock  # Review what changed
   ```

4. **Test thoroughly in development:**
   ```bash
   cd deployment
   dev-build-clean
   dev-up
   # Run tests, migrations, verify functionality
   ```

5. **Commit changes:**
   ```bash
   git add pyproject.toml uv.lock
   git commit -m "chore: upgrade CDCS core packages to 2.19.*"
   ```

### Troubleshooting

**Problem: "Package not found" during Docker build**
- Ensure `uv.lock` is committed and up to date
- Run `uv lock` to regenerate lockfile
- Check for typos in `pyproject.toml`

**Problem: Version conflicts**
- Review CDCS package version pins in `pyproject.toml`
- Use `uv lock --upgrade-package package-name` to upgrade specific packages
- Check upstream CDCS release notes for compatibility

**Problem: Docker build fails after dependency change**
- Clear Docker cache: `dev-build-clean`
- Verify lockfile is committed: `git status`
- Check Dockerfile syntax if you modified it

### Docker Integration

The Dockerfile uses native UV commands for optimal performance:

```dockerfile
# Copy dependency files (separate layer for caching)
COPY pyproject.toml uv.lock ./

# Install from lockfile (no dependency resolution needed - fast!)
RUN uv sync --frozen --no-dev --extra core --extra server
```

**Flags explained:**
- `--frozen`: Use exact versions from lockfile (fail if lockfile is outdated)
- `--no-dev`: Skip development dependencies (not needed in Docker)
- `--extra core --extra server`: Install optional dependency groups

### Why UV?

- **Speed**: 10-100x faster than pip for dependency resolution
- **Reproducibility**: Lockfile ensures identical builds everywhere
- **Modern**: Follows Python packaging standards (PEP 621, PEP 631)
- **Reliable**: Better conflict resolution than pip
- **Efficient**: Shared cache across projects, parallel downloads

## Planning Documents

All planning and analysis documents should be stored in this repository, not in the user's home directory:

- **Plans**: Store in `.claude/planning/` folder
- **Progress tracking**: Each plan should have a corresponding progress document in `.claude/plan-progress/`

This ensures plans and progress are version-controlled with the codebase and accessible to all developers. Format progress documents as `{plan-name}-progress.md` to establish a clear relationship with their corresponding plans.
