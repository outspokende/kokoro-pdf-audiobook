# Architecture

The Streamlit app runs on `0.0.0.0:8501` by default, so it is reachable from the Mac and devices on a trusted LAN/VPN. Set `APP_HOST=127.0.0.1` before `./start.sh` to limit access to the Mac. A PDF selected in the browser is passed to the local Python process, saved temporarily, preprocessed, synthesized one chunk at a time, assembled, and returned through a download button.

```text
Browser on Mac or trusted LAN/VPN
   │ local-network upload
   ▼
Streamlit UI ──> PyMuPDF extraction ──> cleanup/chapter split/chunking
   │                                             │
   │                                     Kokoro / MLX Audio
   │                                             │
   └──────── WAV / MP3 download <── concatenate audio chunks
```

PDF bytes and audio remain on the Mac during inference. The app has no accounts or remote storage; anyone able to reach the bound interface can use it, so do not expose it to an untrusted network. Package installation and initial model retrieval contact external package/model hosts.

## Processing stages

1. Extract page text and built-in PDF TOC with PyMuPDF. Image-only scans need OCR; scans with an OCR text layer are supported.
2. Remove recurring header/footer lines only when they repeat consistently, normalize common typography, join line-wrapped text and dehyphenate line-break splits.
3. Use TOC entries as chapter boundaries where present; otherwise treat the document as one chapter. Optional front-matter skipping uses conservative heuristics and is user-adjustable.
4. Split on paragraph/sentence boundaries, targeting short chunks to fit TTS.
5. Generate audio sequentially with a selected preset voice.
6. Add small sentence/paragraph gaps, then export WAV or MP3.

Front matter is detected heuristically from chapter starts inferred from a printed contents page when no embedded PDF TOC is available. Review the preview before audio generation. OCR quality remains dependent on the source text layer.
