# Nocturne sound library

Nocturne's Onsen/Sky mixer has **eight active slots**. Each slot can be assigned from a larger local sound library, so the UI stays calm while the available sounds can grow.

## Current release shape

- `sounds/sound_library.json` is the primary assignable Onsen/Sky mixer library.
- Fresh install generates a procedural starter pack with `scripts/generate_noise.py`.
- This alpha's default slots prefer bundled recorded CC0/user-owned loops from `sounds/library/`, with generated beds used where they are the best current fit.
- Curated CC0/user-owned sounds live in `sounds/library/`.
- The sound picker reads `sounds/sound_library.json` and falls back to the built-in copy in `static/index.html` only if that manifest cannot be loaded.
- Radio tracks still live separately in `sounds/radio/`.

## Generated starter sounds

Generated during install:

```text
sounds/soft-rain-noise.wav
sounds/window-rain-noise.wav
sounds/heavy-rain-noise.wav
sounds/distant-storm-noise.wav
sounds/soft-wind-noise.wav
sounds/pinknoise.wav
sounds/brown-noise.wav
sounds/white-noise.wav
sounds/low-rumble-bed.wav
sounds/distant-train-bed.wav
sounds/soft-traffic-bed.wav
sounds/fan-room-bed.wav
sounds/rain-on-glass-noise.wav
sounds/deep-water-bed.wav
sounds/ember-crackle-bed.wav
sounds/distant-thunder-bed.wav
sounds/soft-thunderstorm-bed.wav
```

These are intentionally conservative, procedural placeholders. Replace the rain-like ones with curated CC0 field recordings as you find better material. The two thunder beds are alpha.8 audition candidates and should not become defaults until they pass human sleep-safety review.

## Manifest shape

```json
{
  "version": 4,
  "default_slots": ["rain-heavy-open-window", "rain-balcony-peaceful", "..."],
  "sounds": [
    {
      "id": "gentle-rain-cc0",
      "name": "Gentle Rain CC0",
      "category": "rain",
      "theme": "mist-rain",
      "src": "/sounds/library/gentle-rain-cc0.mp3",
      "source": "Freesound",
      "source_title": "Original title",
      "creator": "creator-name",
      "source_url": "https://freesound.org/s/000000/",
      "license": "CC0 1.0",
      "downloaded_at": "2026-06-09",
      "screenshot": "provenance/screenshots/gentle-rain-cc0.jpg",
      "sha256": "...",
      "edits": "trimmed; normalized; loop crossfade"
    }
  ]
}
```

Only `id`, `name`, `category`, `theme`, and `src` are required by the app. The source/provenance fields are for release hygiene.

## Visual themes

```text
mist-rain · garden-rain · distant-storm · mountain-storm · squall · tempest · hearth · ember-noise
```

Use rain themes for rain variants, `hearth` for fire, `ember-noise` for noise/fan/hum, and storm themes for thunder/rainstorm.

## Importing a curated pack

1. Put files in `sounds/inbox/`.
2. Fill `audio_sources.csv` using `audio_sources.template.csv`.
3. Run:

```bash
python scripts/import_sound_pack.py sounds/inbox --metadata-csv audio_sources.csv --generate-credits
```

To make the first eight imported files the default mixer slots:

```bash
python scripts/import_sound_pack.py sounds/inbox --metadata-csv audio_sources.csv --set-defaults --generate-credits --replace
```

## Regenerating credits

```bash
python scripts/write_audio_credits.py
```

This writes `AUDIO_CREDITS.md` and `AUDIO_PROVENANCE.md` from `sounds/sound_library.json`.

## Recorded vs generated

The app now treats these as separate picker filters. `Recorded CC0` entries are bundled Freesound CC0 loops in `sounds/library/`. `Generated` entries are procedural WAV beds created by `scripts/generate_noise.py` during install. Keep labels honest: generated beds should not promise realistic field recordings.

The sound picker also includes a preview button so release candidates can be auditioned before assigning a slot.
