from __future__ import annotations

import html
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import streamlit as st

from app import jobs

st.set_page_config(page_title="Kokoro PDF to Audiobook", page_icon="📚", layout="centered")
SAMPLE_PDF = (
    Path(__file__).resolve().parent.parent
    / "samples" / "war-of-the-worlds" / "warofworlds1898well.pdf"
)


def render_recent_download() -> str | None:
    recent = jobs.most_recent_completed_job()
    if not recent:
        return None
    output_path = recent["output_path"]
    job_id = recent["job_id"]
    title = recent["title"]
    cover_path = recent["cover_path"]
    suffix = output_path.suffix.lower() or ".mp3"
    mime = "audio/wav" if suffix == ".wav" else "audio/mpeg"
    finished = datetime.fromtimestamp(recent["modified_at"]).strftime("%d.%m.%Y · %H:%M")
    size_mib = output_path.stat().st_size / (1024 * 1024)
    with st.container(border=True):
        st.markdown('<p class="section-label">LETZTES HÖRBUCH</p>', unsafe_allow_html=True)
        cover_column, details_column = st.columns([.8, 2.2], vertical_alignment="center")
        with cover_column:
            st.image(str(cover_path), caption=title, width=140)
        with details_column:
            st.subheader(title)
            st.caption(f"Fertig · {finished} · {size_mib:.1f} MiB")
            source_name = recent.get("source_name")
            output_stem = jobs.safe_title_stem(Path(source_name).stem if source_name else title)
            st.download_button(
                "Fertiges Hörbuch herunterladen",
                data=lambda path=output_path: path.read_bytes(),
                file_name=f"{output_stem}{suffix}", mime=mime,
                key=f"recent-download-{job_id}", type="primary", on_click="ignore",
            )
            if suffix == ".wav":
                st.download_button(
                    "Coverbild herunterladen",
                    data=lambda path=cover_path: path.read_bytes(),
                    file_name=f"{output_stem}-cover.jpg", mime="image/jpeg",
                    key=f"recent-cover-{job_id}", on_click="ignore",
                )
            else:
                st.caption("Das Cover ist in der MP3 eingebettet.")
    return job_id


