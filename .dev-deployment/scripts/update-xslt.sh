#!/bin/bash
# Update XSLT stylesheets in the database
# Usage: ./update-xslt.sh [detail|list|all]

set -e

STYLESHEET_TYPE="${1:-all}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CDCS_DIR="$(dirname "$SCRIPT_DIR")/cdcs"

update_detail_stylesheet() {
    echo "Updating detail_stylesheet.xsl..."
    docker compose exec -T cdcs python manage.py shell << 'EOF'
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
    echo "✓ detail_stylesheet.xsl updated successfully"
}

update_list_stylesheet() {
    echo "Updating list_stylesheet.xsl..."
    docker compose exec -T cdcs python manage.py shell << 'EOF'
from core_main_app.components.xsl_transformation import api as xsl_transformation_api
from pathlib import Path

stylesheet_path = Path("/srv/curator/cdcs_config/list_stylesheet.xsl")
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
