# Procedural starter sounds

Nocturne can generate 17 local WAV texture beds with:

```bash
python scripts/generate_noise.py
```

They are deterministic synthesis outputs, not field recordings. The source archive intentionally omits the WAV payloads; the eight Tonight defaults are bundled recordings and remain usable before generation succeeds.

## Ordinary generated beds

- soft, window, and heavy rain noise;
- soft pink rain noise and soft air noise;
- dark rain rumble, brown, and white noise;
- low rumble, distant train, soft traffic, and fan/room beds;
- rain-on-glass noise, deep-water bed, and ember-crackle bed.

## Experimental generated beds

- `distant-thunder-bed.wav`
- `soft-thunderstorm-bed.wav`

These two are visible only under the Experimental picker filter and are never Tonight defaults.

## What the generator does

The script combines filtered noise, slow envelopes, sparse shaped events, conservative level limiting, and a tail/head blend. The naming is intentionally explicit: these are synthetic beds or noise, never claimed field recordings.

The tail/head blend is designed to reduce a boundary discontinuity. It does **not** prove that the loop is inaudible, free from fatigue, comfortable at bedside levels, or safe for overnight use. Generated outputs must be auditioned like recorded candidates.

## Release stance

Generated beds provide local, deterministic, network-free optional texture. Keep them honestly labeled and replace or rename a bed when its audible character does not match its description. Promotion to Tonight requires a manifest decision, synchronized fallback, software checks, and a recorded human/device audition.
