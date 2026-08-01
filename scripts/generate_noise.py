#!/usr/bin/env python3
"""
Generate Nocturne's procedural starter ambience pack.

This script creates deterministic local WAV beds so a fresh install has useful
sounds before any CC0/Freesound curation work is done. They are intentionally
simple, sleep-safe placeholders — not replacements for field recordings.

Generated files (original set):
  sounds/soft-rain-noise.wav
  sounds/window-rain-noise.wav
  sounds/heavy-rain-noise.wav
  sounds/distant-storm-noise.wav   (display name: "Soft Pink Rain Noise")
  sounds/soft-wind-noise.wav       (display name: "Soft Air Noise")
  sounds/brown-noise.wav
  sounds/pinknoise.wav             (display name: "Dark Rain Rumble Noise")
  sounds/white-noise.wav

Generated files (expanded set, added alpha.7):
  sounds/low-rumble-bed.wav        soft sub/low-mid rumble swells, no sharp peaks
  sounds/distant-train-bed.wav     soft low rolling rail cadence, no horn/screech
  sounds/soft-traffic-bed.wav      distant smooth city wash, no honks/sirens/events
  sounds/fan-room-bed.wav          steady fan/AC bed, smoother than white noise
  sounds/rain-on-glass-noise.wav   light synthetic taps over a soft rain bed
  sounds/deep-water-bed.wav        low filtered water movement, no splashes
  sounds/ember-crackle-bed.wav     sparse soft crackles over a warm noise bed

Generated files (experimental thunder audition candidates):
  sounds/distant-thunder-bed.wav    sparse distant low thunder rolls, no rain
  sounds/soft-thunderstorm-bed.wav  soft low thunder rolls with faint rain hush

Honesty rule: every generated bed is named for what it actually is (a synthetic
"bed"/"noise"), never dressed up as a field recording. If a synthesis approach
does not convincingly match a name, the name is changed, not the audio faked.
"""
from __future__ import annotations

import argparse
import math
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOUNDS_DIR = ROOT / "sounds"
SAMPLE_RATE = 44_100
DEFAULT_SECONDS = 60

# Conservative peaks keep stacked mixer channels gentle.
PEAKS = {
    "soft-rain-noise.wav": 0.22,
    "window-rain-noise.wav": 0.23,
    "heavy-rain-noise.wav": 0.24,
    "distant-storm-noise.wav": 0.25,
    "soft-wind-noise.wav": 0.20,
    "brown-noise.wav": 0.26,
    "pinknoise.wav": 0.24,
    "white-noise.wav": 0.22,
    # Expanded set (alpha.7). Kept in the same conservative 0.20–0.26 band so a
    # newly added bed never jumps out louder than the originals in the mixer.
    "low-rumble-bed.wav": 0.26,
    "distant-train-bed.wav": 0.22,
    "soft-traffic-bed.wav": 0.21,
    "fan-room-bed.wav": 0.23,
    "rain-on-glass-noise.wav": 0.23,
    "deep-water-bed.wav": 0.24,
    "ember-crackle-bed.wav": 0.22,
    # Experimental thunder audition candidates. Lower peaks than the broad noise
    # beds because sparse low events can feel louder than their meter level.
    "distant-thunder-bed.wav": 0.20,
    "soft-thunderstorm-bed.wav": 0.21,
}


def _normalise(audio: np.ndarray, peak: float) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float64)
    audio = audio - np.mean(audio)
    max_abs = float(np.max(np.abs(audio))) if audio.size else 0.0
    if max_abs:
        audio = audio / max_abs * peak
    return audio


