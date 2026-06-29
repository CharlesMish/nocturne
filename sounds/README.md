# Nocturne sounds folder

Nocturne has three audio areas:

```text
sounds/
  soft-rain-noise.wav      # generated during install
  window-rain-noise.wav    # generated during install
  heavy-rain-noise.wav     # generated during install
  distant-storm-noise.wav  # generated during install
  soft-wind-noise.wav      # generated during install
  pinknoise.wav            # generated during install
  brown-noise.wav          # generated during install
  white-noise.wav          # generated during install
  low-rumble-bed.wav       # generated during install
  distant-train-bed.wav    # generated during install
  soft-traffic-bed.wav     # generated during install
  fan-room-bed.wav         # generated during install
  rain-on-glass-noise.wav  # generated during install
  deep-water-bed.wav       # generated during install
  ember-crackle-bed.wav    # generated during install
  distant-thunder-bed.wav  # generated during install; audition candidate
  soft-thunderstorm-bed.wav # generated during install; audition candidate
  sound_library.json       # assignable mixer library manifest
  inbox/                   # temporary curation/download intake
  library/                 # finished curated CC0/user-owned loops
  radio/                   # personal radio tracks
```

## Mixer sounds

The Onsen/Sky mixer has eight live slots. Each slot can choose any entry in `sound_library.json`.

Fresh install generates the procedural starter beds above. The public alpha defaults can point to bundled recorded loops in `sounds/library/` plus selected generated beds, all through `sound_library.json`.

Real curated ambience loops should go in `sounds/library/` and be imported with:

```bash
python scripts/import_sound_pack.py sounds/inbox --metadata-csv audio_sources.csv --generate-credits
```

## Radio sounds

Radio mode is separate. Drop personal tracks or bedtime-story MP3s into `sounds/radio/` and refresh the browser.

For stories, keep provenance honest: user-authored text, user-owned or user-licensed generated narration, and not CC0 unless separately proven.

## Legacy fixed names

The old Pixabay/fetcher filenames are still supported for compatibility/archive use, but are no longer the preferred release path:

```text
calming_rain.mp3
gentle_rain.mp3
heavy_rain.mp3
rainstorm.mp3
heavy_storm.mp3
thunder.mp3
fireplace.mp3
```
