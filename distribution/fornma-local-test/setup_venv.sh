#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "Python was not found. Install Python 3.10+ first."
  exit 1
fi

# Force the official PyPI index: some networks (e.g. university mirrors) point
# pip at an incomplete mirror where common packages (pillow, napari-TRACE) are
# missing, which breaks setup with "No matching distribution found".
PIP_INDEX="--index-url https://pypi.org/simple/"

"$PYTHON_BIN" -m venv "$ROOT_DIR/.venv"
"$ROOT_DIR/.venv/bin/python" -m pip install $PIP_INDEX --upgrade pip
"$ROOT_DIR/.venv/bin/pip" install $PIP_INDEX -r "$ROOT_DIR/requirements-local-ui.txt"

echo
echo "Setup complete."
echo "Run ./start_fornma.sh to start forNMA."
