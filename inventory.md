# Inventory

| Component | Role | Status |
|---|---|---|
| `app/preprocess.py` | PDF text extraction, automatic OCR for image-only pages, per-page checkpointing, cleanup including stray asterisk repair, TOC-aware segmentation and noise-tolerant narrative-start detection | Noisy front-matter and OCR asterisks handled; source text still requires review |
| `app/tts.py` | Kokoro via MLX Audio; WAV checkpoints per chunk, resume, WAV/MP3 assembly, MP3 cover and title metadata | Embedded cover/title verified on generated full-length MP3; full-book playback not independently verified |
| `app/jobs.py` | Local job state, source filename/title, PDF first-page cover, progress, cancellation and restart detection | Same PDF/settings resume from checkpoints; metadata and cover are saved locally per job |
| `app/ui.py` | Dark studio-style Streamlit interface; PDF upload or included public-domain book checkbox, English-only OCR, manual text review, six-step live timeline, voice samples, recovery download with cover and filename-based title | Recovery cover/title card visually checked against a locally completed job; full-book playback not independently verified |
| `app/assets/voice_samples/` | Short, matching English MP3 previews for the six built-in voices | Generated locally with Kokoro for in-menu comparison |
| `install.sh`, `start.sh` | Create Python 3.11 virtualenv, install dependencies and run UI | Install and launch verified on Apple Silicon Mac |
| `samples/war-of-the-worlds/` | Scanned public-domain fixture with OCR text layer | 326-page sample; source and rights documented in folder README |

## Runtime assumptions

- macOS and Apple Silicon (MLX requirement). Henning reports Kokoro runs quickly on his 16 GB Mac; this app's own speed and minimum memory have not been measured.
- Python 3.11.
- Internet access for the initial Python package and model download.
- Kokoro model default: `mlx-community/Kokoro-82M-bf16` (model card lists Apache-2.0; confirm voice/data terms before use).
- PDF must contain extractable text. Image-only scans require a separate OCR step; scans with an OCR text layer can be processed.
- English-only OCR and Kokoro voice presets are exposed in the prototype.
- MP3 encoding uses the FFmpeg binary bundled by `imageio-ffmpeg`; WAV is written directly.

## Exclusions

No source PDFs, generated audio, private voice samples, tokens, local server details, employer/customer material, or user-library metadata belong in this repository.