st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp {
  background:
    radial-gradient(ellipse at 85% 0%, rgba(111, 92, 255, .18), transparent 34%),
    radial-gradient(ellipse at 0% 20%, rgba(71, 198, 255, .09), transparent 32%),
    #0b0f18;
}
.block-container { max-width: 1050px; padding-top: 2.25rem; padding-bottom: 3.5rem; }
[data-testid="stHeader"] { background: transparent; }
.hero {
  position: relative; overflow: hidden; padding: 2.1rem 2.25rem 2rem;
  margin-bottom: 1.5rem; border: 1px solid rgba(171, 190, 255, .2);
  border-radius: 26px;
  background: linear-gradient(118deg, rgba(27, 37, 64, .96), rgba(22, 27, 43, .88) 58%, rgba(26, 45, 58, .94));
  box-shadow: 0 24px 80px rgba(0, 0, 0, .28);
}
.hero:after {
  content: ""; position: absolute; width: 260px; height: 260px; border-radius: 50%;
  right: -92px; top: -130px; border: 1px solid rgba(169, 246, 84, .25);
  box-shadow: 0 0 0 28px rgba(169, 246, 84, .035), 0 0 0 58px rgba(169, 246, 84, .025);
}
.hero-kicker { color: #a9f654; font-size: .76rem; font-weight: 750; letter-spacing: .14em; text-transform: uppercase; }
.hero h1 { margin: .65rem 0 .5rem; color: #f6f8ff; font-size: clamp(2.05rem, 5vw, 3.5rem); line-height: 1.05; letter-spacing: -.045em; text-wrap: balance; }
.hero-copy { max-width: 650px; margin: 0; color: #c5cde0; font-size: 1.06rem; line-height: 1.6; }
.hero-pills { display: flex; flex-wrap: wrap; gap: .55rem; margin-top: 1.2rem; }
.hero-pill { padding: .38rem .72rem; border: 1px solid rgba(213, 224, 255, .15); border-radius: 999px; background: rgba(255,255,255,.055); color: #e5eafb; font-size: .78rem; }
.section-label { color: #a9f654; font-size: .75rem; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; margin: .4rem 0 .35rem; }
.timeline { list-style: none; padding: .25rem 0 .1rem; margin: 0; }
.timeline-step { position: relative; display: grid; grid-template-columns: 42px minmax(0, 1fr); gap: .9rem; min-height: 82px; }
.timeline-step:not(:last-child):before { content: ""; position: absolute; left: 17px; top: 39px; bottom: -1px; width: 2px; background: #30394d; }
.timeline-dot { position: relative; z-index: 1; display: grid; place-items: center; width: 36px; height: 36px; border-radius: 50%; border: 0; background: conic-gradient(var(--ring-color, #3a4356) var(--ring-progress, 0%), #30394d 0); color: #98a3ba; font-weight: 700; font-size: .83rem; }
.timeline-dot:before { content: ""; position: absolute; inset: 3px; border-radius: 50%; background: #151b29; }
.timeline-dot > span { position: relative; z-index: 1; }
.timeline-copy { padding: .13rem 0 .8rem; min-width: 0; }
.timeline-title-row { display: flex; flex-wrap: wrap; align-items: center; gap: .6rem; }
.timeline-title { color: #dce3f1; font-size: .98rem; font-weight: 680; }
.timeline-state { color: #7e8aa4; font-size: .67rem; font-weight: 750; letter-spacing: .09em; text-transform: uppercase; }
.timeline-desc { margin: .22rem 0 0; color: #98a4ba; font-size: .85rem; line-height: 1.45; }
.timeline-step.is-done .timeline-dot { color: #111a13; }
.timeline-step.is-done .timeline-dot:before { background: #a9f654; }
.timeline-step.is-done:not(:last-child):before { background: #719e43; }
.timeline-step.is-current .timeline-dot { color: #0b1221; animation: timeline-pulse 1.8s ease-out infinite; }
.timeline-step.is-current .timeline-dot:before { background: #74d9ff; }
@keyframes timeline-pulse {
  0% { box-shadow: 0 0 0 0 rgba(116, 217, 255, .4); }
  70% { box-shadow: 0 0 0 10px rgba(116, 217, 255, .08); }
  100% { box-shadow: 0 0 0 14px rgba(116, 217, 255, 0); }
}
.timeline-step.is-current .timeline-title { color: #f5f8ff; }
.timeline-step.is-current .timeline-state { color: #74d9ff; }
.timeline-step.is-paused .timeline-dot { color: #20170b; }
.timeline-step.is-paused .timeline-dot:before { background: #ffca70; }
.timeline-step.is-paused .timeline-state { color: #ffca70; }
.timeline-step.is-error .timeline-dot { color: #2b1115; }
.timeline-step.is-error .timeline-dot:before { background: #ff7d86; }
.timeline-step.is-error .timeline-state { color: #ff9ba2; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color: rgba(163, 180, 220, .17); border-radius: 20px; background: rgba(18, 24, 37, .55); }
[data-testid="stFileUploader"] section { border: 1px dashed rgba(150, 171, 210, .45); border-radius: 16px; background: rgba(255,255,255,.025); }
[data-testid="stAudio"] { margin: .15rem 0 1rem; }
div[data-testid="stProgress"] > div > div > div > div { background: linear-gradient(90deg, #73d9ff, #a9f654); }
button[kind="primary"] { border: 0; border-radius: 12px; color: #111812; font-weight: 750; background: linear-gradient(100deg, #a9f654, #c8ff80); box-shadow: 0 7px 22px rgba(169, 246, 84, .16); transition: filter .16s ease, transform .16s ease; }
button[kind="primary"]:hover { filter: brightness(1.06); transform: translateY(-1px); }
.stApp :is(button, a, input, select, textarea):focus-visible { outline: 3px solid #74d9ff; outline-offset: 3px; }
h2, h3 { text-wrap: balance; }
@media (max-width: 640px) { .block-container { padding: 1.2rem 1rem 2.5rem; } .hero { padding: 1.5rem 1.25rem; border-radius: 20px; } .timeline-step { min-height: 88px; } }
@media (prefers-reduced-motion: reduce) {
  button[kind="primary"] { transition: none; }
  .timeline-step.is-current .timeline-dot { animation: none; }
}
</style>
<div class="hero">
  <div class="hero-kicker">Local audiobook studio</div>
  <h1>Aus PDFs werden Hörbücher.</h1>
  <p class="hero-copy">Text aufbereiten, eine Stimme wählen und die Entstehung live verfolgen. Die Verarbeitung läuft lokal auf deinem Mac.</p>
  <div class="hero-pills"><span class="hero-pill">✦ Kokoro TTS</span><span class="hero-pill">⌂ Lokal verarbeitet</span><span class="hero-pill">↻ Unterbrechbar & fortsetzbar</span></div>
</div>
""", unsafe_allow_html=True)

recent_download_placeholder = st.empty()

with st.container(border=True):
    input_column, settings_column = st.columns([1.08, .92], gap="large")
    with input_column:
        st.markdown('<p class="section-label">01 / Ausgangsmaterial</p>', unsafe_allow_html=True)
        st.subheader("PDF auswählen")
        use_sample = st.checkbox(
            "Testbuch wählen: The War of the Worlds",
            value=False,
            help="H. G. Wells, Ausgabe von 1898. Das 326-seitige PDF liegt im Repository unter samples/war-of-the-worlds/. Die vollständige Vertonung kann dauern.",
        )
        st.caption("Gemeinfreies Testbuch · H. G. Wells · 326 Seiten · [Quelle und Rechte](https://archive.org/details/warofworlds1898well)")
        upload = st.file_uploader(
            "PDF", type=["pdf"], max_upload_size=100, label_visibility="collapsed",
            disabled=use_sample,
        )
        if use_sample:
            if SAMPLE_PDF.is_file():
                st.info("Testbuch ausgewählt. Klicke unten auf „PDF analysieren und Text aufbereiten“, um zu starten.")
            else:
                st.error("Das Testbuch-PDF fehlt. Lade es aus dem Repository-Ordner samples/war-of-the-worlds/ herunter.")
        skip_front = st.checkbox(
            "Vorspann überspringen, wenn Kapitel erkannt werden", value=True,
            help="Das Inhaltsverzeichnis hilft, die Geschichte zu finden. Bitte die Textvorschau prüfen.",
        )
    with settings_column:
        st.markdown('<p class="section-label">02 / Stimme & Format</p>', unsafe_allow_html=True)
        ocr_language = "eng"
        st.text_input(
            "OCR-Sprache für Scans", value="English", disabled=True,
            help="Die integrierten Kokoro-Stimmen sind englisch; daher ist auch die OCR auf Englisch festgelegt.",
        )
        if not shutil.which("tesseract"):
            st.warning("Für bildbasierte PDFs wird Tesseract benötigt. Auf macOS einmalig im Terminal ausführen: `brew install tesseract tesseract-lang`.")
        else:
            language_output = subprocess.run(["tesseract", "--list-langs"], capture_output=True,
                                            text=True, check=False).stdout.splitlines()[1:]
            installed_languages = {language.strip() for language in language_output if language.strip()}
            missing_languages = set(ocr_language.split("+")) - installed_languages
            if missing_languages:
                st.warning(f"Tesseract-Sprachdaten fehlen: {', '.join(sorted(missing_languages))}. Auf macOS: `brew install tesseract-lang`.")

with settings_column:
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


PIPELINE_STEPS = (
    ("PDF hinzufügen", "Dein Dokument wird lokal auf diesem Mac verarbeitet."),
    ("Text lesen & OCR", "Textlayer prüfen; fehlende Texterkennung seitenweise ergänzen."),
    ("Text aufbereiten", "Seitenmöbel säubern, Kapitel finden und sprechbare Abschnitte bilden."),
    ("Vorschau prüfen", "Erkannten Text prüfen, bevor die Stimme loslegt."),
    ("Stimme erzeugen", "Kokoro vertont die Abschnitte einzeln; fertige Stücke werden gespeichert."),
    ("Hörbuch exportieren", "Abschnitte verbinden und als MP3 oder WAV bereitstellen."),
)


def render_timeline(uploaded: bool, current: dict | None, has_prepared_text: bool) -> None:
    state = (current or {}).get("state")
    stage = (current or {}).get("stage")
    stage_to_step = {
        "extract": 1, "ocr": 1, "clean": 2, "review": 3,
        "load_model": 4, "tts": 4, "merge": 5, "export": 5,
    }
    if not uploaded:
        active_step = 0
    elif state == "complete":
        active_step = len(PIPELINE_STEPS)
    elif state == "review":
        active_step = 3
    elif stage in stage_to_step:
        active_step = stage_to_step[stage]
    else:
        active_step = 3 if has_prepared_text else 1

    rows = []
    for index, (title, description) in enumerate(PIPELINE_STEPS):
        done = state == "complete" or index < active_step
        selected = index == active_step and active_step < len(PIPELINE_STEPS)
        paused = selected and state in {"cancelled", "interrupted"}
        failed = selected and state == "error"
        progress = 100 if done or state == "review" and selected else 0
        if selected and not done and state != "review":
            progress = max(0, min(100, int((current or {}).get("stage_percent", 0))))
        ring_color = "#a9f654" if done else "#ffca70" if paused else "#ff7d86" if failed else "#74d9ff" if selected else "#3a4356"
        classes = "timeline-step"
        classes += " is-done" if done else ""
        classes += " is-current" if selected and not paused and not failed else ""
        classes += " is-paused" if paused else ""
        classes += " is-error" if failed else ""
        marker = "✓" if done else str(index + 1)
        state_label = "Erledigt" if done else "Angehalten" if paused else "Fehler" if failed else "Jetzt" if selected else "Danach"
        current_attr = ' aria-current="step"' if selected else ""
        rows.append(
            f'<li class="{classes}"{current_attr}>'
            f'<span class="timeline-dot" role="progressbar" aria-label="Fortschritt: {html.escape(title)}" '
            f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{progress}" '
            f'style="--ring-progress:{progress}%;--ring-color:{ring_color}"><span>{marker}</span></span>'
            f'<div class="timeline-copy"><div class="timeline-title-row">'
            f'<span class="timeline-title">{html.escape(title)}</span>'
            f'<span class="timeline-state">{state_label}</span></div>'
            f'<p class="timeline-desc">{html.escape(description)}</p></div></li>'
        )
    st.markdown("<ol class='timeline' aria-label='Pipeline-Zeitstrahl'>" + "".join(rows) + "</ol>",
                unsafe_allow_html=True)


def render_pipeline_guide() -> None:
    with st.expander("So läuft die Pipeline ab"):
        st.markdown("""
1. **PDF laden:** Die Datei bleibt während der Verarbeitung auf deinem Mac.
2. **Text erkennen:** Vorhandene Texterkennung wird genutzt. Bildseiten ohne brauchbaren Text gehen lokal durch Tesseract-OCR.
3. **Aufbereiten:** Wiederholte Kopf- und Fußzeilen werden entfernt, Kapitel erkannt und der Text in kurze Sprachabschnitte aufgeteilt.
4. **Vorschau prüfen:** Kontrolliere den Text auf OCR-Fehler, bevor du die Erzeugung startest.
5. **Vertonen:** Kokoro erzeugt Abschnitt für Abschnitt Audio. Jeder fertige Abschnitt wird lokal als Checkpoint gespeichert.
6. **Exportieren:** Die Abschnitte werden verbunden und als MP3 oder WAV zum Download angeboten.

Der Zeitstrahl zeigt die aktuelle Station. Während der Verarbeitung siehst du Gesamtfortschritt und Fortschritt der aktuellen Station. **Anhalten** speichert den letzten fertigen Schritt; zum Fortsetzen lädst du dieselbe PDF mit denselben Einstellungen erneut.
        """)

selected_pdf = use_sample and SAMPLE_PDF.is_file() or upload is not None
if not selected_pdf:
    with recent_download_placeholder.container():
        render_recent_download()
    st.markdown('<p class="section-label">03 / Der Ablauf</p><h3>Eine Pipeline, die du mitverfolgen kannst</h3>', unsafe_allow_html=True)
    render_timeline(False, None, False)
    render_pipeline_guide()
    st.caption("Unterbrochene Jobs lassen sich mit derselben PDF und denselben Einstellungen fortsetzen.")
    st.divider()
    st.caption("PDF und Audio bleiben lokal auf diesem Mac. Für automatische OCR muss Tesseract installiert sein.")
    st.stop()

pdf_bytes = SAMPLE_PDF.read_bytes() if use_sample else upload.getvalue()
source_name = SAMPLE_PDF.name if use_sample else upload.name
settings = {
    "skip_front_matter": skip_front,
    "ocr_language": ocr_language,
    "voice": voice,
    "output_format": output_format,
    "source_name": source_name,
}
job_id = jobs.job_id_for(pdf_bytes, settings)
folder = jobs.job_dir(job_id)
source = jobs.ensure_source(folder, pdf_bytes, source_name)
jobs.ensure_cover(source, folder / "cover.jpg")
prepared_file = folder / "prepared.json"
prepared = jobs._read_json(prepared_file)
status = jobs.status_for(job_id)
recent_download_job_id = None
if status.get("state") == "complete":
    with recent_download_placeholder.container():
        recent_download_job_id = render_recent_download()

st.markdown('<p class="section-label">03 / Live-Pipeline</p><h3>Dein Hörbuch entsteht Schritt für Schritt</h3>', unsafe_allow_html=True)
if not status:
    render_timeline(True, None, bool(prepared))
render_pipeline_guide()

if not prepared and status.get("state") not in {"running", "cancelled", "interrupted", "error"}:
    if st.button("PDF analysieren und Text aufbereiten", type="primary"):
        if not jobs.start_preparation(job_id, settings):
            st.warning("Ein anderer Hörbuchjob läuft gerade. Bitte warten, bis er pausiert oder fertig ist.")
        st.rerun()

if prepared:
    st.success(f"Text vorbereitet · {prepared['page_count']} PDF-Seiten · {len(prepared['chunks'])} Sprachabschnitte")
    st.subheader("Textvorschau – bitte jetzt manuell prüfen")
    st.text_area("Textvorschau – bitte auf OCR-Fehler prüfen", prepared["text"], height=260)

if status:
    running = jobs.thread_running(job_id)

    @st.fragment(run_every=1 if running else None)
    def show_job_progress(current_job_id: str):
        current = jobs.status_for(current_job_id)
        is_running = jobs.thread_running(current_job_id)
        if running and not is_running:
            st.rerun()
        render_timeline(True, current, prepared_file.is_file())
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
            if output.is_file() and current_job_id == recent_download_job_id:
                st.caption("Der Download steht oben unter „Letztes Hörbuch“ bereit.")
            elif output.is_file():
                st.download_button(
                    "Hörbuch herunterladen", data=lambda path=output: path.read_bytes(),
                    file_name=f"{Path(source_name).stem}.{output_format}",
                    mime="audio/mpeg" if output_format == "mp3" else "audio/wav",
                    key=f"download-{current_job_id}", type="primary", on_click="ignore",
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

    show_job_progress(job_id)

if status.get("state") == "review" and prepared and not jobs.thread_running(job_id):
    st.markdown('<p class="section-label">04 / NÄCHSTER SCHRITT</p><h3>Text geprüft? Dann Hörbuch erstellen</h3>', unsafe_allow_html=True)
    st.info("Bitte zuerst die Textvorschau weiter oben manuell auf OCR- und Formatierungsfehler prüfen. Die Schaltfläche hier startet anschließend die Audiogenerierung.")
    if st.button("Hörbuch erstellen", type="primary"):
        if not jobs.start_audio(job_id, settings):
            st.warning("Ein anderer Hörbuchjob läuft gerade. Bitte warten.")
        st.rerun()

st.caption("Fortschritt wird pro Seite und Sprachabschnitt gespeichert. Bei Abbruch kannst du mit derselben PDF und denselben Einstellungen fortsetzen.")
st.divider()
st.caption("PDF und Audio bleiben lokal auf diesem Mac. Der erste Modellabruf benötigt Internet. OCR nutzt Tesseract.")
