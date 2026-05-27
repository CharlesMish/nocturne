"""
Generate placeholder ambient loops for Nocturne's nine hardcoded mixer slots.

Run from the project root after installation:
    python make_test_noise.py

The active mixer expects these exact filenames:
    sounds/brown-noise.wav
    sounds/calming_rain.mp3
    sounds/fireplace.mp3
    sounds/gentle_rain.mp3
    sounds/heavy_rain.mp3
    sounds/heavy_storm.mp3
    sounds/pinknoise.wav
    sounds/thunder.mp3
    sounds/white-noise.wav

WAV files are written directly. MP3 files are created through ffmpeg when it is
available on PATH. If ffmpeg is missing, this script skips the MP3 placeholders
and prints a message; copy your real MP3 files into sounds/ instead.

For a quick smoke test, shorten generation with:
    NOCTURNE_TEST_SOUND_SECONDS=2 python make_test_noise.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44_100
DURATION_SECONDS = int(os.getenv("NOCTURNE_TEST_SOUND_SECONDS", "60"))
PEAK = 0.28  # leave headroom so layered sounds do not clip too easily


def _normalise(audio: np.ndarray, peak: float = PEAK) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float64)
    audio = audio - np.mean(audio)
    max_abs = float(np.max(np.abs(audio))) if audio.size else 0.0
    if max_abs > 0:
        audio = audio / max_abs * peak
    return audio


def white_noise(n: int) -> np.ndarray:
    return _normalise(np.random.randn(n), 0.22)


def pink_noise(n: int) -> np.ndarray:
    white = np.random.randn(n)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, 1 / SAMPLE_RATE)
    freqs[0] = 1.0
    pink = np.fft.irfft(fft / np.sqrt(freqs), n)
    return _normalise(pink, 0.24)


def brown_noise(n: int) -> np.ndarray:
    steps = np.random.randn(n) * 0.02
    return _normalise(np.cumsum(steps), 0.26)


def soft_rain(n: int) -> np.ndarray:
    return _normalise(0.72 * pink_noise(n) + 0.28 * white_noise(n), 0.20)


def heavy_rain(n: int) -> np.ndarray:
    return _normalise(0.60 * pink_noise(n) + 0.40 * brown_noise(n), 0.25)


def thunder_layer(n: int, strikes: int = 5) -> np.ndarray:
    audio = brown_noise(n) * 0.35
    for _ in range(strikes):
        start = np.random.randint(0, max(1, n - SAMPLE_RATE))
        length = np.random.randint(SAMPLE_RATE // 5, SAMPLE_RATE)
        end = min(n, start + length)
        env = np.exp(-np.linspace(0, 5, end - start))
        audio[start:end] += np.random.randn(end - start) * env * 0.9
    return _normalise(audio, 0.30)


def fireplace(n: int) -> np.ndarray:
    audio = brown_noise(n) * 0.20
    crackles = max(10, DURATION_SECONDS * 8)
    for _ in range(crackles):
        start = np.random.randint(0, max(1, n - SAMPLE_RATE // 20))
        length = np.random.randint(120, SAMPLE_RATE // 25)
        end = min(n, start + length)
        env = np.exp(-np.linspace(0, 7, end - start))
        audio[start:end] += np.random.randn(end - start) * env * 1.2
    return _normalise(audio, 0.22)


def save_wav(path: Path, audio: np.ndarray) -> None:
    audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(audio_int16.tobytes())


def save_mp3(path: Path, audio: np.ndarray) -> bool:
    """Encode an MP3 with ffmpeg. Return False when ffmpeg is unavailable."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / f"{path.stem}.wav"
        save_wav(wav_path, audio)
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(wav_path),
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "3",
                str(path),
            ],
            check=True,
        )
    return True


def save_audio(path: Path, audio: np.ndarray) -> bool:
    if path.suffix.lower() == ".wav":
        save_wav(path, audio)
        return True
    if path.suffix.lower() == ".mp3":
        return save_mp3(path, audio)
    raise ValueError(f"Unsupported placeholder extension: {path.suffix}")


def main() -> None:
    out_dir = Path(__file__).parent / "sounds"
    out_dir.mkdir(exist_ok=True)
    n = SAMPLE_RATE * DURATION_SECONDS

    generators = [
        ("brown-noise.wav", brown_noise),
        ("calming_rain.mp3", soft_rain),
        ("fireplace.mp3", fireplace),
        ("gentle_rain.mp3", soft_rain),
        ("heavy_rain.mp3", heavy_rain),
        ("heavy_storm.mp3", lambda samples: _normalise(heavy_rain(samples) + 0.45 * thunder_layer(samples, 7), 0.30)),
        ("pinknoise.wav", pink_noise),
        ("thunder.mp3", lambda samples: thunder_layer(samples, 4)),
        ("white-noise.wav", white_noise),
    ]

    for filename, generator in generators:
        path = out_dir / filename
        print(f"Generating {filename}…", end=" ", flush=True)
        wrote = save_audio(path, generator(n))
        if wrote:
            size_mb = path.stat().st_size / 1_048_576
            print(f"wrote {size_mb:.1f} MB")
        else:
            print("skipped; install ffmpeg or copy in your real MP3 file")


if __name__ == "__main__":
    main()
