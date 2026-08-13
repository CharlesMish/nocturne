# Freesound CC0 curation workflow

Goal: make Nocturne's bundled ambience pack transparent, replaceable, and easy to audit.

## Rule of thumb

Use **CC0 only** for the bundled default pack unless you have a very deliberate reason to accept attribution obligations. Credit creators anyway.

Avoid:

- Creative Commons Attribution Noncommercial.
- No-derivatives sources if you trim, normalize, loop, or crossfade.
- Sound libraries whose terms forbid raw redistribution.
- “Hidden in a binary” as a licensing strategy.

## Folder layout

```text
sounds/inbox/                 # raw files you are evaluating/importing
sounds/library/               # app-ready curated loops used by the mixer
provenance/screenshots/       # screenshots of source pages/license state
provenance/originals/         # optional private/original copies before edits
sounds/sound_library.json     # app manifest
AUDIO_CREDITS.md              # human-readable credits
AUDIO_PROVENANCE.md           # audit trail
```

## Suggested pass

1. Search Freesound with license filter set to **Creative Commons 0**.
2. Prefer longer, loopable, boring sounds: rain, room, stream, wind, distant thunder.
3. Download candidates into `sounds/inbox/`.
4. Screenshot each source page showing title, creator, URL, and CC0 license into `provenance/screenshots/`.
5. Fill a copy of `audio_sources.template.csv`.
6. Import:

```bash
python scripts/import_sound_pack.py sounds/inbox --metadata-csv audio_sources.csv --generate-credits
```

7. Audition in Nocturne's sound picker.
8. Promote your favorite eight with:

```bash
python scripts/import_sound_pack.py sounds/inbox --metadata-csv audio_sources.csv --set-defaults --generate-credits --replace
```

## Starter files generated locally

`python scripts/generate_noise.py` creates 17 procedural starter beds. The
canonical inventory lives in `sounds/sound_library.json`; it currently includes
the original noise set, seven expanded ambient beds, and two explicitly
Experimental thunder candidates.

These keep the app testable while you curate real CC0 field recordings. They
are synthetic and still require human listening review.
