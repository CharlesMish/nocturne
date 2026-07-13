# Nocturne scripts

## Install and run

```bash
python3 install.py
.venv/bin/python run_nocturne.py
```

The normal installer creates `.venv`, installs `requirements.txt`, creates local folders/config, and generates the 17 procedural beds. `--skip-deps` is only for an already prepared `.venv`; the installer now checks that environment before continuing.

## Release integrity

| Purpose | Command |
|---|---|
| Synchronize/check embedded catalog and build fallbacks | `python scripts/sync_release_data.py` / `python scripts/sync_release_data.py --check` |
| Validate a source archive | `python check_audio_contract.py --source` |
| Audit a source archive | `node scripts/release-audit.mjs --source` |
| Exercise live FastAPI routes without persistent state | `python scripts/runtime_smoke.py` |
| Verify dirty-tree exclusions, manifests, and ZIP modes | `python scripts/release_builder_smoke.py` |
| Exercise UI hierarchy/focus and capture screenshots (optional QA deps) | `python scripts/browser_smoke.py` |
| Require all locally generated WAVs | `python check_audio_contract.py --installed` and `node scripts/release-audit.mjs --installed` |
| Stamp a source/archive build | `python scripts/stamp_build.py --version 0.1.0-alpha.N --revision <label>` |

`browser_smoke.py` requires Python Playwright and a Chromium executable, but neither is a Nocturne runtime dependency.

## Audio tools

| Purpose | Command |
|---|---|
| Generate procedural beds | `python scripts/generate_noise.py` |
| Bake a traceable cyclic-crossfade candidate | `python scripts/bake_seamless_loop.py INPUT OUTPUT --crossfade-seconds 6` |
| Split product and evidence archives | `python scripts/make_release.py --output-dir ... --product-name ... --evidence-name ...` |
| Import curated CC0/user-owned sounds | `python scripts/import_sound_pack.py sounds/inbox --metadata-csv audio_sources.csv --generate-credits` |
| Finalize the known core CSV set | `python scripts/finalize_core_sound_pack.py --dry-run` before any real run |
| Regenerate audio credit/provenance docs | `python scripts/write_audio_credits.py` |
| Legacy optional Pixabay compatibility | `python scripts/fetch_media.py --init` then `python scripts/fetch_media.py --yes` |

Use `docs/FREESOUND_CC0_WORKFLOW.md` for the curation workflow. The legacy fetcher does not manage the assignable sound catalog or Radio tracks.

`make_release.py` excludes generated WAVs, local settings and media, transient
reports, screenshots, logs, and non-public `sounds/inbox/` payloads from the
product ZIP. Detached evidence is selected from canonical catalog metadata, not
whatever happens to be in the inbox. The evidence ZIP can also carry current
verification output and an optional history tree.

## Dual-profile release preparation

```bash
python scripts/make_dual_release.py \
  --output-dir outputs \
  --release-id v0.1.0-alpha.12 \
  --evidence-source ../nocturne-evidence-branch
```

This builds `nocturne-*`, `nocturne-pi-*`, and one evidence archive from the
same source identity. The Pi archive omits `static/rain.mp4`; the UI does not
request it after resolving the Pi profile.

## Profile and support checks

```bash
python scripts/profile_smoke.py
python scripts/browser_smoke.py --profile nocturne
python scripts/browser_smoke.py --profile nocturne-pi
python scripts/support_report.py
```
