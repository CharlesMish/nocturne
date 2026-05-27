#!/usr/bin/env python3
"""
Generate Nocturne's procedural noise beds.

This creates the three non-third-party mixer files reproducibly:
  sounds/brown-noise.wav
  sounds/pinknoise.wav
  sounds/white-noise.wav

It intentionally does not create the rain/fire/thunder MP3s; those are either
user-provided or downloaded via scripts/fetch_media.py from the user's chosen
source manifest.
"""
from __future__ import annotations

import argparse
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOUNDS_DIR = ROOT / "sounds"
SAMPLE_RATE = 44_100
PEAKS = {
    "brown-noise.wav": 0.26,
    "pinknoise.wav": 0.24,
    "white-noise.wav": 0.22,
}


def _normalise(audio: np.ndarray, peak: float) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float64)
    audio = audio - np.mean(audio)
    max_abs = float(np.max(np.abs(audio))) if audio.size else 0.0
    if max_abs:
        audio = audio / max_abs * peak
    return audio


def white_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    return _normalise(rng.standard_normal(n), PEAKS["white-noise.wav"])


def pink_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    white = rng.standard_normal(n)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, 1 / SAMPLE_RATE)
    freqs[0] = 1.0
    pink = np.fft.irfft(fft / np.sqrt(freqs), n)
    return _normalise(pink, PEAKS["pinknoise.wav"])


def brown_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    steps = rng.standard_normal(n) * 0.02
    return _normalise(np.cumsum(steps), PEAKS["brown-noise.wav"])


def save_wav(path: Path, audio: np.ndarray) -> None:
    audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(audio_int16.tobytes())


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Nocturne procedural noise beds.")
    parser.add_argument("--seconds", type=int, default=300, help="duration per file; default: 300")
    parser.add_argument("--seed", type=int, default=20260525, help="deterministic random seed")
    parser.add_argument("--overwrite", action="store_true", help="replace existing files")
    args = parser.parse_args()

    if args.seconds < 1:
        raise SystemExit("--seconds must be at least 1")

    SOUNDS_DIR.mkdir(exist_ok=True)
    n = SAMPLE_RATE * args.seconds
    rng = np.random.default_rng(args.seed)
    generators = {
        "brown-noise.wav": brown_noise,
        "pinknoise.wav": pink_noise,
        "white-noise.wav": white_noise,
    }

    for filename, generator in generators.items():
        path = SOUNDS_DIR / filename
        if path.exists() and not args.overwrite:
            print(f"Keeping existing {filename} (use --overwrite to replace)")
            continue
        print(f"Generating {filename}…", flush=True)
        save_wav(path, generator(n, rng))
        print(f"  wrote {path.stat().st_size / 1_048_576:.1f} MB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
