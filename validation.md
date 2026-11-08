# End-to-end validation

Date: 2026-11-07. Machine: Apple Silicon Mac, Python 3.11, 16 GB RAM.

## Input and preprocessing

- Fixture: [The War of the Worlds scan](samples/war-of-the-worlds/README.md), a 326-page scanned PDF with an OCR text layer.
- The current preprocessing run found 22 narrative chapter starts using the printed contents page, removed repeated page furniture, skipped front matter, and stopped at `THE END` before the library circulation card.
- Result: 334,144 characters in 1,110 speech chunks. OCR mistakes remain in the source layer; inspect the preview before generating a complete book.
- Image-only scans are OCR'd when Tesseract and the selected language data are installed.

## Speech and runtime

- Kokoro `af_heart` generated the first prepared paragraph as a 22.025-second, 24 kHz mono WAV.
- The same paragraph encoded to a 193,340-byte MP3 at about 70 kb/s. After the model was warm, that run took about 9 seconds.
- The complete 1,110-chunk fixture audiobook was regenerated after removing stray asterisks from 81 text chunks. The MP3 was remuxed with the first PDF page as attached artwork and the filename stem as its title; both metadata and image stream were verified. Full-length playback was not reviewed.
- On 2026-11-08, the completed-audiobook download button in the browser returned `warofworlds1898well.mp3` (172,161,547 bytes; valid ID3 header). This confirms the browser download path for a completed job.
- `./install.sh` completed. `./start.sh` started Streamlit bound to `0.0.0.0:8501`; the app displayed a LAN URL and its page was reachable at `http://192.168.178.89:8501` during this session. That address can change with DHCP; users should use their Mac's current LAN/VPN-reachable IP.

## OCR and resume checks

- Created a temporary one-page image-only PDF from the scan. Tesseract OCR extracted the first chapter text and reported page-level progress.
- Interrupted a one-chunk Kokoro MP3 job after its WAV checkpoint was written. Restarting synthesis reused that checkpoint and produced a valid MP3.
- Generated six short MP3 previews with the same English sentence; the live UI renders the selected preview under the voice menu.

## Limits of this run

This confirms PDF extraction/preprocessing, Kokoro WAV/MP3 synthesis/encoding, and the completed-job browser download path on the included scan. It does **not** confirm uninterrupted synthesis of all 1,110 chunks in one run or full-length listening review. The temporary excerpts and generated audio were not added to the repository.
