# Procedural starter sounds

Nocturne's generated sounds are **starter beds**, not final field recordings.
They exist so a fresh install can make sound immediately while the bundled
CC0 sound pack is being curated.

## What is generated

`python scripts/generate_noise.py` creates these local WAV files.

Original set:

- `soft-rain-noise.wav`
- `window-rain-noise.wav`
- `heavy-rain-noise.wav`
- `distant-storm-noise.wav` (shown as **Soft Pink Rain Noise** after alpha.8 audition)
- `soft-wind-noise.wav` (shown as **Soft Air Noise**)
- `pinknoise.wav`
- `brown-noise.wav`
- `white-noise.wav`

Expanded set (alpha.7):

- `low-rumble-bed.wav` — soft sub/low-mid rumble with slow swells; thunder-adjacent, no sharp peaks.
- `distant-train-bed.wav` — soft low rolling rail cadence; no horn, no metallic screech.
- `soft-traffic-bed.wav` — distant smooth city wash; no honks, sirens, or identifiable events.
- `fan-room-bed.wav` — steady fan/air-conditioner bed; smoother and warmer than white noise.
- `rain-on-glass-noise.wav` — light synthetic taps over a soft rain bed; windowpane feel.
- `deep-water-bed.wav` — low filtered water movement; no animal sounds, no splashes.
- `ember-crackle-bed.wav` — sparse soft crackles over a warm bed; rounded, not clicky.

Thunder audition candidates (alpha.8):

- `distant-thunder-bed.wav` — sparse low thunder rolls, no rain; audition candidate.
- `soft-thunderstorm-bed.wav` — soft low thunder rolls with faint rain hush; audition candidate.

The noise files are useful in their own right. The rain/storm/wind/train/traffic/
water/ember files are best understood as believable-enough texture beds.

## Honest naming

Every generated file is named for what it actually is — a synthetic *bed* or
*noise*, never a field recording. If a synthesis approach does not convincingly
match a name, the **name** is changed rather than the audio faked. That is why
the old "Distant Storm" became **Soft Pink Rain Noise** after alpha.8 audition
and "Soft Wind" became **Soft Air Noise**: they are steady synthetic beds, not
real occasional thunder or wind. A user auditioning a generated bed should
never feel misled.

## How the synthesized files work

All beds are shaped noise modulated by slow envelopes — no pure tones, melody,
or voice-like formants, and no fast attacks.

The rain-like files:

- band-limited white noise gives the soft broadband wash of rainfall;
- slow amplitude envelopes make the texture breathe instead of sounding static;
- small decaying noise bursts are sprinkled in as droplets/taps;
- heavy rain adds lower-frequency wash;
- soft pink rain noise adds a broad rain/noise wash that alpha.8 audition found
  closer to pink-noise-like texture than convincing thunder.

The expanded beds:

- **low-rumble-bed** — a continuous low bed plus long raised-cosine swells in the
  22–130 Hz band. Swells rise from an already-audible floor with a slow soft
  attack, so there is no perceptible onset.
- **distant-train-bed** — low-mid noise with a gentle periodic amplitude ripple
  (a smooth squared sinusoid) for rolling cadence, plus a slow drift so it never
  sounds mechanically looped.
- **soft-traffic-bed** — low-mid noise under two heavily smoothed envelopes; no
  single swell is identifiable as one vehicle.
- **fan-room-bed** — mid "air" band plus a faint low "body" band to imply a motor
  without any tone, under a very steady envelope.
- **rain-on-glass-noise** — brighter rain band with denser, slightly larger taps
  than soft-rain, pushing it toward a windowpane character.
- **deep-water-bed** — low noise modulated by shallow detuned sinusoidal surges
  so the water moves without splashes.
- **ember-crackle-bed** — warm bed with sparse crackles; each crackle is an
  *integrated* (cumulative-summed) noise burst, which rounds the attack so it
  pops softly instead of clicking.
- **distant-thunder-bed** — sparse distant low thunder rolls over a very quiet
  rumble floor; no rain and no sharp cracks.
- **soft-thunderstorm-bed** — closer-spaced low thunder rolls with faint rain
  hush; audition candidate only, not a default.

Every bed is also tail-to-head crossfaded (`_loop_blend`) so it loops without a
click or level jump.

This can sound pleasant in a sleep mixer, especially under other layers, but it
will not fool someone listening critically on headphones. Real ambiences have
complex space, surfaces, stereo movement, and irregular detail that a simple
generator does not fully reproduce.

## Release stance

Use these as the guaranteed fallback pack:

- local;
- deterministic;
- license-safe;
- no network;
- generated during install.

For the public alpha's default sound pack, prefer reviewed CC0 field recordings
from Freesound or another source with clear redistribution permission.
