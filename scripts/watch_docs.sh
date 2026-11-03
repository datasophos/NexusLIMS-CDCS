#!/usr/bin/env bash
# Build, serve, and automatically rebuild the CDCS documentation.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
exec uv run --group docs sphinx-autobuild -b html -n --host 127.0.0.1 --port 8765 docs docs/_build/html "$@"
