# Nocturne scripts

## Install and run

```bash
python3 install.py
.venv/bin/python run_nocturne.py
```

The normal installer creates `.venv`, installs the readable direct dependencies
from `requirements.txt` using the known-good versions in `constraints.txt`,
creates local folders/config, and attempts to generate 17 optional procedural
beds at 60 seconds each. Use `--noise-seconds 180` (or another positive value)
for a longer pack, or `--skip-noise` to omit it. Generation failure is nonfatal
and prints an exact retry command because the bundled curated Core Sound Pack
is already usable. Required dependency failures remain fatal. `--skip-deps` is
only for an already prepared `.venv`; the installer checks that environment
before continuing.

The constraints pin the runtime dependency graph tested by this source snapshot.
NumPy uses a Python 3.10-specific pin because newer NumPy releases require
Python 3.11, and platform-only packages retain explicit markers. This is
intentionally not a hash-locked, platform-specific artifact lock: Windows,
macOS, Linux, and Raspberry Pi still select compatible upstream wheels or source
distributions. A future packaging pass can publish per-platform hashed locks
once those targets are exercised in CI or on hardware.

## Release integrity

| Purpose | Command |
|---|---|
| Synchronize/check embedded catalog and build fallbacks | `python3 scripts/sync_release_data.py` / `.venv/bin/python scripts/sync_release_data.py --check` |
| Validate a source archive | `.venv/bin/python check_audio_contract.py --source` |
| Audit a source archive | `node scripts/release-audit.mjs --source` |
| Exercise live FastAPI routes without persistent state | `.venv/bin/python scripts/runtime_smoke.py` |
| Exercise installer outcomes without rebuilding a venv | `.venv/bin/python scripts/installer_smoke.py` |
| Exercise catalog/CSV/release containment | `.venv/bin/python scripts/path_safety_smoke.py` |
| Verify selections, manifests, audit stability, ZIP modes, and launcher endings | `.venv/bin/python scripts/release_builder_smoke.py` |
| Compile all Python source | `.venv/bin/python -m compileall -q .` |
| Exercise both UI profiles and capture screenshots (QA-only dependencies) | `.venv/bin/python scripts/browser_smoke.py --profile nocturne` and `--profile nocturne-pi` |
| Require all locally generated WAVs | `.venv/bin/python check_audio_contract.py --installed` and `node scripts/release-audit.mjs --installed` |
| Stamp a source/archive build | `.venv/bin/python scripts/stamp_build.py --version 0.1.0-alpha.N --revision <label>` |

The release audit prints JSON to stdout and does not mutate the repository.
Write a retained report only when requested explicitly, for example:

```bash
node scripts/release-audit.mjs --source \
  --report verification-artifacts/release-audit.json
```

`browser_smoke.py` requires Python Playwright and Chromium, but neither is a
Nocturne runtime dependency. It honors `--chromium` and `CHROMIUM_BIN`, searches
the ordinary executable path, then uses Playwright's installed Chromium. Install
that QA-only browser with `.venv/bin/python -m playwright install chromium`
when needed. Both profiles are expected before a UI-release completion claim
when the browser is available; otherwise record `NOT RUN`. This harness is not
real Windows, Raspberry Pi, screen-reader, lock/background, listening-comfort,
or overnight evidence.

## Audio tools

| Purpose | Command |
|---|---|
| Generate procedural beds (60 seconds each by default) | `.venv/bin/python scripts/generate_noise.py` |
| Bake a traceable cyclic-crossfade candidate | `.venv/bin/python scripts/bake_seamless_loop.py INPUT OUTPUT --crossfade-seconds 6` |
| Split product and evidence archives | `.venv/bin/python scripts/make_release.py --output-dir ... --product-name ... --evidence-name ...` |
| Import curated CC0/user-owned sounds | `.venv/bin/python scripts/import_sound_pack.py sounds/inbox --metadata-csv audio_sources.csv --generate-credits` |
| Finalize the known core CSV set | `.venv/bin/python scripts/finalize_core_sound_pack.py --dry-run` before any real run |
| Regenerate audio credit/provenance docs | `.venv/bin/python scripts/write_audio_credits.py` |
| Legacy optional Pixabay compatibility | `.venv/bin/python scripts/fetch_media.py --init` then `.venv/bin/python scripts/fetch_media.py --yes` |

The optional Windows wrapper for that compatibility workflow is deliberately
demoted to `scripts/legacy/Fetch Ambient Media.bat`; it is not part of normal
installation.

Use `docs/FREESOUND_CC0_WORKFLOW.md` for the curation workflow. The legacy fetcher does not manage the assignable sound catalog or Radio tracks.

`make_release.py` excludes generated WAVs, local settings and media, transient
reports, screenshots, logs, and non-public `sounds/inbox/` payloads from the
product ZIP. Detached evidence is selected from canonical catalog metadata, not
whatever happens to be in the inbox. The evidence ZIP can also carry current
verification output and an optional history tree.

## Dual-profile release preparation

```bash
.venv/bin/python scripts/make_dual_release.py \
  --output-dir outputs \
  --release-id <release-id> \
  --evidence-source ../nocturne-evidence-branch
```

This builds `nocturne-*`, `nocturne-pi-*`, and one evidence archive from the
same source identity. The Pi archive omits `static/rain.mp4`; the UI does not
request it after resolving the Pi profile.

## Profile and support checks

```bash
.venv/bin/python scripts/profile_smoke.py
.venv/bin/python scripts/browser_smoke.py --profile nocturne
.venv/bin/python scripts/browser_smoke.py --profile nocturne-pi
.venv/bin/python scripts/support_report.py
```
