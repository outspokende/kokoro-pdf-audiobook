"""Sequential Kokoro synthesis and local WAV/MP3 assembly."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

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
