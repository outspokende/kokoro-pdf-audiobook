"""Persistent, resumable local pipeline jobs for the Streamlit interface."""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from pathlib import Path

import pymupdf as fitz

from app.preprocess import prepare_pdf
from app.tts import synthesize_resumable

OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "output" / "jobs"
# Bump when preprocessing results must be regenerated after an algorithm fix.
PREPROCESS_REVISION = 3
_threads: dict[str, threading.Thread] = {}
_thread_lock = threading.Lock()


def job_id_for(pdf_bytes: bytes, settings: dict) -> str:
    digest = hashlib.sha256()
    digest.update(pdf_bytes)
    digest.update(json.dumps(settings, sort_keys=True).encode("utf-8"))
    digest.update(f"preprocess-revision:{PREPROCESS_REVISION}".encode("ascii"))
    return digest.hexdigest()[:20]


def job_dir(job_id: str) -> Path:
    return OUTPUT_ROOT / job_id


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


def _read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _status_path(folder: Path) -> Path:
    return folder / "status.json"


def safe_title_stem(title: str) -> str:
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", title).strip(" .")
    return (stem[:120] or "Hoerbuch")


def _update(folder: Path, **changes) -> dict:
    path = _status_path(folder)
    state = _read_json(path, {})
    state.update(changes)
    _write_json(path, state)
    return state


def ensure_source(folder: Path, pdf_bytes: bytes, source_name: str | None = None) -> Path:
    source = folder / "source.pdf"
    if not source.exists():
        folder.mkdir(parents=True, exist_ok=True)
        temporary = source.with_suffix(".pdf.tmp")
        temporary.write_bytes(pdf_bytes)
        os.replace(temporary, source)
    if source_name:
        clean_name = Path(source_name).name
        _write_json(folder / "metadata.json", {
            "source_name": clean_name,
            "title": Path(clean_name).stem,
            "cover_page": 1,
        })
    return source


def ensure_cover(source_pdf: str | Path, cover_path: str | Path) -> Path:
    """Render the PDF's first page as a modest JPEG cover image."""
    source_pdf = Path(source_pdf)
    cover_path = Path(cover_path)
    if cover_path.is_file():
        return cover_path
    cover_path.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(source_pdf) as document:
        if not document.page_count:
            raise ValueError("Das PDF enthält keine Seiten für ein Cover.")
        page = document[0]
        largest_edge = max(page.rect.width, page.rect.height, 1)
        scale = min(2.0, 1200 / largest_edge)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        pixmap.save(str(cover_path), jpg_quality=88)
    return cover_path


def status_for(job_id: str) -> dict:
    folder = job_dir(job_id)
    status = _read_json(_status_path(folder), {})
    if status.get("state") == "running" and not thread_running(job_id):
        status = _update(folder, state="interrupted", message="Unterbrochen – gespeicherte Schritte können fortgesetzt werden.")
    return status


def most_recent_completed_job() -> dict | None:
    """Return the newest completed job whose output file still exists."""
    candidates = []
    for status_path in OUTPUT_ROOT.glob("*/status.json"):
        status = _read_json(status_path, {})
        output_name = status.get("output")
        if status.get("state") != "complete" or not isinstance(output_name, str):
            continue
        if Path(output_name).name != output_name:
            continue
        output_path = status_path.parent / output_name
        if output_path.is_file():
            candidates.append((status_path.stat().st_mtime, {
                "job_id": status_path.parent.name,
                "status": status,
                "output_path": output_path,
                "modified_at": status_path.stat().st_mtime,
            }))
    if not candidates:
        return None
    recent = max(candidates, key=lambda item: item[0])[1]
    folder = recent["output_path"].parent
    metadata = _read_json(folder / "metadata.json", {})
    title = metadata.get("title")
    if not title:
        try:
            with fitz.open(folder / "source.pdf") as document:
                title = (document.metadata or {}).get("title")
        except (OSError, RuntimeError):
            title = None
    recent["title"] = title or recent["output_path"].stem
    recent["source_name"] = metadata.get("source_name")
    recent["cover_path"] = ensure_cover(folder / "source.pdf", folder / "cover.jpg")
    return recent


def thread_running(job_id: str) -> bool:
    with _thread_lock:
        thread = _threads.get(job_id)
        return bool(thread and thread.is_alive())


def request_cancel(job_id: str) -> None:
    folder = job_dir(job_id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "cancel.request").write_text("stop", encoding="utf-8")
    _update(folder, message="Abbruch angefordert – aktueller Arbeitsschritt wird noch gespeichert …")


