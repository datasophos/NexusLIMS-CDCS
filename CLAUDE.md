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

## Planning Documents

All planning and analysis documents should be stored in this repository, not in the user's home directory:

- **Plans**: Store in `.claude/planning/` folder
- **Progress tracking**: Each plan should have a corresponding progress document in `.claude/plan-progress/`

This ensures plans and progress are version-controlled with the codebase and accessible to all developers. Format progress documents as `{plan-name}-progress.md` to establish a clear relationship with their corresponding plans.
