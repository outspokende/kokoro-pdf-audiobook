# End-to-end validation

Date: 2026-11-07. Machine: Apple Silicon Mac, Python 3.11, 16 GB RAM.

## Input and preprocessing

- Fixture: [The War of the Worlds scan](samples/war-of-the-worlds/README.md), a 326-page scanned PDF with an OCR text layer.
- The current preprocessing run found 22 narrative chapter starts using the printed contents page, removed repeated page furniture, skipped front matter, and stopped at `THE END` before the library circulation card.
- Result: 333,393 characters in 1,101 speech chunks. OCR mistakes remain in the source layer; inspect the preview before generating a complete book.
- Image-only scans without a text layer are not OCR'd by this app and will not work as-is.

## Speech and runtime

- Kokoro `af_heart` generated the first prepared paragraph as a 22.025-second, 24 kHz mono WAV.
- The same paragraph encoded to a 193,340-byte MP3 at about 70 kb/s. After the model was warm, that run took about 9 seconds.
- `./install.sh` completed. `./start.sh` started Streamlit bound to `0.0.0.0:8501`; the app displayed a LAN URL and its page was reachable at `http://192.168.178.89:8501` during this session. That address can change with DHCP; users should use their Mac's current LAN/VPN-reachable IP.

## Limits of this run

This confirms PDF extraction/preprocessing and the Kokoro WAV/MP3 synthesis/encoding functions on real text from the scan. It does **not** confirm synthesis of all 1,101 chunks, a complete multi-hour audiobook, or the final browser download-button interaction. The temporary three-page excerpt and generated audio were not added to the repository.
