#!/usr/bin/env bash
# manage-demo-fixtures.sh - Manage demo fixture data via GitHub Releases
#
# Demo fixture data (~195MB of preview images) is too large for git.
# This script uploads/downloads from a dedicated GitHub Release tag.
#
# Usage:
#   ./manage-demo-fixtures.sh upload    # Package and upload demo_data to the release
#   ./manage-demo-fixtures.sh download  # Download and extract demo_data from the release
#   ./manage-demo-fixtures.sh status    # Show what assets are in the release
#
# Environment variables (with defaults):
#   DEMO_FIXTURES_REPO  - GitHub repo slug (default: datasophos/NexusLIMS-CDCS)
#   DEMO_FIXTURES_TAG   - Release tag to use  (default: demo-fixtures-latest)

set -e

REPO="${DEMO_FIXTURES_REPO:-datasophos/NexusLIMS-CDCS}"
TAG="${DEMO_FIXTURES_TAG:-demo-fixtures-latest}"
ASSET_NAME="demo_data.tar.gz"

# Resolve paths relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
FIXTURES_DIR="${DEPLOYMENT_DIR}/fixtures"
DEMO_DATA_DIR="${FIXTURES_DIR}/demo_data"

# ── helpers ──────────────────────────────────────────────────────────────────

require_gh() {
    if ! command -v gh &>/dev/null; then
        echo "error: 'gh' (GitHub CLI) is required but not installed." >&2
        echo "       Install from https://cli.github.com/" >&2
        exit 1
    fi
    if ! gh auth status &>/dev/null; then
        echo "error: not authenticated with GitHub CLI. Run 'gh auth login'." >&2
        exit 1
    fi
}

ensure_release_exists() {
    if ! gh release view "${TAG}" --repo "${REPO}" &>/dev/null; then
        echo "Release '${TAG}' does not exist on ${REPO}. Creating it..."
        gh release create "${TAG}" \
            --repo "${REPO}" \
            --title "Demo Fixture Data" \
            --notes "Large binary demo fixture files (preview images) for the live NexusLIMS demo deployment. Managed automatically by manage-demo-fixtures.sh and not tied to a software release. Contains a variety of preview images and metadata extracted from public datasets." \
            --prerelease
        echo "Release created."
    fi
}

# ── subcommands ───────────────────────────────────────────────────────────────

cmd_upload() {
    require_gh

    if [ ! -d "${DEMO_DATA_DIR}" ]; then
        echo "error: ${DEMO_DATA_DIR} does not exist - nothing to upload." >&2
        exit 1
    fi

    ensure_release_exists

    TARBALL="/tmp/${ASSET_NAME}"
    echo "Packaging ${DEMO_DATA_DIR} -> ${TARBALL}..."
    COPYFILE_DISABLE=1 tar -czf "${TARBALL}" \
        -C "${FIXTURES_DIR}" \
        --exclude=".DS_Store" \
        --exclude="._*" \
        demo_data
    SIZE=$(du -sh "${TARBALL}" | cut -f1)
    echo "Packed ${SIZE}"

    echo "Uploading to https://github.com/${REPO}/releases/tag/${TAG}..."
    gh release upload "${TAG}" "${TARBALL}" \
        --repo "${REPO}" \
        --clobber
    rm -f "${TARBALL}"

    echo "Done. Fixtures are live at:"
    echo "  https://github.com/${REPO}/releases/download/${TAG}/${ASSET_NAME}"
}

cmd_download() {
    TARBALL="/tmp/${ASSET_NAME}"

    echo "Downloading demo fixtures from github.com/${REPO}/releases/tag/${TAG}..."
    DOWNLOAD_URL="https://github.com/${REPO}/releases/download/${TAG}/${ASSET_NAME}"

    if command -v gh &>/dev/null && gh auth status &>/dev/null; then
        gh release download "${TAG}" \
            --repo "${REPO}" \
            --pattern "${ASSET_NAME}" \
            --dir /tmp \
            --clobber
    else
        # Fall back to curl for unauthenticated download (works for public repos)
        curl -fL --progress-bar -o "${TARBALL}" "${DOWNLOAD_URL}"
    fi

    echo "Extracting to ${FIXTURES_DIR}..."
    mkdir -p "${FIXTURES_DIR}"
    tar -xzf "${TARBALL}" -C "${FIXTURES_DIR}"
    rm -f "${TARBALL}"

    echo "Done. Demo fixtures are at ${DEMO_DATA_DIR}"
}

cmd_status() {
    require_gh
    echo "Release: ${TAG} on ${REPO}"
    echo ""
    if gh release view "${TAG}" --repo "${REPO}" &>/dev/null; then
        gh release view "${TAG}" --repo "${REPO}" --json assets \
            --jq '.assets[] | "\(.name)  \(.size / 1048576 | floor)MB  updated: \(.updatedAt)"'
    else
        echo "(release does not exist yet)"
    fi
}

# ── dispatch ──────────────────────────────────────────────────────────────────

case "${1:-}" in
    upload)   cmd_upload ;;
    download) cmd_download ;;
    status)   cmd_status ;;
    *)
        echo "Usage: $(basename "$0") <upload|download|status>"
        echo ""
        echo "  upload    Package deployment/fixtures/demo_data/ and push to GitHub Release"
        echo "  download  Pull demo_data from GitHub Release and extract locally"
        echo "  status    Show assets currently attached to the release"
        echo ""
        echo "Env vars: DEMO_FIXTURES_REPO (default: ${REPO})"
        echo "          DEMO_FIXTURES_TAG  (default: ${TAG})"
        exit 1
        ;;
esac
