# Inventory

| Component | Role | Status |
|---|---|---|
| `app/preprocess.py` | PDF text extraction, repeated header/footer suppression, cleanup, TOC-aware segmentation, sentence chunks | Tested on the included 326-page scan; 22 chapters and about 333k cleaned characters |
| `app/tts.py` | Kokoro via MLX Audio; sequential chunk generation and WAV/MP3 assembly | Confirmed 22-second WAV and MP3 excerpt; full-book synthesis not run |
| `app/ui.py` | Streamlit upload, text preview, voice/format choices and download | Starts on LAN/VPN and page is reachable; browser upload/download flow not fully verified |
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
