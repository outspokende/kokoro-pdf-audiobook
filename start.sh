#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/streamlit ]; then
  echo "Run ./install.sh first." >&2
  exit 1
fi
exec .venv/bin/streamlit run app/ui.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
