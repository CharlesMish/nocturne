# Nocturne scripts

## What works immediately

```bash
python3 install.py
```

The installer creates the virtual environment, installs dependencies, creates local folders, writes default config, and generates the procedural starter sound pack.

## Core scripts

| Task | Command | Output |
|---|---|---|
| Generate procedural starter beds | `python3 scripts/generate_noise.py` | rain-like placeholders, storm/wind noise, pink/brown/white noise in `sounds/` |
| Import curated CC0/user-owned sounds | `python scripts/import_sound_pack.py sounds/inbox --metadata-csv audio_sources.csv --generate-credits` | copied files in `sounds/library/`, updated `sounds/sound_library.json`, regenerated credits/provenance |
| Regenerate credits only | `python scripts/write_audio_credits.py` | `AUDIO_CREDITS.md`, `AUDIO_PROVENANCE.md` |
| Legacy optional Pixabay fetcher | `python scripts/fetch_media.py --init` then `python scripts/fetch_media.py --yes` | old fixed files in `sounds/` plus receipts, if scraping/downloads work |
| Stamp release build | `python scripts/stamp_build.py --version 0.1.0-alpha.N` | updated `nocturne_build.json` |

## Preferred media workflow

Use `docs/FREESOUND_CC0_WORKFLOW.md`. The short version:

1. Download CC0 candidates into `sounds/inbox/`.
2. Screenshot each source page into `provenance/screenshots/`.
3. Fill `audio_sources.csv` from `audio_sources.template.csv`.
4. Import with `scripts/import_sound_pack.py`.
5. Audition through Nocturne's sound picker.

## Legacy `fetch_media.py`

`fetch_media.py` is a compatibility helper for the old fixed Onsen/Sky ambient filenames. It does **not** manage the new assignable sound library and does **not** fetch Radio tracks.