def _is_cancelled(folder: Path) -> bool:
    return (folder / "cancel.request").exists()


def _start(job_id: str, target, *args) -> bool:
    with _thread_lock:
        existing = _threads.get(job_id)
        if existing and existing.is_alive():
            return False
        if any(t.is_alive() for t in _threads.values()):
            return False
        folder = job_dir(job_id)
        (folder / "cancel.request").unlink(missing_ok=True)
        thread = threading.Thread(target=target, args=(job_id, *args), daemon=True,
                                  name=f"audiobook-{job_id}")
        _threads[job_id] = thread
        thread.start()
        return True


def start_preparation(job_id: str, settings: dict) -> bool:
    return _start(job_id, _prepare_worker, settings)


def start_audio(job_id: str, settings: dict) -> bool:
    return _start(job_id, _audio_worker, settings)


def _prepare_worker(job_id: str, settings: dict) -> None:
    folder = job_dir(job_id)
    source = folder / "source.pdf"
    try:
        _update(folder, state="running", stage="extract", percent=0, stage_percent=0,
                message="PDF wird analysiert …", completed_pages=0)

        def report(stage, done, total, message):
            if _is_cancelled(folder):
                raise InterruptedError("Aufbereitung angehalten.")
            percent = int(done / max(total, 1) * 8)
            _update(folder, stage=stage, percent=percent,
                    stage_percent=int(done / max(total, 1) * 100), completed_pages=done,
                    total_pages=total, message=message)

        result = prepare_pdf(
            str(source), settings["skip_front_matter"], settings["ocr_language"],
            progress=report, checkpoint_dir=folder / "preprocess", cancelled=lambda: _is_cancelled(folder),
        )
        if _is_cancelled(folder):
            raise InterruptedError("Aufbereitung angehalten.")
        _write_json(folder / "prepared.json", {
            "chunks": result["chunks"], "chapters": result["chapters"],
            "page_count": result["page_count"], "text": result["text"],
        })
        _update(folder, state="review", stage="review", percent=10,
                message="Text ist aufbereitet. Bitte Vorschau prüfen.",
                total_chunks=len(result["chunks"]), completed_chunks=0)
    except InterruptedError:
        _update(folder, state="cancelled", message="Aufbereitung angehalten. Beim Fortsetzen werden fertige Seiten wiederverwendet.")
    except Exception as exc:
        _update(folder, state="error", message=str(exc))


def _audio_worker(job_id: str, settings: dict) -> None:
    folder = job_dir(job_id)
    try:
        prepared = _read_json(folder / "prepared.json")
        if not prepared:
            raise RuntimeError("Der vorbereitete Text fehlt. Bitte die PDF-Aufbereitung zuerst starten.")
        chunks = [(str(text), bool(paragraph_end)) for text, paragraph_end in prepared["chunks"]]
        _update(folder, state="running", stage="load_model", percent=10, stage_percent=0,
                message="Kokoro wird geladen …", total_chunks=len(chunks),
                completed_chunks=0)

        def report(done, total, stage, message):
            ratio = done / max(total, 1)
            percent = (10 + int(ratio * 80) if stage == "tts" else
                       90 + int(ratio * 8) if stage == "merge" else 99)
            _update(folder, stage=stage, percent=percent, stage_percent=int(ratio * 100),
                    completed_chunks=done, total_chunks=total, message=message)

        metadata = _read_json(folder / "metadata.json", {})
        title = metadata.get("title") or "Hoerbuch"
        filename = f"{safe_title_stem(title)}.{settings['output_format']}"
        output = folder / filename
        synthesize_resumable(
            chunks, settings["voice"], settings["output_format"], folder / "audio_chunks",
            output, progress=report, cancelled=lambda: _is_cancelled(folder),
            cover_path=folder / "cover.jpg", title=title,
        )
        if _is_cancelled(folder):
            raise InterruptedError("Audiogenerierung angehalten.")
        _update(folder, state="complete", stage="complete", percent=100,
                message="Hörbuch ist fertig.", output=filename)
    except InterruptedError:
        status = _read_json(_status_path(folder), {})
        _update(folder, state="cancelled",
                message=f"Angehalten bei {status.get('completed_chunks', 0)} von {status.get('total_chunks', 0)} Abschnitten. Fortsetzen ist möglich.")
    except Exception as exc:
        _update(folder, state="error", message=str(exc))
