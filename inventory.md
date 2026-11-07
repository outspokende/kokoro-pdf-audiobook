# Inventory

| Component | Role | Status |
|---|---|---|
| `app/preprocess.py` | PDF text extraction, automatic OCR for image-only pages, per-page checkpointing, cleanup, TOC-aware segmentation | OCR smoke-tested on an image-only page; full scan's text layer processed into 22 chapters |
| `app/tts.py` | Kokoro via MLX Audio; WAV checkpoints per chunk, resume, WAV/MP3 assembly | Pause/resume smoke-tested on a generated sample; full-book synthesis not run |
| `app/jobs.py` | Local job state, background worker, progress, cancellation and restart detection | Implemented; same PDF and settings resume from page/chunk checkpoints |
| `app/ui.py` | Streamlit upload, OCR-language selection, preview, live progress/cancel/resume, voice samples and download | UI workflow updated; requires manual walkthrough for a full book |
| `app/assets/voice_samples/` | Short, matching English MP3 previews for the six built-in voices | Generated locally with Kokoro for in-menu comparison |
| `install.sh`, `start.sh` | Create Python 3.11 virtualenv, install dependencies and run UI | Install and launch verified on Apple Silicon Mac |
| `samples/war-of-the-worlds/` | Scanned public-domain fixture with OCR text layer | 326-page sample; source and rights documented in folder README |

## Runtime assumptions

- macOS and Apple Silicon (MLX requirement). Henning reports Kokoro runs quickly on his 16 GB Mac; this app's own speed and minimum memory have not been measured.
- Python 3.11.
- Internet access for the initial Python package and model download.
- Kokoro model default: `mlx-community/Kokoro-82M-bf16` (model card lists Apache-2.0; confirm voice/data terms before use).
- PDF must contain extractable text. Image-only scans require a separate OCR step; scans with an OCR text layer can be processed.
- English presets only in this prototype; other languages are not yet exposed in the UI.
- MP3 encoding uses the FFmpeg binary bundled by `imageio-ffmpeg`; WAV is written directly.

## Exclusions

No source PDFs, generated audio, private voice samples, tokens, local server details, employer/customer material, or user-library metadata belong in this repository.
