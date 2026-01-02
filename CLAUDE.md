# Claude Code Context

Important information for working with this codebase.

## XSLT Stylesheet Updates

**CRITICAL**: XSLT stylesheets are stored in the Django database, not just as files on disk.

### Files Location
- Detail stylesheet: `.dev-deployment/cdcs/detail_stylesheet.xsl`
- List stylesheet: `.dev-deployment/cdcs/list_stylesheet.xsl`

### Update Process

1. **Edit the XSL file** in `.dev-deployment/cdcs/`

2. **Update the database** (REQUIRED - changes won't appear otherwise):

```bash
docker compose -f .dev-deployment/docker-compose.yml exec -T cdcs python manage.py shell << 'EOF'
from core_main_app.components.xsl_transformation import api as xsl_transformation_api
from pathlib import Path

stylesheet_path = Path("/srv/curator/cdcs_config/detail_stylesheet.xsl")
with stylesheet_path.open(encoding="utf-8") as f:
    stylesheet_content = f.read()

# Patch URLs for file serving
print("Patching URLs in detail_stylesheet.xsl...")
stylesheet_content = stylesheet_content.replace(
    '<xsl:variable name="datasetBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>',
    '<xsl:variable name="datasetBaseUrl">https://files.nexuslims-dev.localhost/instrument-data</xsl:variable>'
)
stylesheet_content = stylesheet_content.replace(
    '<xsl:variable name="previewBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>',
    '<xsl:variable name="previewBaseUrl">https://files.nexuslims-dev.localhost/data</xsl:variable>'
)

# Verify replacements
if 'https://files.nexuslims-dev.localhost/instrument-data' in stylesheet_content:
    print("  ✓ datasetBaseUrl patched")
else:
    print("  ✗ datasetBaseUrl patch failed or not found")

if 'https://files.nexuslims-dev.localhost/data' in stylesheet_content:
    print("  ✓ previewBaseUrl patched")
else:
    print("  ✗ previewBaseUrl patch failed or not found")

# Update the stylesheet in the database
xslt = xsl_transformation_api.get_by_name("detail_stylesheet.xsl")
xslt.content = stylesheet_content
xslt = xsl_transformation_api.upsert(xslt)
print(f"Updated stylesheet '{xslt.name}' (ID: {xslt.id})")
EOF
```

### Notes
- Just editing the file is NOT enough - you must update the database
- The XSLT transforms XML records to HTML for display in the browser
- The init script loads these on initial setup but doesn't auto-reload on changes
- The init script automatically patches `datasetBaseUrl` and `previewBaseUrl` `<xsl:variable>` elements to:
  - `datasetBaseUrl`: `https://files.nexuslims-dev.localhost/instrument-data`
  - `previewBaseUrl`: `https://files.nexuslims-dev.localhost/data`
- If you manually update stylesheets outside the init script, apply these patches before uploading to the database

## Planning Documents

All planning and analysis documents should be stored in this repository, not in the user's home directory:

- **Plans**: Store in `.claude/planning/` folder
- **Progress tracking**: Each plan should have a corresponding progress document in `.claude/plan-progress/`

This ensures plans and progress are version-controlled with the codebase and accessible to all developers. Format progress documents as `{plan-name}-progress.md` to establish a clear relationship with their corresponding plans.
