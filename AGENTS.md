# Nocturne agent guide

Nocturne is a quiet, local-first bedside sound instrument. Preserve one shared
codebase, no accounts/cloud/analytics, honest platform limits, local-only
scenes, and the public quarantine boundary.

## Current architecture

- Profiles: `profiles/nocturne.json` and `profiles/nocturne-pi.json`.
- Packaged default: `nocturne_profile.json`; runtime override:
  `.venv/bin/python run_nocturne.py --profile ...` (or
  `.venv\Scripts\python.exe` on Windows).
- Hosted build and deploy tooling lives in `web/`; the editable shared UI
  remains in `static/`. The hosted target reuses Nocturne's public media and
  provenance and is not another Python runtime profile.
- Local Nocturne and Nocturne Pi product archives intentionally exclude
  `web/`, including generated Worker output. Keep that boundary covered by
  `scripts/release_builder_smoke.py`.
- Deployment mode (server-only versus local display) is not a profile.
- Public source belongs on `main`; detailed release evidence belongs on the
  version-matched `evidence` branch/package.

## Before reporting completion

Run, at minimum:

```bash
.venv/bin/python scripts/sync_release_data.py --check
.venv/bin/python check_audio_contract.py --source
node scripts/release-audit.mjs --source
.venv/bin/python scripts/runtime_smoke.py
.venv/bin/python scripts/profile_smoke.py
.venv/bin/python scripts/installer_smoke.py
.venv/bin/python scripts/path_safety_smoke.py
.venv/bin/python scripts/release_builder_smoke.py
.venv/bin/python -m compileall -q .
```

Before claiming a UI release complete, also run both browser profiles when
Playwright and Chromium are available:

```bash
.venv/bin/python scripts/browser_smoke.py --profile nocturne
.venv/bin/python scripts/browser_smoke.py --profile nocturne-pi
```

Record an unavailable browser as `NOT RUN`, never as `PASS`. Browser automation
does not substitute for real Windows, Raspberry Pi, screen-reader,
lock/background, listening-comfort, or overnight evidence.

Do not claim Raspberry Pi 3, lock-screen, screen-reader, listening comfort, or
overnight behavior was verified unless real target evidence is supplied.

## Hosted web edition

Use Node 22. From the repository root, the complete non-deploying check is:

```bash
cd web
npm ci
npm run check
```

`npm run check` runs the production build, built-asset verifier, and Wrangler
dry run. It does not deploy. Run `npm run deploy` or `npm run deploy:preview`
only with explicit deployment authorization, and never describe a dry run or
uploaded version as live production traffic.

Keep personal Radio files browser-local, preserve the no-account/no-analytics
boundary, and keep media credits and provenance synchronized with the canonical
repository records. Do not edit generated `web/dist/` output as source.
