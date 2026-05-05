"""
Generates three noise samples (white, pink, brown) into ./sounds/.
Useful for testing the app before you download "real" sounds.

Run once after first install:
    python make_test_noise.py

Each file is a 60-second loop. They sound rough but seamless.
Replace them with proper recordings from freesound.org when you're ready.
"""
import wave
from pathlib import Path

import numpy as np


SAMPLE_RATE = 44_100
DURATION_SECONDS = 60
PEAK = 0.3  # 0.0 = silent, 1.0 = clipping. 0.3 leaves headroom.


def white_noise(n: int) -> np.ndarray:
    """Equal energy at every frequency. Bright, hissy."""
    return np.random.randn(n) * PEAK


def pink_noise(n: int) -> np.ndarray:
    """Energy falls 3 dB per octave. Softer, like distant rain or a fan."""
    white = np.random.randn(n)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, 1 / SAMPLE_RATE)
    freqs[0] = 1  # Avoid divide-by-zero on the DC component.
    fft = fft / np.sqrt(freqs)
    pink = np.fft.irfft(fft, n)
    pink = pink / np.max(np.abs(pink)) * PEAK
    return pink


def brown_noise(n: int) -> np.ndarray:
    """Energy falls 6 dB per octave. Deep, rumbly — closest to ocean or wind."""
    steps = np.random.randn(n) * 0.02
    brown = np.cumsum(steps)
    brown = brown - np.mean(brown)  # Remove DC drift.
    brown = brown / np.max(np.abs(brown)) * PEAK
    return brown


def save_wav(path: Path, audio: np.ndarray) -> None:
    """Write a mono 16-bit PCM WAV — small files, plays everywhere."""
    audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(audio_int16.tobytes())


def main() -> None:
    out_dir = Path(__file__).parent / "sounds"
    out_dir.mkdir(exist_ok=True)

    n_samples = SAMPLE_RATE * DURATION_SECONDS

    generators = [
        ("brown-noise", brown_noise),
        ("pink-noise", pink_noise),
        ("white-noise", white_noise),
    ]

    for name, generator in generators:
        path = out_dir / f"{name}.wav"
        print(f"Generating {name}…", end=" ", flush=True)
        save_wav(path, generator(n_samples))
        size_mb = path.stat().st_size / 1_048_576
        print(f"wrote {path.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
"""