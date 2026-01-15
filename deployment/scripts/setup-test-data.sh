#!/bin/bash
# Extract NexusLIMS test data if not already extracted
# This script runs on the host before starting Docker containers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DATA_DIR="${SCRIPT_DIR}/../test-data"
ARCHIVE="${TEST_DATA_DIR}/nexuslims-test-data.tar.gz"

# Check if archive exists
if [ ! -f "$ARCHIVE" ]; then
    echo "⚠ Test data archive not found: $ARCHIVE"
    echo "→ Skipping test data extraction"
    exit 0
fi

# Check if data is already extracted
if [ -d "${TEST_DATA_DIR}/nx-data" ] && [ -d "${TEST_DATA_DIR}/nx-instrument-data" ] && [ -f "${TEST_DATA_DIR}/example_record.xml" ]; then
    echo "✓ Test data already extracted"
    exit 0
fi

# Extract the archive
echo "→ Extracting test data from nexuslims-test-data.tar.gz..."
tar -xzf "$ARCHIVE" -C "$TEST_DATA_DIR"

if [ $? -eq 0 ]; then
    echo "✓ Test data extracted successfully"
else
    echo "✗ Failed to extract test data"
    exit 1
fi
