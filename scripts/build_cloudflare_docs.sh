#!/usr/bin/env bash
# Build the CDCS guide for a Cloudflare Pages branch preview.
set -euo pipefail

python -m pip install uv
python -m uv run --locked --only-group docs sphinx-build -b html -n -W --keep-going docs docs/_build/html
