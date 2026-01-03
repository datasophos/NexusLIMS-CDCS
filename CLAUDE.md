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
# From the .dev-deployment directory:
source dev-commands.sh
dev-update-xslt        # Updates both detail and list stylesheets
# OR
dev-update-xslt-detail # Updates only detail_stylesheet.xsl
dev-update-xslt-list   # Updates only list_stylesheet.xsl
```

The update script (`.dev-deployment/scripts/update-xslt.sh`) automatically:
- Loads the XSL file from `.dev-deployment/cdcs/`
- Patches the `datasetBaseUrl` and `previewBaseUrl` variables for detail stylesheet
- Updates the stylesheet in the Django database
- Verifies the changes were applied

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