def _loop_blend(audio: np.ndarray, seconds_tail: float = 4.0) -> np.ndarray:
    """Make a bed loop seamlessly by crossfading its tail into its head.

    The last ``seconds_tail`` are equal-power-ish crossfaded over the first
    ``seconds_tail`` and then trimmed, so playback wraps without a click or a
    sudden level change at the loop point. Returns a slightly shorter array.
    """
    n = len(audio)
    tail = min(int(seconds_tail * SAMPLE_RATE), n // 4)
    if tail < 16:
        return audio
    out = audio.copy()
    fade = np.linspace(0.0, 1.0, tail)
    head = out[:tail].copy()
    end = out[-tail:].copy()
    out[:tail] = end * (1.0 - fade) + head * fade
    return out[:-tail]


def _smooth_noise(n: int, rng: np.random.Generator, points: int = 128, low: float = 0.65, high: float = 1.0) -> np.ndarray:
    anchors = rng.uniform(low, high, points)
    x = np.linspace(0, points - 1, n)
    env = np.interp(x, np.arange(points), anchors)
    # Smooth interpolation a little with a small Hann window.
    win = np.hanning(401)
    win = win / win.sum()
    return np.convolve(env, win, mode="same")


def _fft_shaped_noise(n: int, rng: np.random.Generator, shape) -> np.ndarray:
    white = rng.standard_normal(n)
    spectrum = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, 1 / SAMPLE_RATE)
    gains = shape(freqs)
    gains = np.asarray(gains, dtype=np.float64)
    gains[0] = 0.0
    return np.fft.irfft(spectrum * gains, n)


def _band(freqs: np.ndarray, low: float, high: float, slope: float = 24.0) -> np.ndarray:
    freqs = np.maximum(freqs, 1.0)
    hp = 1.0 / (1.0 + (low / freqs) ** (slope / 6.0))
    lp = 1.0 / (1.0 + (freqs / high) ** (slope / 6.0))
    return hp * lp


def _add_droplets(audio: np.ndarray, rng: np.random.Generator, *, count: int, amp: float, min_len: int, max_len: int, bright: bool = True) -> np.ndarray:
    out = audio.copy()
    n = len(out)
    for _ in range(count):
        length = int(rng.integers(min_len, max_len))
        if length < 4 or length >= n:
            continue
        start = int(rng.integers(0, n - length))
        decay = np.exp(-np.linspace(0, 5.5 if bright else 3.4, length))
        click = rng.standard_normal(length) * decay
        if not bright:
            click = np.cumsum(click)
            click -= click.mean()
            m = np.max(np.abs(click)) or 1.0
            click = click / m
        out[start:start + length] += click * amp * rng.uniform(0.45, 1.0)
    return out


def _event_shape(n: int, attack_s: float, decay_s: float) -> np.ndarray:
    t = np.arange(n) / SAMPLE_RATE
    attack = np.clip(t / max(attack_s, 1e-3), 0.0, 1.0)
    attack = attack * attack * (3.0 - 2.0 * attack)
    decay = np.exp(-np.maximum(t - attack_s, 0.0) / max(decay_s, 1e-3))
    env = attack * decay
    max_env = np.max(env) or 1.0
    env = env / max_env
    tail = min(n, int(0.08 * SAMPLE_RATE))
    if tail > 1:
        env[-tail:] *= np.linspace(1.0, 0.0, tail)
    return env


def _thunder_event(length: int, rng: np.random.Generator, *, low: float, high: float, attack_s: float, decay_s: float) -> np.ndarray:
    roll = _fft_shaped_noise(length, rng, lambda f: _band(f, low, high) / np.sqrt(np.maximum(f, 1.0)))
    roll *= _event_shape(length, attack_s, decay_s)
    # Slow irregular rolling envelope, never hard-gated.
    roll *= _smooth_noise(length, rng, points=max(8, int(length / SAMPLE_RATE * 1.5)), low=0.38, high=1.0)
    return roll


def _scheduled_thunder(n: int, rng: np.random.Generator, *, gap_range: tuple[float, float], dur_range: tuple[float, float], high_range: tuple[float, float], gain_range: tuple[float, float]) -> np.ndarray:
    out = np.zeros(n, dtype=np.float64)
    seconds = n / SAMPLE_RATE
    t = rng.uniform(5.0, 10.0)
    while t < seconds - dur_range[0]:
        length = min(int(rng.uniform(*dur_range) * SAMPLE_RATE), n - int(t * SAMPLE_RATE))
        if length <= 0:
            break
        ev = _thunder_event(
            length,
            rng,
            low=rng.uniform(18.0, 30.0),
            high=rng.uniform(*high_range),
            attack_s=rng.uniform(0.65, 1.25),
            decay_s=rng.uniform(3.5, 7.5),
        )
        ev *= rng.uniform(*gain_range)
        start = int(t * SAMPLE_RATE)
        out[start:start + length] += ev[:max(0, min(length, n - start))]
        t += length / SAMPLE_RATE * rng.uniform(0.45, 0.75) + rng.uniform(*gap_range)
    return out


