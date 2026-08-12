#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Could not find the local virtual environment."
  echo "Run ./setup_venv.sh from this same folder before starting forNMA."
  exit 1
fi

if ! "$PYTHON_BIN" -c "import fastapi, uvicorn, plotly, multipart"; then
  echo "The local virtual environment is missing required packages."
  echo "Run ./setup_venv.sh again from this same folder."
  echo "If setup says everything is already satisfied, delete the .venv folder and run ./setup_venv.sh again."
  exit 1
fi

echo "Starting forNMA with:"
echo "  $PYTHON_BIN"
echo

exec "$PYTHON_BIN" "$ROOT_DIR/launcher/start_fornma.py"
