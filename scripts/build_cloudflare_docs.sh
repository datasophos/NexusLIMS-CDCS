#!/usr/bin/env bash
# Build the CDCS guide for a Cloudflare Pages branch preview.
set -euo pipefail

python -m pip install -r docs/requirements.txt
python -m sphinx -b html -n -W --keep-going docs docs/_build/html