def _low_rumble_floor(n: int, rng: np.random.Generator, *, high: float, level: float) -> np.ndarray:
    bed = _fft_shaped_noise(n, rng, lambda f: _band(f, 22, high) / np.sqrt(np.maximum(f, 1.0)))
    bed *= _smooth_noise(n, rng, points=18, low=0.45, high=1.0)
    return _normalise(bed, level)


def _soft_rain_hush(n: int, rng: np.random.Generator, *, level: float) -> np.ndarray:
    rain = _fft_shaped_noise(n, rng, lambda f: _band(f, 650, 6_200))
    rain *= _smooth_noise(n, rng, points=96, low=0.50, high=1.0)
    return _normalise(rain, level)


def white_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    return _normalise(rng.standard_normal(n), PEAKS["white-noise.wav"])


def pink_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    def shape(freqs: np.ndarray) -> np.ndarray:
        freqs = np.maximum(freqs, 1.0)
        return 1 / np.sqrt(freqs)
    return _normalise(_fft_shaped_noise(n, rng, shape), PEAKS["pinknoise.wav"])


def brown_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    steps = rng.standard_normal(n) * 0.02
    return _normalise(np.cumsum(steps), PEAKS["brown-noise.wav"])


def soft_rain_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    base = _fft_shaped_noise(n, rng, lambda f: _band(f, 450, 9_500) / np.sqrt(np.maximum(f, 1)))
    base *= _smooth_noise(n, rng, points=96, low=0.55, high=1.0)
    drops = int(max(60, n / SAMPLE_RATE * 16))
    base = _add_droplets(base, rng, count=drops, amp=0.018, min_len=35, max_len=180)
    return _normalise(base, PEAKS["soft-rain-noise.wav"])


def window_rain_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    base = _fft_shaped_noise(n, rng, lambda f: _band(f, 700, 12_000))
    base *= _smooth_noise(n, rng, points=140, low=0.45, high=1.0)
    drops = int(max(100, n / SAMPLE_RATE * 28))
    base = _add_droplets(base, rng, count=drops, amp=0.028, min_len=20, max_len=110, bright=True)
    return _normalise(base, PEAKS["window-rain-noise.wav"])


def heavy_rain_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    low = _fft_shaped_noise(n, rng, lambda f: _band(f, 120, 2_400) / np.power(np.maximum(f, 1), 0.20))
    high = _fft_shaped_noise(n, rng, lambda f: _band(f, 1_400, 11_500))
    env = _smooth_noise(n, rng, points=180, low=0.70, high=1.0)
    audio = (0.72 * low + 0.38 * high) * env
    audio = _add_droplets(audio, rng, count=int(n / SAMPLE_RATE * 36), amp=0.012, min_len=20, max_len=90)
    return _normalise(audio, PEAKS["heavy-rain-noise.wav"])


def distant_storm_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    rain = heavy_rain_noise(n, rng) / PEAKS["heavy-rain-noise.wav"] * 0.16
    rumble = np.zeros(n, dtype=np.float64)
    seconds = n / SAMPLE_RATE
    for t in np.arange(8, seconds, 22):
        start = int((t + rng.uniform(-3, 3)) * SAMPLE_RATE)
        length = int(rng.uniform(4.0, 9.0) * SAMPLE_RATE)
        if start < 0 or start >= n:
            continue
        length = min(length, n - start)
        burst = _fft_shaped_noise(length, rng, lambda f: _band(f, 25, 180) / np.sqrt(np.maximum(f, 1)))
        env = np.exp(-np.linspace(0, 5, length)) * np.sin(np.linspace(0, math.pi, length))
        rumble[start:start + length] += burst * env * rng.uniform(0.45, 0.9)
    return _normalise(rain + rumble, PEAKS["distant-storm-noise.wav"])


