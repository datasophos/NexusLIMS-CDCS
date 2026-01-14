#!/bin/bash
# Update XSLT stylesheets in the database
# Usage: ./update-xslt.sh [detail|list|all]

set -e

STYLESHEET_TYPE="${1:-all}"

# Get environment variables or use defaults
DATASET_BASE_URL="${XSLT_DATASET_BASE_URL:-https://files.nexuslims-dev.localhost/instrument-data}"
PREVIEW_BASE_URL="${XSLT_PREVIEW_BASE_URL:-https://files.nexuslims-dev.localhost/data}"

update_detail_stylesheet() {
    echo "Updating detail_stylesheet.xsl..."
    docker compose exec -T cdcs python manage.py shell << EOF
from core_main_app.components.xsl_transformation import api as xsl_transformation_api
from pathlib import Path

# Read from mounted xslt directory
stylesheet_path = Path("/srv/nexuslims/xslt/detail_stylesheet.xsl")
with stylesheet_path.open(encoding="utf-8") as f:
    stylesheet_content = f.read()

# Get URLs from environment (passed from host)
dataset_base_url = "${DATASET_BASE_URL}"
preview_base_url = "${PREVIEW_BASE_URL}"

# Patch URLs for file serving
print(f"Patching URLs in detail_stylesheet.xsl...")
print(f"  datasetBaseUrl: {dataset_base_url}")
print(f"  previewBaseUrl: {preview_base_url}")

stylesheet_content = stylesheet_content.replace(
    '<xsl:variable name="datasetBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>',
    f'<xsl:variable name="datasetBaseUrl">{dataset_base_url}</xsl:variable>'
)
stylesheet_content = stylesheet_content.replace(
    '<xsl:variable name="previewBaseUrl">https://CHANGE.THIS.VALUE</xsl:variable>',
    f'<xsl:variable name="previewBaseUrl">{preview_base_url}</xsl:variable>'
)

# Verify replacements
if dataset_base_url in stylesheet_content:
    print("  ✓ datasetBaseUrl patched")
else:
    print("  ✗ datasetBaseUrl patch failed or not found")

if preview_base_url in stylesheet_content:
    print("  ✓ previewBaseUrl patched")
else:
    print("  ✗ previewBaseUrl patch failed or not found")

# Update the stylesheet in the database
xslt = xsl_transformation_api.get_by_name("detail_stylesheet.xsl")
xslt.content = stylesheet_content
xslt = xsl_transformation_api.upsert(xslt)
print(f"Updated stylesheet '{xslt.name}' (ID: {xslt.id})")
EOF
    echo "✓ detail_stylesheet.xsl updated successfully"
}

update_list_stylesheet() {
    echo "Updating list_stylesheet.xsl..."
    docker compose exec -T cdcs python manage.py shell << 'EOF'
from core_main_app.components.xsl_transformation import api as xsl_transformation_api
from pathlib import Path

# Read from mounted xslt directory
stylesheet_path = Path("/srv/nexuslims/xslt/list_stylesheet.xsl")
with stylesheet_path.open(encoding="utf-8") as f:
    stylesheet_content = f.read()

# Update the stylesheet in the database
xslt = xsl_transformation_api.get_by_name("list_stylesheet.xsl")
xslt.content = stylesheet_content
xslt = xsl_transformation_api.upsert(xslt)
print(f"Updated stylesheet '{xslt.name}' (ID: {xslt.id})")
EOF
    echo "✓ list_stylesheet.xsl updated successfully"
}

case "$STYLESHEET_TYPE" in
    detail)
        update_detail_stylesheet
        ;;
    list)
        update_list_stylesheet
        ;;
    all)
        update_detail_stylesheet
        echo ""
        update_list_stylesheet
        ;;
    *)
        echo "Usage: $0 [detail|list|all]"
        echo "  detail - Update only detail_stylesheet.xsl"
        echo "  list   - Update only list_stylesheet.xsl"
        echo "  all    - Update both stylesheets (default)"
        exit 1
        ;;
esac

echo ""
echo "XSLT stylesheet(s) updated in database."
echo "Refresh your browser to see changes."
