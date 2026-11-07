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

For scanned PDFs without a text layer, install the OCR engine once before starting the app:

```bash
brew install tesseract tesseract-lang
```

OCR is fixed to English to match the built-in English Kokoro voices. Tesseract's English language data must be installed for scanned PDFs.

Then open [http://localhost:8501](http://localhost:8501) on the Mac, or `http://<Mac-LAN-or-VPN-IP>:8501` from a device that can reach it. The app binds to all network interfaces by default for LAN/VPN access; use it only on a trusted network. Set `APP_HOST=127.0.0.1` before `./start.sh` to restrict it to the Mac. It is not a public upload service.

## What it does

1. Reads selectable PDF text; automatically applies OCR to image pages without a usable text layer.
2. Cleans common PDF artifacts, wraps, hyphenation, and boilerplate page furniture.
3. Splits prose into sentence-aware chunks for Kokoro.
4. Generates speech with a built-in Kokoro voice and joins it with short pauses.
5. Offers a WAV or MP3 download.

The interface includes a six-step timeline from PDF upload through OCR, text preparation, review, synthesis, and export. Each circle has a progress ring: completed steps are full, the active step follows its stage percentage, and upcoming steps are empty. The active stage also pulses gently; that animation respects the system’s reduced-motion preference. After preparation, a clear next-step panel below the timeline tells the user to review the preview above before selecting “Hörbuch erstellen.” Expand “So läuft die Pipeline ab” for an explanation of each stage and the resume workflow.

To try the pipeline without uploading your own book, tick **“Testbuch wählen: The War of the Worlds”** in the PDF panel. This selects the included 326-page PDF and disables the uploader while selected. The book is included at `samples/war-of-the-worlds/warofworlds1898well.pdf`; the [sample README](samples/war-of-the-worlds/README.md) documents its source and public-domain status. Review the prepared text first; generating the entire audiobook can take a long time.

Each available voice has a short English sample in the voice selector so listeners can compare them before generating an audiobook. OCR and synthesis progress are shown in the app. Page extraction and each speech chunk are checkpointed locally, so an interrupted job can resume with the same PDF and settings. The most recently completed audiobook remains downloadable from the top of the page if the upload widget resets or the browser reconnects.

This prototype currently provides English Kokoro voices. Image-only scans are OCR'd locally with Tesseract; pages with an existing text layer use that text. When “skip front matter” is enabled, common `PROLOGUE` and `CHAPTER 1/ONE/I` headings are recognized even if scan noise such as leading punctuation appears before them. Always review the extracted text before generating audio: OCR quality and front-matter detection remain dependent on the scan.

## Privacy and rights

Processing is local after dependencies and the model have been installed. The first installation/model load requires network access. Do not upload confidential PDFs or books you do not have permission to process. This project does not bypass DRM and does not clone voices.

## How the preprocessing relates to KokoroBooks

The PDF preparation grew out of the extraction, text-cleaning, chapter, and chunking work in KokoroBooks, adapted here into a standalone local workflow. Corpus-specific corrections and private library/server code are excluded.

The project code is licensed under AGPL-3.0. PyMuPDF is offered under AGPL or a commercial license; this project uses its AGPL option. Kokoro's MLX model is listed as Apache-2.0 on its model card. Check all dependency and model terms before redistributing modified versions or using generated audio commercially. See [PyMuPDF licensing](https://pymupdf.io/licensing), the [Kokoro model card](https://huggingface.co/mlx-community/Kokoro-82M-bf16), and [MLX Audio documentation](https://github.com/Blaizzy/mlx-audio/blob/main/docs/models/tts/kokoro.md).

## Documents

- [inventory.md](inventory.md) — components, dependencies, and current status
- [architecture.md](architecture.md) — data flow and local processing boundaries
- [validation.md](validation.md) — end-to-end test scope and results
- [samples/war-of-the-worlds/README.md](samples/war-of-the-worlds/README.md) — public-domain scanned fixture and provenance
- [INSTALL_WITH_AI.md](INSTALL_WITH_AI.md) — prompt for an AI coding assistant to install or troubleshoot
- [redaktionsnotiz.md](redaktionsnotiz.md) — factual wording for the related post

## Status

**Prototype.** Validated preprocessing on the included 326-page public-domain scan: 22 chapters, about 334k cleaned characters, and the narrative correctly bounded from its first chapter through “THE END.” Kokoro generated and encoded a 22-second WAV and MP3 excerpt. The app starts on the LAN/VPN interface. The landing page now recovers the newest completed local output after a browser reconnect. See [validation.md](validation.md).