def soft_wind_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    base = _fft_shaped_noise(n, rng, lambda f: _band(f, 70, 1_600) / np.power(np.maximum(f, 1), 0.15))
    gusts = _smooth_noise(n, rng, points=42, low=0.10, high=1.0)
    slow = 0.72 + 0.28 * np.sin(np.linspace(0, 2 * np.pi * max(1, n / SAMPLE_RATE / 18), n))
    return _normalise(base * gusts * slow, PEAKS["soft-wind-noise.wav"])


# ---------------------------------------------------------------------------
# Expanded procedural set (alpha.7).
#
# Design rules shared by all of these:
#   * No pure tones, melody, or voice-like formants — everything is shaped noise
#     or noise modulated by *slow* envelopes well below pitch perception.
#   * Conservative peaks via PEAKS, matching the original beds.
#   * Slow, rounded envelopes only; no fast attacks, so nothing startles a
#     half-asleep listener.
#   * Honest naming: each is a "bed"/"noise", not a simulated field recording.
# ---------------------------------------------------------------------------

def low_rumble_bed(n: int, rng: np.random.Generator) -> np.ndarray:
    """Occasional soft sub/low-mid rumble — thunder-adjacent, never sharp.

    A continuous low bed at a healthy floor, with long raised-cosine swells in
    the 22–130 Hz region fading in and out over 9–14 s. Because the swells rise
    from an already-audible bed (not from silence) and have a slow soft attack,
    there is no perceptible onset — just the room seeming to breathe low.
    """
    bed = _fft_shaped_noise(n, rng, lambda f: _band(f, 30, 240) / np.sqrt(np.maximum(f, 1)))
    bed *= _smooth_noise(n, rng, points=60, low=0.75, high=1.0)
    swells = np.zeros(n, dtype=np.float64)
    seconds = n / SAMPLE_RATE
    for t in np.arange(8, seconds, rng.uniform(16, 22)):
        start = int((t + rng.uniform(-2, 2)) * SAMPLE_RATE)
        if start < 0 or start >= n:
            continue
        length = min(int(rng.uniform(9.0, 14.0) * SAMPLE_RATE), n - start)
        burst = _fft_shaped_noise(length, rng, lambda f: _band(f, 22, 130) / np.sqrt(np.maximum(f, 1)))
        env = (0.5 - 0.5 * np.cos(np.linspace(0, 2 * np.pi, length))) ** 1.5
        swells[start:start + length] += burst * env * rng.uniform(0.35, 0.6)
    return _normalise(bed * 0.85 + swells, PEAKS["low-rumble-bed.wav"])


def distant_train_bed(n: int, rng: np.random.Generator) -> np.ndarray:
    """Very soft low rolling rail texture — no horn, no metallic screech.

    Low-mid shaped noise (60–1400 Hz) given a gentle periodic amplitude ripple
    to suggest the rolling cadence of distant rail joints. The cadence is a
    smooth squared sinusoid, so it reads as rhythmic motion rather than discrete
    clacks, with a slow drift envelope so it never sounds mechanical/looping.
    """
    bed = _fft_shaped_noise(n, rng, lambda f: _band(f, 60, 1_400) / np.power(np.maximum(f, 1), 0.25))
    seconds = n / SAMPLE_RATE
    t = np.linspace(0, seconds, n)
    period = rng.uniform(1.4, 1.9)
    cadence = 0.82 + 0.18 * (0.5 + 0.5 * np.sin(2 * np.pi * t / period)) ** 2
    drift = _smooth_noise(n, rng, points=40, low=0.7, high=1.0)
    return _normalise(bed * cadence * drift, PEAKS["distant-train-bed.wav"])


def soft_traffic_bed(n: int, rng: np.random.Generator) -> np.ndarray:
    """Distant city traffic wash — very low and smooth, no honks/sirens/events.

    Low-mid shaped noise with two layered slow envelopes (a fast-ish wash and a
    very slow "passing" swell). Both envelopes are heavily smoothed so no single
    pass is identifiable as a discrete vehicle — it stays an anonymous wash.
    """
    bed = _fft_shaped_noise(n, rng, lambda f: _band(f, 80, 1_100) / np.power(np.maximum(f, 1), 0.30))
    wash = _smooth_noise(n, rng, points=50, low=0.45, high=1.0)
    swell = _smooth_noise(n, rng, points=24, low=0.6, high=1.0)
    return _normalise(bed * wash * swell, PEAKS["soft-traffic-bed.wav"])


