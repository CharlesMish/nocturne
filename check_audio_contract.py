"""
Check Nocturne's canonical ambient mixer files.

This is a local filesystem check; it does not start the FastAPI app. Use it
after copying audio into ./sounds/ to see which mixer channels are ready.
"""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parent
SOUNDS_DIR = ROOT / "sounds"

EXPECTED = [
    ("calming-rain", "Calming Rain", "calming_rain.mp3"),
    ("gentle-rain", "Gentle Rain", "gentle_rain.mp3"),
    ("heavy-rain", "Heavy Rain", "heavy_rain.mp3"),
    ("heavy-storm", "Heavy Storm", "heavy_storm.mp3"),
    ("thunder", "Thunder", "thunder.mp3"),
    ("fireplace", "Fireplace", "fireplace.mp3"),
    ("brown-noise", "Brown Noise", "brown-noise.wav"),
    ("pink-noise", "Pink Noise", "pinknoise.wav"),
    ("white-noise", "White Noise", "white-noise.wav"),
]


def main() -> int:
    missing = []
    print("Nocturne ambient audio contract")
    print(f"Directory: {SOUNDS_DIR}")
    for channel_id, label, filename in EXPECTED:
        path = SOUNDS_DIR / filename
        if path.is_file():
            size_mb = path.stat().st_size / 1_048_576
            print(f"OK      {channel_id:13} {label:13} sounds/{filename} ({size_mb:.1f} MB)")
        else:
            missing.append(filename)
            print(f"MISSING {channel_id:13} {label:13} sounds/{filename}")

    if missing:
        print()
        print("Missing files:")
        for filename in missing:
            print(f"  - sounds/{filename}")
        print()
        print("The app will still boot; missing channels are disabled in the UI.")
        return 0

    print()
    print("All ambient mixer files are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
