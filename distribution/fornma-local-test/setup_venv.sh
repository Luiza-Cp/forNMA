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

"$PYTHON_BIN" -m venv "$ROOT_DIR/.venv"
"$ROOT_DIR/.venv/bin/python" -m pip install --upgrade pip
"$ROOT_DIR/.venv/bin/python" -m pip install -r "$ROOT_DIR/requirements-local-ui.txt"
"$ROOT_DIR/.venv/bin/python" -c "import fastapi, uvicorn, plotly, multipart"

echo
echo "Setup complete."
echo "Run ./start_fornma.sh to start forNMA."