def fan_room_bed(n: int, rng: np.random.Generator) -> np.ndarray:
    """Steady fan / air-conditioner style bed — smoother than white noise.

    Band-limited mid "air" (200–3200 Hz) plus a faint low "body" band (90–600 Hz)
    to imply a motor without using any pure tone. A very steady envelope keeps it
    flat and reliable — the most "appliance-like" of the set.
    """
    air = _fft_shaped_noise(n, rng, lambda f: _band(f, 200, 3_200) / np.power(np.maximum(f, 1), 0.15))
    body = _fft_shaped_noise(n, rng, lambda f: _band(f, 90, 600))
    bed = 0.8 * air + 0.4 * body
    bed *= _smooth_noise(n, rng, points=30, low=0.85, high=1.0)
    return _normalise(bed, PEAKS["fan-room-bed.wav"])


def rain_on_glass_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    """Light synthetic rain taps over a soft rain bed — windowpane feel.

    Brighter band than soft-rain (600 Hz–11 kHz) with a breathing envelope, plus
    denser short decaying noise taps than the soft-rain bed uses. The taps are
    small (amp ~0.026) so they read as drops on glass, closer to the window-rain
    character than to plain filtered noise.
    """
    base = _fft_shaped_noise(n, rng, lambda f: _band(f, 600, 11_000))
    base *= _smooth_noise(n, rng, points=130, low=0.45, high=1.0)
    taps = int(max(80, n / SAMPLE_RATE * 30))
    out = _add_droplets(base, rng, count=taps, amp=0.026, min_len=18, max_len=120, bright=True)
    return _normalise(out, PEAKS["rain-on-glass-noise.wav"])


def deep_water_bed(n: int, rng: np.random.Generator) -> np.ndarray:
    """Low filtered water-like movement — no animal sounds, no splashes.

    Low shaped noise (40–700 Hz) modulated by gentle detuned sinusoidal surges
    (10–14 s and 6–8 s periods) plus a smoothed body envelope. The surges are
    shallow (clipped to 0.45–1.1) so the water "moves" without any sudden splash
    or transient.
    """
    low = _fft_shaped_noise(n, rng, lambda f: _band(f, 40, 700) / np.sqrt(np.maximum(f, 1)))
    seconds = n / SAMPLE_RATE
    t = np.linspace(0, seconds, n)
    surge = (0.78
             + 0.13 * np.sin(2 * np.pi * t / rng.uniform(10, 14))
             + 0.09 * np.sin(2 * np.pi * t / rng.uniform(6, 8) + 1.0))
    surge = np.clip(surge, 0.45, 1.1)
    body = _smooth_noise(n, rng, points=70, low=0.7, high=1.0)
    return _normalise(low * surge * body, PEAKS["deep-water-bed.wav"])


def ember_crackle_bed(n: int, rng: np.random.Generator) -> np.ndarray:
    """Sparse soft crackles over a warm noise bed — not harsh, not clicky.

    Warm low-mid bed (90–1800 Hz) carries sparse crackles (~4/s). Each crackle is
    a short decaying noise burst that is *integrated* (cumulative-summed) to round
    off its attack, so it pops softly rather than clicking. Crackle amplitude is
    small and the warm bed dominates, keeping the texture gentle.
    """
    warm = _fft_shaped_noise(n, rng, lambda f: _band(f, 90, 1_800) / np.power(np.maximum(f, 1), 0.35))
    warm *= _smooth_noise(n, rng, points=50, low=0.6, high=1.0)
    out = _add_droplets(warm, rng, count=int(n / SAMPLE_RATE * 4), amp=0.05,
                        min_len=40, max_len=160, bright=False)
    return _normalise(out, PEAKS["ember-crackle-bed.wav"])


