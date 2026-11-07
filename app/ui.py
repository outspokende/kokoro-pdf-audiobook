from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from app.preprocess import prepare_pdf
from app.tts import synthesize

st.set_page_config(page_title="Kokoro PDF to Audiobook", page_icon="📚", layout="centered")
st.title("PDF → Hörbuch")
st.caption("Lokal auf deinem Mac. PDF-Text wird bereinigt und mit einer Kokoro-Stimme vorgelesen.")
st.info("Voraussetzung: Apple-Silicon-Mac. Die erste Generierung lädt das Sprachmodell. Nur PDFs verarbeiten, für die du die nötigen Rechte hast.")

upload = st.file_uploader("PDF auswählen", type=["pdf"], max_upload_size=100)
skip_front = st.checkbox("Vorspann überspringen, wenn ein Kapitelanfang erkannt wird", value=False,
                         help="Heuristik; bitte die Textvorschau kontrollieren. Ein PDF-Inhaltsverzeichnis bleibt erhalten.")
voice = st.selectbox("Kokoro-Stimme", ["af_heart", "af_bella", "am_michael", "am_adam", "bf_emma", "bm_george"])
fmt = st.radio("Downloadformat", ["mp3", "wav"], horizontal=True)

if upload is not None:
    st.caption(f"{upload.name} · {upload.size / 1024 / 1024:.1f} MB")
    if st.button("Text aus PDF aufbereiten", type="primary"):
        with st.spinner("PDF wird lokal gelesen und für TTS vorbereitet …"):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(upload.getvalue())
                pdf_path = f.name
            try:
                st.session_state.prepared = prepare_pdf(pdf_path, skip_front)
                st.session_state.upload_name = Path(upload.name).stem
            except Exception as exc:
                st.error(str(exc))
                st.session_state.pop("prepared", None)
            finally:
                Path(pdf_path).unlink(missing_ok=True)

prepared = st.session_state.get("prepared")
if prepared:
    st.success(f"Text vorbereitet · {prepared['page_count']} PDF-Seiten · {len(prepared['chunks'])} Sprachabschnitte")
    st.text_area("Bitte kurz prüfen, ob der extrahierte Text passt", prepared["text"], height=260)
    if st.button("Hörbuch erstellen"):
        progress = st.progress(0, text="Kokoro wird geladen …")
        try:
            data, filename = synthesize(prepared["chunks"], voice, fmt,
                                        lambda x: progress.progress(x, text=f"Erzeuge Audio … {int(x * 100)}%"))
            st.session_state.audio = (data, filename)
            st.success("Fertig.")
        except Exception as exc:
            st.error(f"Audio konnte nicht erstellt werden: {exc}")

if st.session_state.get("audio"):
    data, filename = st.session_state.audio
    st.download_button("Hörbuch herunterladen", data, file_name=(st.session_state.get("upload_name", "audiobook") + "." + fmt),
                       mime="audio/mpeg" if filename.endswith("mp3") else "audio/wav", type="primary")

st.divider()
st.caption("Dein PDF und das Audio verlassen diesen Mac während der Verarbeitung nicht. Der erste Modellabruf benötigt Internet.")
