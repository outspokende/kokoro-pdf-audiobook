# Architecture

The Streamlit app runs on `127.0.0.1:8501`. A PDF selected in the browser is passed to the local Python process, saved to a temporary directory, preprocessed, synthesized one chunk at a time, assembled, and returned through a download button.

```text
Browser on this Mac
   │ localhost upload
   ▼
Streamlit UI ──> PyMuPDF extraction ──> cleanup/chapter split/chunking
   │                                             │
   │                                     Kokoro / MLX Audio
   │                                             │
   └──────── WAV / MP3 download <── concatenate audio chunks
```

PDF bytes and audio remain on the Mac during inference. The app is deliberately bound to localhost and has no accounts, upload endpoint, or remote storage. Package installation and initial model retrieval do contact external package/model hosts.

## Processing stages

1. Extract page text and built-in PDF TOC with PyMuPDF.
2. Remove recurring header/footer lines only when they repeat consistently, normalize common typography, join line-wrapped text and dehyphenate line-break splits.
3. Use TOC entries as chapter boundaries where present; otherwise treat the document as one chapter. Optional front-matter skipping uses conservative heuristics and is user-adjustable.
4. Split on paragraph/sentence boundaries, targeting short chunks to fit TTS.
5. Generate audio sequentially with a selected preset voice.
6. Add small sentence/paragraph gaps, then export WAV or MP3.

This prototype has no OCR and no guaranteed automatic identification of story starts. The preview is there so a person can catch extraction errors before audio generation.
