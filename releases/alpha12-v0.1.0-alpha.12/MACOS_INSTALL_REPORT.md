# macOS accelerated install report

Date: 2026-07-12 (America/Chicago)

Artifact: `nocturne-v0.1.0-alpha.12.zip`

SHA-256: `5faf3d22dcc0ea29d6fcf0f97a403c10945922c2c795c8e99031ea4325bb8bd5`

Environment:

- macOS 26.4, build 25E246;
- Python 3.14.3;
- Brave 147.1.89.137 installed;
- Chrome for Testing 148.0.7778.96 used by the deterministic browser smoke.

Observed:

- supplied checksum matched;
- ZIP extracted into a fresh temporary directory;
- `Install Nocturne.command --noise-seconds 1` completed successfully;
- the installer created local configuration and a fresh virtual environment;
- dependencies installed and all 17 procedural generator paths completed;
- the extracted server started at localhost;
- `/health`, `/api/version`, and `/api/profile` returned the expected ordinary
  Nocturne identity and Alpha 12 build;
- the packaged ordinary-profile browser smoke passed with no console or page
  errors.

This was an accelerated installation and functional smoke, not a listening,
playback-duration, full 180-second-bed, screen-reader, lock-screen, or overnight
test. No human audio-quality claim is made.
