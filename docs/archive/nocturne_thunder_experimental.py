"""Historical experimental thunder-generation scratch script.

Not used by alpha.8 runtime or install path; active generated beds are produced
by scripts/generate_noise.py.

Original scratch filename: nocturne_thunder.py
-------------------
Procedural "distant sleep thunder" beds for Nocturne.

Two candidates:
  - Candidate A: distant_thunder   -> sparse, deep rolling rumbles, no rain.
  - Candidate B: soft_thunderstorm -> softer/closer-spaced thunder + faint rain hush.

Pure numpy/scipy. No samples, no files, no network.
Designed to layer UNDER rain/ambient beds without dominating.

Drop these helpers into your generator, or call build_candidate_a / build_candidate_b
and feed the result to your existing WAV writer. A reference writer is included.
"""

import numpy as np
from scipy import signal
from scipy.interpolate import PchipInterpolator
from scipy.io import wavfile

SR = 44100

# ----------------------------------------------------------------------------- #
# Low-level building blocks
# ----------------------------------------------------------------------------- #

def _rng(seed=None):
    return np.random.default_rng(seed)


def brown_noise(n, sr, rng, hp_hz=25.0):
    """Brown/red noise (random walk) with a gentle high-pass so it doesn't
    wander into DC / subsonic. Energy concentrated in the low end (-6 dB/oct)."""
    w = rng.standard_normal(n)
    b = np.cumsum(w)
    b -= np.mean(b)
    sos = signal.butter(2, hp_hz / (0.5 * sr), btype="high", output="sos")
    b = signal.sosfiltfilt(sos, b)
    b /= (np.max(np.abs(b)) + 1e-9)
    return b


def lowpass(x, cutoff_hz, sr, order=4):
    sos = signal.butter(order, cutoff_hz / (0.5 * sr), btype="low", output="sos")
    return signal.sosfiltfilt(sos, x)


def highpass(x, cutoff_hz, sr, order=2):
    sos = signal.butter(order, cutoff_hz / (0.5 * sr), btype="high", output="sos")
    return signal.sosfiltfilt(sos, x)


def bandpass(x, lo_hz, hi_hz, sr, order=2):
    sos = signal.butter(order, [lo_hz / (0.5 * sr), hi_hz / (0.5 * sr)],
                        btype="band", output="sos")
    return signal.sosfiltfilt(sos, x)


def smooth_random_env(n, sr, rng, rate_hz=1.0, lo=0.0, hi=1.0):
    """Slow, smooth, irregular control envelope in [lo, hi].

    Built from random control points spaced ~1/rate apart, then PCHIP
    interpolated (monotone, no overshoot -> never leaves range, never negative).
    More robust than ultra-low-cutoff filtering for slow LFOs."""
    npts = max(3, int(n / sr * rate_hz) + 2)
    xp = np.linspace(0, n - 1, npts)
    yp = rng.random(npts)
    e = PchipInterpolator(xp, yp)(np.arange(n))
    e -= e.min()
    e /= (e.max() + 1e-9)
    return lo + (hi - lo) * e


def event_shape(n, sr, attack_s=0.6, decay_s=4.0):
    """Soft-attack / long-decay envelope for a single thunder event.
    Smoothstep attack (no click), exponential decay. Starts and ends near 0."""
    t = np.arange(n) / sr
    a = np.clip(t / max(attack_s, 1e-3), 0, 1)
    a = a * a * (3 - 2 * a)                       # smoothstep
    d = np.exp(-np.maximum(t - attack_s, 0) / max(decay_s, 1e-3))
    env = a * d
    env /= (env.max() + 1e-9)
    # guarantee the very tail returns to zero (anti-click on overlap-add)
    tail = min(n, int(0.05 * sr))
    if tail > 1:
        env[-tail:] *= np.linspace(1, 0, tail)
    return env


# ----------------------------------------------------------------------------- #
# Thunder event + scheduler
# ----------------------------------------------------------------------------- #