def distant_thunder_bed(n: int, rng: np.random.Generator) -> np.ndarray:
    """Sparse distant thunder candidate — deep rolling events, no rain.

    Adapted from the local Claude thunder design, but implemented with
    Nocturne's NumPy-only generator helpers. Events use slow soft attacks,
    low-pass shaped noise, and conservative peak normalization so they can be
    auditioned under rain beds without sharp cracks or startling transients.
    """
    floor = _low_rumble_floor(n, rng, high=95.0, level=0.045)
    thunder = _scheduled_thunder(
        n,
        rng,
        gap_range=(18.0, 48.0),
        dur_range=(4.5, 9.5),
        high_range=(105.0, 210.0),
        gain_range=(0.28, 0.82),
    )
    return _normalise(floor + thunder, PEAKS["distant-thunder-bed.wav"])


def soft_thunderstorm_bed(n: int, rng: np.random.Generator) -> np.ndarray:
    """Soft thunderstorm candidate — distant rolls plus a faint rain hush.

    Also adapted from the local Claude thunder design. This is an audition
    candidate, not a default: closer-spaced low rolls sit under a quiet
    band-limited rain texture with no bright thunder cracks.
    """
    floor = _low_rumble_floor(n, rng, high=105.0, level=0.042)
    thunder = _scheduled_thunder(
        n,
        rng,
        gap_range=(12.0, 32.0),
        dur_range=(4.0, 8.0),
        high_range=(95.0, 190.0),
        gain_range=(0.22, 0.64),
    )
    rain = _soft_rain_hush(n, rng, level=0.036)
    return _normalise(floor + thunder + rain, PEAKS["soft-thunderstorm-bed.wav"])


def save_wav(path: Path, audio: np.ndarray) -> None:
    audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(audio_int16.tobytes())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Nocturne procedural starter ambience.")
    parser.add_argument(
        "--seconds",
        type=int,
        default=DEFAULT_SECONDS,
        help=f"duration per file; default: {DEFAULT_SECONDS}",
    )
    parser.add_argument("--seed", type=int, default=20260609, help="deterministic random seed")
    parser.add_argument("--overwrite", action="store_true", help="replace existing files")
    parser.add_argument("--no-loop-blend", action="store_true", help="skip tail/head crossfade (files keep full --seconds length)")
    parser.add_argument("--only", nargs="*", choices=sorted(PEAKS), help="generate only the named files")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.seconds < 1:
        parser.error("--seconds must be at least 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    SOUNDS_DIR.mkdir(exist_ok=True)
    n = SAMPLE_RATE * args.seconds
    rng = np.random.default_rng(args.seed)
    generators = {
        "soft-rain-noise.wav": soft_rain_noise,
        "window-rain-noise.wav": window_rain_noise,
        "heavy-rain-noise.wav": heavy_rain_noise,
        "distant-storm-noise.wav": distant_storm_noise,
        "soft-wind-noise.wav": soft_wind_noise,
        "brown-noise.wav": brown_noise,
        "pinknoise.wav": pink_noise,
        "white-noise.wav": white_noise,
        # Expanded set (alpha.7)
        "low-rumble-bed.wav": low_rumble_bed,
        "distant-train-bed.wav": distant_train_bed,
        "soft-traffic-bed.wav": soft_traffic_bed,
        "fan-room-bed.wav": fan_room_bed,
        "rain-on-glass-noise.wav": rain_on_glass_noise,
        "deep-water-bed.wav": deep_water_bed,
        "ember-crackle-bed.wav": ember_crackle_bed,
        # Experimental thunder audition candidates
        "distant-thunder-bed.wav": distant_thunder_bed,
        "soft-thunderstorm-bed.wav": soft_thunderstorm_bed,
    }
    selected = set(args.only or generators.keys())

    for filename, generator in generators.items():
        if filename not in selected:
            continue
        path = SOUNDS_DIR / filename
        if path.exists() and not args.overwrite:
            print(f"Keeping existing {filename} (use --overwrite to replace)")
            continue
        print(f"Generating {filename}…", flush=True)
        audio = generator(n, rng)
        if not args.no_loop_blend:
            audio = _loop_blend(audio)
        save_wav(path, audio)
        print(f"  wrote {path.stat().st_size / 1_048_576:.1f} MB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
