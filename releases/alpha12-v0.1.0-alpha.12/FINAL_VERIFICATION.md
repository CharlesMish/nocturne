# Alpha 12 automated verification

Source tag: `v0.1.0-alpha.12`

Source commit: `a650b8d4fc14e643f7a665c060e6c49254c6ceb1`

## Required source suite

The repository virtual environment supplied the Python interpreter because the
host has no `python` alias. Each corresponding AGENTS command passed:

- `scripts/sync_release_data.py --check`;
- `check_audio_contract.py --source`;
- `node scripts/release-audit.mjs --source` (0 errors, 0 warnings);
- `scripts/runtime_smoke.py`;
- `scripts/profile_smoke.py`;
- `scripts/release_builder_smoke.py`;
- `python -m compileall -q .`.

## Browser checks

Chrome for Testing 148.0.7778.96 ran the repository's deterministic Playwright
harness. Source smokes passed for `nocturne` and `nocturne-pi`. Freshly
extracted package smokes also passed for both profiles. The Pi smoke confirmed
that the Pi profile did not request the omitted `static/rain.mp4`.

Each smoke exercised the core-mode hierarchy, packaged identity, device-status
wording, local scene persistence/deletion/error handling, Tonight and
Experimental shelf boundaries, picker focus trapping and focus return, and
desktop/mobile overflow checks. No page or console errors were reported.

## Package integrity

Initial tagged build:

| Archive | Bytes | SHA-256 |
|---|---:|---|
| `nocturne-v0.1.0-alpha.12.zip` | 11,490,420 | `5faf3d22dcc0ea29d6fcf0f97a403c10945922c2c795c8e99031ea4325bb8bd5` |
| `nocturne-pi-v0.1.0-alpha.12.zip` | 8,574,374 | `fa3f94712fc08788a2504511a8e739fa136327ada721981b8a69ab300dde1b36` |

Both product archives and the preliminary evidence archive passed supplied
checksum and ZIP CRC validation. Extracted product manifests matched all 100
ordinary files and all 99 Pi files by size and SHA-256. Both product archives
preserved executable modes for `install.sh` and `Install Nocturne.command`.

The companion evidence archive hash is intentionally published in its adjacent
checksum asset rather than embedded here: embedding an archive's own hash in
the evidence snapshot would be self-referential.
