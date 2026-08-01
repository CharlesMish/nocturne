# Nocturne Alpha.13 Hardening Verification Report

## Environment

- Date: 2026-08-01
- Host: Apple Silicon MacBook Air, arm64
- OS: macOS 26.4 (Darwin 25.4.0)
- Prepared interpreter: CPython 3.14.6
- pip: 26.1.1
- Node: 25.8.2
- Browser QA: Playwright 1.61.0 with local Chromium, headless
- Starting revision: `f99a7665b8988b9c03d63b0e1512841a29daa703`
- Verified implementation revision: `c71361f9908f8ec1b7b22b4fc0e0bc8f9458287d`

No real Windows, Raspberry Pi, screen-reader, phone lock/background, listening,
or overnight environment was used. Those results are not inferred from smoke
tests.

## Baseline

Before editing, the working tree was clean. The prepared interpreter produced:

| Command | Result |
|---|---|
| `.venv/bin/python scripts/sync_release_data.py --check` | PASS |
| `.venv/bin/python check_audio_contract.py --source` | PASS |
| `node scripts/release-audit.mjs --source` | PASS — 153 files, 39 audio files, 28 public sounds, 8 defaults, 3 excluded, 0 errors, 0 warnings |
| `.venv/bin/python scripts/runtime_smoke.py` | PASS — 47 checks |
| `.venv/bin/python scripts/profile_smoke.py` | PASS — 13 checks |
| `.venv/bin/python scripts/release_builder_smoke.py` | PASS — 12 checks |
| `.venv/bin/python -m compileall -q .` | PASS |
| both baseline `browser_smoke.py` profiles | NOT RUN — the managed sandbox blocked Chromium startup with `SIGABRT`/`EPERM` before page launch; this was an environment limitation, not recorded as product success or failure |

## Final source checks

| Command | Result |
|---|---|
| `.venv/bin/python scripts/sync_release_data.py --check` | PASS |
| `.venv/bin/python check_audio_contract.py --source` | PASS |
| `node scripts/release-audit.mjs --source --report verification-artifacts/release-audit.json` | PASS — 155 workspace files, 39 local audio files, 28 public sounds, 8 defaults, 3 excluded, 0 errors, 0 warnings; explicit report created |
| `.venv/bin/python scripts/runtime_smoke.py` | PASS — 85 checks |
| `.venv/bin/python scripts/profile_smoke.py` | PASS — 13 checks |
| `.venv/bin/python scripts/installer_smoke.py` | PASS — 21 checks |
| `.venv/bin/python scripts/path_safety_smoke.py` | PASS — 24 checks |
| `.venv/bin/python scripts/release_builder_smoke.py` | PASS — 27 checks |
| `.venv/bin/python -m compileall -q .` | PASS |
| `.venv/bin/python -m py_compile install.py main.py scripts/*.py` | PASS |
| `node --check scripts/release-audit.mjs` | PASS |
| `node --check scripts/path_safety.mjs` | PASS |
| inline JavaScript parse performed by `release-audit.mjs` | PASS — 0 syntax errors |
| `git diff --check` / `git diff --cached --check` | PASS |

The backend has no separate pytest/unittest suite; `runtime_smoke.py` and
`profile_smoke.py` are the existing FastAPI `TestClient` backend coverage.

### Browser and timer coverage

| Command | Result |
|---|---|
| first final-tree `browser_smoke.py --profile nocturne` run | FAIL — the newly added test inspected retained historical mock events instead of only the active schedule; no page/console error was present |
| corrected `.venv/bin/python scripts/browser_smoke.py --profile nocturne` | PASS — 50 checks, 0 console errors, 0 page errors |
| corrected `.venv/bin/python scripts/browser_smoke.py --profile nocturne-pi` | PASS — 39 checks, 0 console errors, 0 page errors |
| post-review `.venv/bin/python scripts/browser_smoke.py --profile nocturne` | PASS — 50 checks, 0 console errors, 0 page errors |
| post-review `.venv/bin/python scripts/browser_smoke.py --profile nocturne-pi` | PASS — 40 checks, including computed static-hero and no-MP4 assertions; 0 console errors, 0 page errors |
| extracted RC `browser_smoke.py --profile nocturne` | PASS — 50 checks |
| extracted RC `browser_smoke.py --profile nocturne-pi` | PASS — 39 checks |
| post-review rebuilt/extracted RC `browser_smoke.py --profile nocturne` | PASS — 50 checks |
| post-review rebuilt/extracted RC `browser_smoke.py --profile nocturne-pi` | PASS — 40 checks, including visible packaged still and no MP4 request |

The deterministic browser clock/audio shim verifies the gain hold/ramp times,
immediate short fade, interval non-interference, cancel/replace cleanup, manual
master rescheduling, visible return before expiry, and completion after expiry.
It does not simulate OS suspension guarantees.

Visual inspection of captured desktop/mobile/profile evidence found the full
profile coherent with no overflow regressions. Post-review inspection confirms
the Pi hero now visibly renders the packaged rain still instead of a plain
black stage.

## Installer and dependency evidence

The deterministic installer smoke covers the 60-second default, explicit
180-second overrides, invalid values, skip messaging, optional generator
failure, and required dependency failure.

