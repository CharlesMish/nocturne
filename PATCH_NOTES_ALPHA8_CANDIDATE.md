# Nocturne alpha.8 candidate — expanded generated beds

This is an audition candidate, not the final alpha.8 release.

Merged wholesale from the generated-sounds bundle on top of the alpha.7 source-split preview build:

- 7 new generated procedural beds:
  - `low-rumble-bed.wav`
  - `distant-train-bed.wav`
  - `soft-traffic-bed.wav`
  - `fan-room-bed.wav`
  - `rain-on-glass-noise.wav`
  - `deep-water-bed.wav`
  - `ember-crackle-bed.wav`
- `scripts/generate_noise.py` expanded to generate all 17 procedural beds, including two thunder audition candidates.
- `sounds/sound_library.json` currently has 29 entries: 12 recorded CC0 + 17 generated.
- `check_audio_contract.py` updated for the expanded generated set.
- `docs/PROCEDURAL_STARTER_SOUNDS.md`, `MEDIA_LICENSES.md`, and README updated.
- `static/index.html` fallback sound-library block synced.

Small mechanical fix applied during merge:

- `_loop_blend()` now computes the crossfade tail as `min(int(seconds_tail * SAMPLE_RATE), n // 4)` so short test generations behave correctly.

Recommended review:

1. Run `python install.py --no-fetch-media`.
2. Run `.venv/bin/python run_nocturne.py`.
3. Open `http://127.0.0.1:8000/`.
4. Use the picker `generated` filter and preview every new generated bed.
5. Mark each sound as keep / maybe / reject based on honest naming and sleep usefulness.

Do not treat new generated beds as accepted until they have been auditioned. The two thunder beds are audition candidates only and are not defaults.
