from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import streamlit as st

from app import jobs

st.set_page_config(page_title="Kokoro PDF to Audiobook", page_icon="📚", layout="centered")
st.title("PDF → Hörbuch")
st.caption("Lokal auf deinem Mac. PDF-Text wird bereinigt und mit einer Kokoro-Stimme vorgelesen.")
st.info("Voraussetzung: Apple-Silicon-Mac. PDFs ohne Texterkennung werden automatisch per OCR gelesen. Nur PDFs verarbeiten, für die du die nötigen Rechte hast.")

upload = st.file_uploader("PDF auswählen", type=["pdf"], max_upload_size=100)
skip_front = st.checkbox(
    "Vorspann überspringen, wenn Kapitel erkannt werden", value=True,
    help="Das Inhaltsverzeichnis hilft, die Geschichte zu finden. Bitte die Textvorschau prüfen.",
)
ocr_language = st.selectbox("OCR-Sprache für Scans", ["eng", "deu", "eng+deu"],
                            format_func={"eng": "English", "deu": "Deutsch", "eng+deu": "English + Deutsch"}.__getitem__)
if not shutil.which("tesseract"):
    st.warning("Für bildbasierte PDFs wird Tesseract benötigt. Auf macOS einmalig im Terminal ausführen: `brew install tesseract tesseract-lang`.")
else:
    language_output = subprocess.run(["tesseract", "--list-langs"], capture_output=True,
                                    text=True, check=False).stdout.splitlines()[1:]
    installed_languages = {language.strip() for language in language_output if language.strip()}
    missing_languages = set(ocr_language.split("+")) - installed_languages
    if missing_languages:
        st.warning(f"Tesseract-Sprachdaten fehlen: {', '.join(sorted(missing_languages))}. Auf macOS: `brew install tesseract-lang`.")

voices = ["af_heart", "af_bella", "am_michael", "am_adam", "bf_emma", "bm_george"]
voice_labels = {
    "af_heart": "🇺🇸 👩 American female · Heart",
    "af_bella": "🇺🇸 👩 American female · Bella",
    "am_michael": "🇺🇸 👨 American male · Michael",
    "am_adam": "🇺🇸 👨 American male · Adam",
    "bf_emma": "🇬🇧 👩 British female · Emma",
    "bm_george": "🇬🇧 👨 British male · George",
}
voice = st.selectbox("Kokoro-Stimme", voices, format_func=voice_labels.__getitem__)
voice_sample = Path(__file__).parent / "assets" / "voice_samples" / f"{voice}.mp3"
if voice_sample.is_file():
    st.caption("Kurze englische Hörprobe dieser Stimme")
    st.audio(voice_sample.read_bytes(), format="audio/mpeg")
output_format = st.radio("Downloadformat", ["mp3", "wav"], horizontal=True)

if upload is None:
    st.caption("Unterbrochene Jobs lassen sich mit derselben PDF und denselben Einstellungen fortsetzen.")
    st.divider()
    st.caption("PDF und Audio bleiben lokal auf diesem Mac. Für automatische OCR muss Tesseract installiert sein.")
    st.stop()

pdf_bytes = upload.getvalue()
settings = {
    "skip_front_matter": skip_front,
    "ocr_language": ocr_language,
    "voice": voice,
    "output_format": output_format,
}
job_id = jobs.job_id_for(pdf_bytes, settings)
folder = jobs.job_dir(job_id)
source = jobs.ensure_source(folder, pdf_bytes)
prepared_file = folder / "prepared.json"
prepared = jobs._read_json(prepared_file)
status = jobs.status_for(job_id)

if not prepared and status.get("state") not in {"running", "cancelled", "interrupted", "error"}:
    if st.button("PDF analysieren und Text aufbereiten", type="primary"):
        if not jobs.start_preparation(job_id, settings):
            st.warning("Ein anderer Hörbuchjob läuft gerade. Bitte warten, bis er pausiert oder fertig ist.")
        st.rerun()

if prepared:
    st.success(f"Text vorbereitet · {prepared['page_count']} PDF-Seiten · {len(prepared['chunks'])} Sprachabschnitte")
    st.text_area("Textvorschau – bitte auf OCR-Fehler prüfen", prepared["text"], height=260)
    if status.get("state") == "review" and not jobs.thread_running(job_id):
        if st.button("Hörbuch erstellen / fortsetzen", type="primary"):
            if not jobs.start_audio(job_id, settings):
                st.warning("Ein anderer Hörbuchjob läuft gerade. Bitte warten.")
            st.rerun()

if status:
    running = jobs.thread_running(job_id)

    @st.fragment(run_every=1 if running else None)
    def show_job_progress(current_job_id: str):
        current = jobs.status_for(current_job_id)
        is_running = jobs.thread_running(current_job_id)
        if running and not is_running:
            st.rerun()
        labels = {
            "extract": "PDF-Seiten lesen",
            "ocr": "Texterkennung (OCR)",
            "clean": "Text bereinigen und aufteilen",
            "review": "Textprüfung",
            "load_model": "Kokoro-Modell laden",
            "tts": "Sprache erzeugen",
            "merge": "Audiodatei zusammensetzen",
            "export": "MP3-Datei kodieren",
            "complete": "Abgeschlossen",
        }
        if current.get("state") == "running":
            st.progress(min(current.get("percent", 0), 100) / 100,
                        text=f"Gesamtfortschritt: {current.get('percent', 0)} %")
            st.progress(min(current.get("stage_percent", 0), 100) / 100,
                        text=f"{labels.get(current.get('stage'), 'Verarbeitung')}: {current.get('message', '')}")
            if st.button("Anhalten", key=f"cancel-{current_job_id}"):
                jobs.request_cancel(current_job_id)
            return

        if current.get("state") == "complete":
            st.success(current.get("message", "Hörbuch fertig"))
            output = folder / current["output"]
            if output.is_file():
                st.download_button(
                    "Hörbuch herunterladen", output.read_bytes(), file_name=f"{Path(upload.name).stem}.{output_format}",
                    mime="audio/mpeg" if output_format == "mp3" else "audio/wav",
                    key=f"download-{current_job_id}", type="primary",
                )
            return

        if current.get("state") in {"cancelled", "interrupted", "error"}:
            st.warning(current.get("message", "Job unterbrochen."))
            if prepared_file.is_file():
                if st.button("Audio fortsetzen", key=f"resume-audio-{current_job_id}", type="primary"):
                    if not jobs.start_audio(current_job_id, settings):
                        st.warning("Ein anderer Hörbuchjob läuft gerade. Bitte warten.")
                    st.rerun()
            elif st.button("OCR/Textaufbereitung fortsetzen", key=f"resume-text-{current_job_id}", type="primary"):
                if not jobs.start_preparation(current_job_id, settings):
                    st.warning("Ein anderer Hörbuchjob läuft gerade. Bitte warten.")
                st.rerun()
            return

        if current.get("state") == "review":
            if not prepared:
                st.rerun()
            st.caption("Textprüfung abgeschlossen. Kontrolliere die Vorschau und starte danach die Audiogenerierung.")

    show_job_progress(job_id)

st.caption("Fortschritt wird pro Seite und Sprachabschnitt gespeichert. Bei Abbruch kannst du mit derselben PDF und denselben Einstellungen fortsetzen.")
st.divider()
st.caption("PDF und Audio bleiben lokal auf diesem Mac. Der erste Modellabruf benötigt Internet. OCR nutzt Tesseract.")