def thunder_event(dur_s, sr, rng, lp_hz=180.0, attack_s=0.6, decay_s=4.0,
                  roll_rate_hz=1.6, roll_depth=0.55):
    """One distant thunder roll.

    Filtered brown noise -> soft event shape -> slow irregular amplitude 'roll'.
    Lower lp_hz / lower level = farther away.
    """
    n = int(dur_s * sr)
    src = brown_noise(n, sr, rng)
    src = lowpass(src, lp_hz, sr, order=4)

    shape = event_shape(n, sr, attack_s=attack_s, decay_s=decay_s)
    # irregular rolling amplitude; stays >= (1 - roll_depth) so it never gates hard
    roll = smooth_random_env(n, sr, rng, rate_hz=roll_rate_hz,
                             lo=1.0 - roll_depth, hi=1.0)
    return src * shape * roll


def schedule_thunder(total_s, sr, rng,
                     gap_range=(14.0, 42.0),
                     dur_range=(3.5, 8.5),
                     lp_range=(120.0, 230.0),
                     gain_range=(0.35, 1.0),
                     first_after=(3.0, 8.0)):
    """Place randomized thunder events along a buffer via overlap-add.

    Per-event randomization (timing, duration, distance/cutoff, loudness,
    attack, decay, roll) is what kills audible repetition.
    """
    N = int(total_s * sr)
    buf = np.zeros(N, dtype=np.float64)

    t = rng.uniform(*first_after)
    while t < total_s - dur_range[0]:
        dur = rng.uniform(*dur_range)
        ev = thunder_event(
            dur, sr, rng,
            lp_hz=rng.uniform(*lp_range),
            attack_s=rng.uniform(0.35, 0.9),
            decay_s=rng.uniform(2.5, 6.0),
            roll_rate_hz=rng.uniform(1.0, 2.6),
            roll_depth=rng.uniform(0.4, 0.7),
        )
        ev *= rng.uniform(*gain_range)

        idx = int(t * sr)
        end = min(N, idx + len(ev))
        buf[idx:end] += ev[:end - idx]

        # advance: overlap the tail of this event a little into the next gap
        t += dur * rng.uniform(0.35, 0.7) + rng.uniform(*gap_range)
    return buf


def background_rumble(total_s, sr, rng, lp_hz=95.0, level=0.06, swell_rate_hz=0.06):
    """Very low constant rumble so silence is never truly dead.
    Slowly swelling so it isn't static. Keep level low; it's a floor, not a voice."""
    N = int(total_s * sr)
    bed = brown_noise(N, sr, rng)
    bed = lowpass(bed, lp_hz, sr, order=2)
    swell = smooth_random_env(N, sr, rng, rate_hz=swell_rate_hz, lo=0.5, hi=1.0)
    bed *= swell
    bed /= (np.max(np.abs(bed)) + 1e-9)
    return bed * level


def rain_texture(total_s, sr, rng, lo_hz=600.0, hi_hz=6500.0,
                 level=0.05, shimmer_rate_hz=6.0, swell_rate_hz=0.08):
    """Subtle rain hush for Candidate B. Band-limited noise with fast shallow
    shimmer + slow intensity swells. Deliberately quiet so it reads as 'faint
    rain on a far roof', not foreground hiss."""
    N = int(total_s * sr)
    w = rng.standard_normal(N)
    r = bandpass(w, lo_hz, hi_hz, sr, order=2)
    shimmer = smooth_random_env(N, sr, rng, rate_hz=shimmer_rate_hz, lo=0.75, hi=1.0)
    swell = smooth_random_env(N, sr, rng, rate_hz=swell_rate_hz, lo=0.6, hi=1.0)
    r = r * shimmer * swell
    r /= (np.max(np.abs(r)) + 1e-9)
    return r * level


# ----------------------------------------------------------------------------- #
# Loop, normalize, safety, write
# ----------------------------------------------------------------------------- #

def make_loopable(x, sr, xfade_s=3.0):
    """Crossfade the tail into the head so end -> start is seamless when looped.
    Returns a buffer slightly shorter than the input by xfade_s."""
    nf = int(xfade_s * sr)
    if nf <= 1 or nf * 2 >= len(x):
        return apply_edge_fades(x, sr, fade_s=min(1.0, len(x) / sr / 4))
    fin = np.linspace(0.0, 1.0, nf)
    loop = x.copy()
    loop[:nf] = x[:nf] * fin + x[-nf:] * (1.0 - fin)
    return loop[:-nf]


