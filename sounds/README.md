# Nocturne sound areas

Nocturne keeps playable audio, curation intake, and personal Radio tracks separate.

```text
sounds/
  sound_library.json       # canonical public catalog + exclusion records
  *.wav                    # 17 procedural beds generated during install
  library/                 # 11 bundled public CC0 recordings
  inbox/                   # never public; intake and quarantine
    quarantine-seam-risk/  # retained evidence in review tree / evidence ZIP
    quarantine-unverified/ # records for payloads that are not shipped
    seam-baked/            # candidates + sidecars; detached from tester ZIP
  radio/                   # personal Radio tracks
```

## Public mixer contract

The Onsen/Sky mixer always has eight live slots. `sound_library.json` is the source of truth for the picker and contains:

- **8 Tonight defaults:** all bundled recorded CC0 files;
- **3 optional bundled recordings:** including Gentle Waves, which is not a default;
- **15 ordinary install-generated beds**;
- **2 Experimental install-generated thunder candidates**.

That is 28 public catalog entries. Generated WAVs are intentionally absent from the source archive and are created by `install.py` or `scripts/generate_noise.py`. The browser fallback is generated from the canonical JSON by `scripts/sync_release_data.py`; do not hand-edit both copies.

## Quarantine

Nothing under `sounds/inbox/` is served by `/sounds`. Non-README inbox payloads are also detached from the slim tester ZIP and placed in the companion evidence archive. The canonical manifest retains paths, sizes, hashes, and three exclusion records:

- `rain-inside-house`: payload retained under `quarantine-seam-risk/` after numerical boundary screening found a severe seam-risk signal;
- `rain-inside-house-seam-baked`: an offline cyclic-crossfade render with a transform sidecar; still `audition_required`;
- `soft-wind-trees`: historical hash and reason retained, but the unverified payload is not shipped.

Promotion requires an explicit manifest edit, catalog synchronization, release audit, and human listening record. Moving a file alone is not promotion.

## Importing a recorded sound

Place finished, appropriately licensed audio in `sounds/inbox/`, complete the metadata CSV, then run:

```bash
python scripts/import_sound_pack.py sounds/inbox \
  --metadata-csv audio_sources.csv \
  --generate-credits
```

Use `--set-defaults` only with at least eight reviewed files. The importer updates the canonical manifest and synchronizes the browser fallback.

## Radio

Radio is separate from the ambience catalog. Drop personal tracks or bedtime-story files into `sounds/radio/` and refresh the browser. Keep provenance honest; user-owned or user-licensed narration is not CC0 unless that status is separately established.
