"""Sequential Kokoro synthesis and local WAV/MP3 assembly."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import os

import numpy as np
import soundfile as sf

MODEL_REPO = "mlx-community/Kokoro-82M-bf16"
SAMPLE_RATE = 24000


def synthesize(chunks: list[tuple[str, bool]], voice: str, output_format: str,
              progress=None) -> tuple[bytes, str]:
    from mlx_audio.tts.utils import load_model
    import imageio_ffmpeg

    model = load_model(MODEL_REPO)
    sr = int(getattr(model, "sample_rate", SAMPLE_RATE))
    language = "b" if voice.startswith(("bf_", "bm_")) else "a"
    with tempfile.TemporaryDirectory(prefix="kokoro-audiobook-") as temp:
        root = Path(temp)
        wav_path = root / "audiobook.wav"
        with sf.SoundFile(wav_path, mode="w", samplerate=sr, channels=1, subtype="PCM_16") as out:
            for i, (text, paragraph_end) in enumerate(chunks):
                blocks = []
                for result in model.generate(text=text, voice=voice, speed=1.0, lang_code=language):
                    audio = getattr(result, "audio", result)
                    if hasattr(audio, "tolist"):
                        audio = np.asarray(audio.tolist(), dtype=np.float32)
                    else:
                        audio = np.asarray(audio, dtype=np.float32)
                    blocks.append(audio.reshape(-1))
                    sr = int(getattr(result, "sample_rate", sr) or sr)
                if not blocks:
                    raise RuntimeError(f"Kokoro returned no audio for chunk {i + 1}.")
                out.write(np.concatenate(blocks))
                if i < len(chunks) - 1:
                    out.write(np.zeros(int(sr * (0.32 if paragraph_end else 0.16)), dtype=np.float32))
                if progress:
                    progress((i + 1) / len(chunks))
        if output_format == "wav":
            return wav_path.read_bytes(), "audiobook.wav"
        mp3_path = root / "audiobook.mp3"
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        result = subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                                 "-i", str(wav_path), "-codec:a", "libmp3lame",
                                 "-q:a", "3", str(mp3_path)], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(f"MP3 conversion failed: {result.stderr[-1000:]}")
        return mp3_path.read_bytes(), "audiobook.mp3"


def synthesize_resumable(chunks: list[tuple[str, bool]], voice: str, output_format: str,
                         chunk_dir: str | Path, output_path: str | Path,
                         progress=None, cancelled=None, cover_path: str | Path | None = None,
                         title: str | None = None) -> Path:
    """Synthesize one checkpointed WAV per text chunk, then assemble the result."""
    import imageio_ffmpeg
    from mlx_audio.tts.utils import load_model

    chunk_dir = Path(chunk_dir)
    output_path = Path(output_path)
    chunk_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model = load_model(MODEL_REPO)
    sample_rate = int(getattr(model, "sample_rate", SAMPLE_RATE))
    language = "b" if voice.startswith(("bf_", "bm_")) else "a"
    total = len(chunks)

    for index, (text, _paragraph_end) in enumerate(chunks):
        if cancelled and cancelled():
            raise InterruptedError("Audiogenerierung angehalten.")
        chunk_path = chunk_dir / f"{index:06d}.wav"
        if chunk_path.is_file():
            try:
                if sf.info(chunk_path).frames <= 0:
                    chunk_path.unlink()
            except Exception:
                chunk_path.unlink(missing_ok=True)
        if not chunk_path.is_file():
            blocks = []
            for result in model.generate(text=text, voice=voice, speed=1.0, lang_code=language):
                audio = getattr(result, "audio", result)
                if hasattr(audio, "tolist"):
                    audio = np.asarray(audio.tolist(), dtype=np.float32)
                else:
                    audio = np.asarray(audio, dtype=np.float32)
                blocks.append(audio.reshape(-1))
                sample_rate = int(getattr(result, "sample_rate", sample_rate) or sample_rate)
            if not blocks:
                raise RuntimeError(f"Kokoro returned no audio for chunk {index + 1}.")
            temporary_chunk = chunk_dir / f"{index:06d}.partial.wav"
            sf.write(temporary_chunk, np.concatenate(blocks), sample_rate, subtype="PCM_16")
            os.replace(temporary_chunk, chunk_path)
        if progress:
            progress(index + 1, total, "tts", f"Kokoro: Abschnitt {index + 1} von {total}")

    wav_partial = output_path.with_name(output_path.stem + ".partial.wav")
    with sf.SoundFile(wav_partial, mode="w", samplerate=sample_rate, channels=1,
                      subtype="PCM_16", format="WAV") as combined:
        for index, (_text, paragraph_end) in enumerate(chunks):
            if cancelled and cancelled():
                wav_partial.unlink(missing_ok=True)
                raise InterruptedError("Zusammenfügen angehalten. Sprachabschnitte sind gespeichert.")
            chunk_path = chunk_dir / f"{index:06d}.wav"
            with sf.SoundFile(chunk_path, mode="r") as part:
                if part.samplerate != sample_rate or part.channels != 1:
                    raise RuntimeError(f"Audioformat stimmt bei Abschnitt {index + 1} nicht überein.")
                for audio_block in part.blocks(blocksize=65536, dtype="float32"):
                    combined.write(audio_block)
            if index < total - 1:
                gap = 0.32 if paragraph_end else 0.16
                combined.write(np.zeros(int(sample_rate * gap), dtype=np.float32))
            if progress:
                progress(index + 1, total, "merge", f"Füge Audio zusammen: {index + 1} von {total}")
    if output_format == "wav":
        os.replace(wav_partial, output_path)
        return output_path

    if progress:
        progress(total, total, "export", "MP3 wird kodiert")
    mp3_partial = output_path.with_name(output_path.stem + ".partial.mp3")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                             "-i", str(wav_partial), "-codec:a", "libmp3lame",
                             "-q:a", "3", str(mp3_partial)], capture_output=True, text=True)
    wav_partial.unlink(missing_ok=True)
    if result.returncode:
        mp3_partial.unlink(missing_ok=True)
        raise RuntimeError(f"MP3 conversion failed: {result.stderr[-1000:]}")
    if cover_path and Path(cover_path).is_file():
        tagged_partial = output_path.with_name(output_path.stem + ".cover.partial.mp3")
        tag_result = subprocess.run([
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(mp3_partial), "-i", str(cover_path),
            "-map", "0:a:0", "-map", "1:v:0", "-c:a", "copy", "-c:v", "copy",
            "-id3v2_version", "3", "-metadata", f"title={title or output_path.stem}",
            "-metadata", f"album={title or output_path.stem}",
            "-metadata:s:v:0", "title=Album cover",
            "-metadata:s:v:0", "comment=Cover (front)",
            "-disposition:v:0", "attached_pic", str(tagged_partial),
        ], capture_output=True, text=True)
        if tag_result.returncode:
            tagged_partial.unlink(missing_ok=True)
            mp3_partial.unlink(missing_ok=True)
            raise RuntimeError(f"MP3-Cover konnte nicht eingebettet werden: {tag_result.stderr[-1000:]}")
        mp3_partial.unlink(missing_ok=True)
        mp3_partial = tagged_partial
    os.replace(mp3_partial, output_path)
    return output_path
