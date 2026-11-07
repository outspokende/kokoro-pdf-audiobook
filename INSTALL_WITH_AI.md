# Install with an AI coding assistant

Run this prompt only after cloning this repository on an Apple Silicon Mac. The ordinary supported path is still `./install.sh` followed by `./start.sh`.

```text
Help me install and run this local Kokoro PDF-to-audiobook project on my Apple Silicon Mac.

First read Readme.md, inventory.md, and architecture.md. Check that this is macOS on Apple Silicon and Python 3.11 is available. Explain that first setup downloads Python packages and the Kokoro model. Do not upload my PDFs, audio, source code, credentials, or personal data anywhere. Do not expose this Streamlit app to the network or change its localhost binding.

Use the repository's ./install.sh to create its .venv and install dependencies. If a command fails, show the error and explain the smallest safe fix before changing system configuration. Do not use sudo, overwrite unrelated files, install global Python packages, or request/print secrets. Then run ./start.sh and tell me to open http://localhost:8501. Do not process any PDF unless I explicitly choose one in the UI.
```
