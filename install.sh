#!/bin/sh
set -eu
cd "$(dirname "$0")"

if [ "$(uname -s)" != "Darwin" ] || [ "$(uname -m)" != "arm64" ]; then
  echo "This prototype currently requires macOS on Apple Silicon (arm64)." >&2
  exit 1
fi

if ! command -v python3.11 >/dev/null 2>&1; then
  echo "Python 3.11 is required. Install it from python.org or with Homebrew, then run this script again." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  python3.11 -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
if ! command -v tesseract >/dev/null 2>&1; then
  echo "Optional OCR is not installed. For scanned PDFs, run: brew install tesseract tesseract-lang"
fi
echo "Setup finished. Start the local app with ./start.sh"
