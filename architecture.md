# Architecture

The Streamlit app runs on `0.0.0.0:8501` by default, so it is reachable from the Mac and devices on a trusted LAN/VPN. Set `APP_HOST=127.0.0.1` before `./start.sh` to limit access to the Mac. A PDF selected in the browser is passed to the local Python process, saved temporarily, preprocessed, synthesized one chunk at a time, assembled, and returned through a download button.

```text
Browser on Mac or trusted LAN/VPN
   │ local-network upload
   ▼
Streamlit UI ──> Per-page text check ──> Tesseract OCR if needed
   │                                      │
   │                              cleanup/chapter split/chunking
   │                                      │
   │                                Kokoro / MLX Audio
   │                                      │
   └──────── WAV / MP3 download <── checkpointed chunks + assembly
```

PDF bytes and audio remain on the Mac during inference. The app has no accounts or remote storage; anyone able to reach the bound interface can use it, so do not expose it to an untrusted network. Completed jobs remain under `output/jobs/`; the UI surfaces the newest existing output on the landing view so it can still be downloaded after a browser reconnect or uploader reset. Package installation and initial model retrieval contact external package/model hosts.

## Processing stages

1. Extract page text and built-in PDF TOC with PyMuPDF. Pages that contain an image but fewer than 24 selectable text characters are OCR'd with Tesseract (220 DPI, user-selected language).
2. Remove recurring header/footer lines only when they repeat consistently, normalize common typography, join line-wrapped text and dehyphenate line-break splits.
3. Use TOC entries as chapter boundaries where present; otherwise treat the document as one chapter. Optional front-matter skipping uses conservative heuristics and is user-adjustable.
4. Split on paragraph/sentence boundaries, targeting short chunks to fit TTS.
5. Generate each text chunk sequentially with a selected preset voice. Each completed chunk is atomically saved as WAV under `output/jobs/`.
6. Assemble the saved chunks with short sentence/paragraph gaps, then export WAV or MP3. If a job is interrupted, the app reuses finished OCR pages and audio chunks.

Front matter is detected heuristically from chapter starts inferred from a printed contents page when no embedded PDF TOC is available. If no contents page is found, common English openings (`PROLOGUE`, `CHAPTER 1`, `CHAPTER ONE`, or `CHAPTER I`) are recognized even when leading scan punctuation appears before the heading. Review the preview before audio generation. Pages with an existing text layer use that layer; OCR quality remains dependent on the source scan. Jobs are keyed to the uploaded PDF and chosen settings plus a preprocessing revision; after a preprocessing fix, the app creates a fresh job so stale text and audio checkpoints are not reused.
