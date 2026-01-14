#!/bin/bash
# Update nexus-experiment.xsd from canonical source in NexusLIMS repository
# This script downloads the latest version of the schema file

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_DIR="${SCRIPT_DIR}/../schemas"
SCHEMA_FILE="${SCHEMA_DIR}/nexus-experiment.xsd"
CANONICAL_URL="https://raw.githubusercontent.com/datasophos/NexusLIMS/main/nexusLIMS/schemas/nexus-experiment.xsd"

# Create schemas directory if it doesn't exist
mkdir -p "$SCHEMA_DIR"

echo "→ Downloading nexus-experiment.xsd from canonical source..."
echo "  Source: ${CANONICAL_URL}"
echo "  Target: ${SCHEMA_FILE}"

# Download the schema file
if curl -f -L -o "$SCHEMA_FILE" "$CANONICAL_URL"; then
    echo "✓ Schema updated successfully"

    # Show file size
    SIZE=$(ls -lh "$SCHEMA_FILE" | awk '{print $5}')
    echo "  File size: ${SIZE}"

    # Show first few lines to verify it's an XML schema
    echo ""
    echo "First few lines of updated schema:"
    head -5 "$SCHEMA_FILE"

    echo ""
    echo "✓ Schema file is ready for deployment"
    echo ""
    echo "IMPORTANT: After updating the schema, you need to update it in the database:"
    echo "  • For development: Restart the dev environment (dev-down && dev-up)"
    echo "  • For production: Run 'docker exec <container> python /srv/scripts/init_environment.py'"
else
    echo "✗ Failed to download schema file"
    echo "  Check your internet connection and that the URL is correct"
    exit 1
fi
