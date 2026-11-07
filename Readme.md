# Kokoro PDF to Audiobook

A small, local web app for turning a text-based PDF into a WAV or MP3 audiobook. It runs Kokoro through MLX Audio on Apple Silicon, prepares extracted text for speech, and keeps the PDF and generated audio on your Mac.

## Quick start

Requires macOS on Apple Silicon and Python 3.11. The first launch downloads model files from Hugging Face.

```bash
git clone https://github.com/outspokende/kokoro-pdf-audiobook.git
cd kokoro-pdf-audiobook
./install.sh
./start.sh
```

Then open [http://localhost:8501](http://localhost:8501), upload a PDF you have the right to process, choose a voice and output format, and download the result. The app binds to localhost; it is not a public upload service.

## What it does

1. Extracts selectable PDF text and chapter headings.
2. Cleans common PDF artifacts, wraps, hyphenation, and boilerplate page furniture.
3. Splits prose into sentence-aware chunks for Kokoro.
4. Generates speech with a built-in Kokoro voice and joins it with short pauses.
5. Offers a WAV or MP3 download.

This prototype currently provides English Kokoro voices. Scanned/image-only PDFs need OCR first. Always review the extracted text before generating audio. Front-matter detection is heuristic; inspect the preview and disable its option if it would omit wanted content.

## Privacy and rights

Processing is local after dependencies and the model have been installed. The first installation/model load requires network access. Do not upload confidential PDFs or books you do not have permission to process. This project does not bypass DRM and does not clone voices.

## How the preprocessing relates to KokoroBooks

The PDF preparation grew out of the extraction, text-cleaning, chapter, and chunking work in KokoroBooks, adapted here into a standalone local workflow. Corpus-specific corrections and private library/server code are excluded.

The project code is licensed under AGPL-3.0. PyMuPDF is offered under AGPL or a commercial license; this project uses its AGPL option. Kokoro's MLX model is listed as Apache-2.0 on its model card. Check all dependency and model terms before redistributing modified versions or using generated audio commercially. See [PyMuPDF licensing](https://pymupdf.io/licensing), the [Kokoro model card](https://huggingface.co/mlx-community/Kokoro-82M-bf16), and [MLX Audio documentation](https://github.com/Blaizzy/mlx-audio/blob/main/docs/models/tts/kokoro.md).

## Documents

- [inventory.md](inventory.md) — components, dependencies, and current status
- [architecture.md](architecture.md) — data flow and local processing boundaries
- [INSTALL_WITH_AI.md](INSTALL_WITH_AI.md) — prompt for an AI coding assistant to install or troubleshoot
- [redaktionsnotiz.md](redaktionsnotiz.md) — factual wording for the related post

## Status

**Prototype.** UI and pipeline code are assembled but have not yet been run end to end with a real PDF/model on this machine. Henning reports Kokoro runs quickly on his 16 GB Mac; this new app's speed has not yet been measured.