def apply_edge_fades(x, sr, fade_s=1.5):
    nf = min(int(fade_s * sr), len(x) // 2)
    if nf < 2:
        return x
    f = np.linspace(0.0, 1.0, nf)
    x = x.copy()
    x[:nf] *= f
    x[-nf:] *= f[::-1]
    return x


def dc_block(x):
    return x - np.mean(x)


def rms(x):
    return float(np.sqrt(np.mean(x ** 2) + 1e-12))


def match_rms(x, target_rms_db=-26.0):
    target = 10 ** (target_rms_db / 20.0)
    return x * (target / rms(x))


def normalize_peak(x, peak_db=-6.0):
    p = np.max(np.abs(x)) + 1e-12
    target = 10 ** (peak_db / 20.0)
    return x * (target / p)


def soft_limit(x, ceiling_db=-3.0):
    """Gentle tanh ceiling that only engages near the top -> no hard clipping,
    no sharp transients introduced."""
    c = 10 ** (ceiling_db / 20.0)
    return c * np.tanh(x / c)


def finalize(x, sr, target_rms_db=-26.0, ceiling_db=-3.0, xfade_s=3.0):
    """DC block -> loop crossfade -> RMS match to sibling beds -> soft ceiling."""
    x = dc_block(x)
    x = make_loopable(x, sr, xfade_s=xfade_s)
    x = match_rms(x, target_rms_db=target_rms_db)
    x = soft_limit(x, ceiling_db=ceiling_db)
    return x


def write_wav(path, x, sr, rng=None, bits=16):
    """Write mono WAV with TPDF dither (important: low-level rumble in 16-bit
    quantizes badly without it)."""
    rng = rng or _rng()
    x = np.clip(x, -1.0, 1.0)
    if bits == 16:
        lsb = 1.0 / 32768.0
        dither = (rng.random(len(x)) - rng.random(len(x))) * lsb  # TPDF
        y = np.clip(x + dither, -1.0, 1.0)
        wavfile.write(path, sr, np.int16(np.round(y * 32767)))
    else:  # 32-bit float
        wavfile.write(path, sr, x.astype(np.float32))


# ----------------------------------------------------------------------------- #
# Candidate builders
# ----------------------------------------------------------------------------- #

def build_candidate_a(total_s=120.0, sr=SR, seed=None, target_rms_db=-26.0):
    """distant_thunder: sparse deep rolling rumbles, lots of space, no rain.
    Meant to sit UNDER an existing rain bed."""
    rng = _rng(seed)
    bed = background_rumble(total_s, sr, rng, lp_hz=95.0, level=0.05)
    thunder = schedule_thunder(
        total_s, sr, rng,
        gap_range=(16.0, 46.0),
        dur_range=(3.5, 8.5),
        lp_range=(110.0, 220.0),
        gain_range=(0.30, 0.95),
    )
    mix = bed + thunder
    return finalize(mix, sr, target_rms_db=target_rms_db)


def build_candidate_b(total_s=120.0, sr=SR, seed=None, target_rms_db=-25.0):
    """soft_thunderstorm: softer/closer-spaced thunder + faint rain hush.
    Can stand alone as a 'storm in a bottle' or layer."""
    rng = _rng(seed)
    bed = background_rumble(total_s, sr, rng, lp_hz=100.0, level=0.05)
    thunder = schedule_thunder(
        total_s, sr, rng,
        gap_range=(10.0, 30.0),     # a bit more frequent
        dur_range=(3.0, 7.0),
        lp_range=(100.0, 200.0),    # a touch farther/softer on top
        gain_range=(0.25, 0.75),    # quieter rolls
    )
    rain = rain_texture(total_s, sr, rng, level=0.05)
    mix = bed + thunder + rain
    return finalize(mix, sr, target_rms_db=target_rms_db)


# ----------------------------------------------------------------------------- #
# Self-test
# ----------------------------------------------------------------------------- #

if __name__ == "__main__":
    import os
    out = os.environ.get("OUT", ".")
    dur = float(os.environ.get("DUR", "60"))

    a = build_candidate_a(total_s=dur, seed=11)
    b = build_candidate_b(total_s=dur, seed=22)

    for name, x in (("A_distant_thunder", a), ("B_soft_thunderstorm", b)):
        path = os.path.join(out, f"{name}.wav")
        write_wav(path, x, SR, rng=_rng(1))
        peak_db = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
        rms_db = 20 * np.log10(rms(x) + 1e-12)
        print(f"{name:20s} dur={len(x)/SR:6.2f}s  peak={peak_db:6.2f} dBFS  "
              f"rms={rms_db:6.2f} dBFS  -> {path}")