A fresh temporary Python 3.14 virtual environment was created and installed
with:

```bash
/tmp/nocturne-alpha13-resolution/bin/python -m pip install \
  -r requirements.txt -c constraints.txt
```

- First sandboxed attempt: FAIL/NOT RUN as a resolution check because DNS access
  to PyPI was blocked; pip had no matching index data.
- Approved network retry: PASS.
- Resolved direct versions: FastAPI 0.136.3, HTTPX 0.28.1, NumPy 2.4.6,
  Uvicorn 0.48.0.

This proves one known-good macOS arm64/Python 3.14 resolution. Platform markers
remain responsible for Windows and Python-version-specific selections; no claim
is made that Windows, Linux, or Raspberry Pi wheels were installed here.

## Real procedural generation and installed checks

The root generated WAVs already existed as ignored local install output before
measurement. The deterministic `--overwrite` pass replaced them with the new
default-duration output.

| Command | Result |
|---|---|
| sandboxed `/usr/bin/time -l .venv/bin/python scripts/generate_noise.py --overwrite` | generation completed, but command status FAIL because the sandbox denied the final `sysctl kern.clockrate` measurement |
| approved `/usr/bin/time -l .venv/bin/python scripts/generate_noise.py --overwrite` | PASS |
| `.venv/bin/python check_audio_contract.py --installed` | PASS |
| `node scripts/release-audit.mjs --installed` | PASS — 0 errors, 0 warnings |

Measured on this host:

- 17 WAV files;
- 60-second requested duration per file (the loop blend shortens payload audio
  slightly as documented by the generator);
- 83,967,148 bytes total (80.08 MiB);
- 4.10 seconds wall time, 3.99 seconds user, 0.08 seconds system;
- 358,039,552 bytes maximum resident set size (about 341.45 MiB);
- 343,638,760-byte macOS peak memory footprint.

These are informational Mac measurements, not Raspberry Pi 3 verification.

## Audit non-mutation, path, and line-ending evidence

`scripts/release_builder_smoke.py` ran the source audit twice. All relevant
fields (mode, overall status, counts, passes, warnings, and errors) were
identical; only the deliberately current `generatedAt` timestamp can differ.
No repository-root `release-audit.json` existed before or after. An explicit
report under `verification-artifacts/` was created only with `--report`.

Path tests rejected `../../escape`, absolute paths, Windows/mixed separators,
and `sounds/inbox/../../escape`; valid basename, catalog, quarantine, and
detached-evidence paths passed. No escaped fixture or residual song staging
directory was found.

All four shipped BAT launchers passed CRLF checks in source and test ZIP
members. `install.sh` and `Install Nocturne.command` passed LF-only source and
ZIP checks. Both Unix launchers retained executable mode `0755` in the ZIP.

## Release artifacts and extracted package

Builder command:

```bash
.venv/bin/python scripts/make_release.py \
  --output-dir dist \
  --product-name NOCTURNE_ALPHA13_HARDENING_RC \
  --evidence-name NOCTURNE_ALPHA13_HARDENING_EVIDENCE
```

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `NOCTURNE_ALPHA13_HARDENING_RC.zip` | 12,102,995 | `72095d33fc136c5d1aeab703d1a331179ae07d86239de12546344307419bcbd9` |
| `NOCTURNE_ALPHA13_HARDENING_EVIDENCE.zip` | 13,258,131 | `31ea7d5b7a2b29c7e42409cf26570932135d45a89df2e48c98db591f5d8f540b` |

- `unzip -t` on both archives: PASS.
- First `shasum -a 256 -c dist/...sha256` invocation from the repository root:
  FAIL because the checksum files intentionally name ZIP basenames and the
  command was run from the wrong directory; no content mismatch occurred.
- Corrected checksum verification from `dist/`: PASS for both archives.
- Canonical `RELEASE_MANIFEST.json`: regenerated by `make_release.py`; 120
  payload records plus the self-excluded manifest, all source sizes/hashes PASS.

The product ZIP was extracted to a fresh `/tmp` directory. Against that
extracted tree, all of these passed:

- synchronized release data check;
- source audio contract;
- source release audit: 121 files, 11 packaged audio files, 17 correctly absent
  install-generated files, 0 errors, 0 warnings;
- runtime smoke (85 checks);
- profile smoke (13 checks);
- installer smoke (21 checks);
- path-safety smoke (24 checks);
- release-builder smoke (27 checks);
- `compileall`;
- both browser profiles (50 and 40 checks after the post-review rebuild).

## Old-version search

The active surfaces named by the release audit contain no stale numbered alpha
reference. Full-tree search leaves exactly:

- `CHANGELOG.md`: the intentional historical predecessor section (sequence 12);
- `scripts/release_builder_smoke.py`: an intentional old-workspace filename
  fixture proving stale archives are excluded from product selection.

## Field-test status

NOT RUN: real Windows batch launch/install, Raspberry Pi 3 install/display and
memory behavior, screen-reader interaction, phone lock/background survival,
bedside listening comfort, loop audition, and overnight survival. The local
browser and Mac measurements must not be substituted for those results.
