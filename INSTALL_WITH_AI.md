# Install with an AI coding assistant

Run this prompt only after cloning this repository on an Apple Silicon Mac. The ordinary supported path is still `./install.sh` followed by `./start.sh`.

```text
Help me install and run this local Kokoro PDF-to-audiobook project on my Apple Silicon Mac.

First read Readme.md, inventory.md, and architecture.md. Check that this is macOS on Apple Silicon and Python 3.11 is available. Explain that first setup downloads Python packages and the Kokoro model. Do not upload PDFs, audio, source code, credentials, or personal data anywhere. The app binds to the LAN by default for trusted home-network access; do not expose it to the public internet. Use APP_HOST=127.0.0.1 only when localhost-only access is wanted.

Use the repository's ./install.sh to create its .venv and install Python dependencies. For OCR of image-only PDFs, check for Tesseract; on macOS it can be installed with `brew install tesseract tesseract-lang`. If missing, explain that OCR won't work until it is installed; do not install system software without the user's request. If a command fails, show the error and explain the smallest safe fix. Do not use sudo, overwrite unrelated files, install global Python packages, or request/print secrets. Then run ./start.sh and tell me to open http://localhost:8501, or the displayed LAN URL on a trusted network. Do not process any PDF unless I explicitly choose one in the UI.
```
