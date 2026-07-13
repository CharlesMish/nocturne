# Nocturne agent guide

Nocturne is a quiet, local-first bedside sound instrument. Preserve one shared
codebase, no accounts/cloud/analytics, honest platform limits, local-only
scenes, and the public quarantine boundary.

## Current architecture

- Profiles: `profiles/nocturne.json` and `profiles/nocturne-pi.json`.
- Packaged default: `nocturne_profile.json`; runtime override:
  `python run_nocturne.py --profile ...`.
- Deployment mode (server-only versus local display) is not a profile.
- Public source belongs on `main`; detailed release evidence belongs on the
  version-matched `evidence` branch/package.

## Before reporting completion

Run, at minimum:

```bash
python scripts/sync_release_data.py --check
python check_audio_contract.py --source
node scripts/release-audit.mjs --source
python scripts/runtime_smoke.py
python scripts/profile_smoke.py
python scripts/release_builder_smoke.py
python -m compileall -q .
```

Do not claim Raspberry Pi 3, lock-screen, screen-reader, listening comfort, or
overnight behavior was verified unless real target evidence is supplied.
