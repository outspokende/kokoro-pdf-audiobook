"""Generate the short English previews embedded in the voice selector."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.tts import synthesize


VOICES = ("af_heart", "af_bella", "am_michael", "am_adam", "bf_emma", "bm_george")
SAMPLE_TEXT = "A story can take you anywhere. This is a short sample of this audiobook voice."
DESTINATION = ROOT / "app" / "assets" / "voice_samples"


def main() -> None:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for voice in VOICES:
        audio, _ = synthesize([(SAMPLE_TEXT, True)], voice, "mp3")
        path = DESTINATION / f"{voice}.mp3"
        path.write_bytes(audio)
        print(f"Wrote {path} ({len(audio):,} bytes)")


if __name__ == "__main__":
    main()
