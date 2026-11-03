# XSLT Stylesheet Development

```{important}
XSLT stylesheets are stored in the Django database, not just as files. Editing the `.xsl` file is not enough - you must update the database.
```

## Update Process

1. Edit the XSL file in `xslt/` (at repository root)
2. Update the database:

```bash
cd deployment
source dev-commands.sh
dev-update-xslt
```

3. Refresh your browser to see changes

## URL Configuration

The update script automatically patches URLs in the XSLT based on environment variables:
- `XSLT_DATASET_BASE_URL` - Base URL for instrument data files
- `XSLT_PREVIEW_BASE_URL` - Base URL for preview images

Development defaults:
```bash
XSLT_DATASET_BASE_URL=https://files.nexuslims-dev.localhost/instrument-data
XSLT_PREVIEW_BASE_URL=https://files.nexuslims-dev.localhost/data
```
