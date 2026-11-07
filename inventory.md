# Inventory

| Component | Role | Status |
|---|---|---|
| `app/preprocess.py` | PDF text extraction, basic boilerplate removal, cleaning, TOC-aware segmentation, sentence chunks | Prototype; adapted from KokoroBooks work |
| `app/tts.py` | Kokoro via MLX Audio; sequential chunk generation and WAV/MP3 assembly | Prototype; API pattern follows KokoroBooks backend |
| `app/ui.py` | Local Streamlit upload, text preview, voice/format choices and download | Prototype; not run end to end |
| `install.sh`, `start.sh` | Create Python 3.11 virtualenv, install dependencies and run UI | Draft; not executed |

## Runtime assumptions

- macOS and Apple Silicon (MLX requirement). Henning reports Kokoro runs quickly on his 16 GB Mac; this app's own speed and minimum memory have not been measured.
- Python 3.11.
- Internet access for the initial Python package and model download.
- Kokoro model default: `mlx-community/Kokoro-82M-bf16` (model card lists Apache-2.0; confirm voice/data terms before use).
- PDF must contain extractable text. Scans require OCR separately.
- English presets only in this prototype; other languages are not yet exposed in the UI.
- MP3 encoding uses the FFmpeg binary bundled by `imageio-ffmpeg`; WAV is written directly.

## Exclusions

No source PDFs, generated audio, private voice samples, tokens, local server details, employer/customer material, or user-library metadata belong in this repository.
