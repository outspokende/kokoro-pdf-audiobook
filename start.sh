#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/streamlit ]; then
  echo "Run ./install.sh first." >&2
  exit 1
fi
APP_HOST=${APP_HOST:-0.0.0.0}
APP_PORT=${APP_PORT:-8501}
PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPATH
printf '\n' | .venv/bin/streamlit run app/ui.py --server.address "$APP_HOST" --server.port "$APP_PORT" --browser.gatherUsageStats false
