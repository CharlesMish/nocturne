# Nocturne sound library

Nocturne's Onsen/Sky mixer has eight active slots. The public catalog can be larger, but the bedside surface stays intentionally small.

## Canonical release shape

`sounds/sound_library.json` is the source of truth. It currently defines:

- eight bundled recorded **Tonight** defaults;
- three optional bundled recordings;
- fifteen ordinary install-generated beds;
- two install-generated **Experimental** thunder candidates;
- three non-public exclusion records: an original seam-risk source, its transformed audition candidate, and one unshipped historical mismatch record.

The browser contains a generated fallback for resilience. Never hand-maintain it as a second catalog: run `python scripts/sync_release_data.py` after manifest edits and `--check` before release.

## Status and availability fields

| Field | Meaning |
|---|---|
| `status: core` | A Tonight/default entry. |
| `status: optional` | Ordinary wider-library entry. |
| `status: experimental` | Visible only through the Experimental picker filter. |
| `availability: bundled` | Payload exists in the source archive. |
| `availability: install_generated` | WAV is expected only after local generation. |
| `recommended: true` | Must agree with membership in the eight `default_slots`. |
| `retention: evidence_bundle` | Non-public payload/sidecar is detached from the tester ZIP but remains hash-recorded and ships in the companion evidence archive. |

`excluded_sounds` retains quarantine/provenance records but is never merged into the public `sounds[]` list.

## Minimal public entry

```json
{
  "id": "example-rain",
  "name": "Example Rain",
  "category": "rain",
  "theme": "mist-rain",
  "src": "/sounds/library/example-rain.mp3",
  "source_type": "recorded_cc0",
  "source_label": "Recorded CC0",
  "availability": "bundled",
  "status": "optional",
  "recommended": false,
  "sort_order": 200
}
```

Recorded release entries should additionally carry creator, source URL/title, license, verification/download date, screenshot, original/processed filenames, file size, SHA-256, and honest edit notes.

## Import and synchronization

```bash
python scripts/import_sound_pack.py sounds/inbox \
  --metadata-csv audio_sources.csv \
  --generate-credits
python scripts/sync_release_data.py --check
node scripts/release-audit.mjs --source
```

`--set-defaults` requires at least eight imported files and updates `recommended`/`status` consistently. Human listening is still required before treating that edit as a release decision.

Radio remains separate under `sounds/radio/`.
