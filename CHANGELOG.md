# Changelog

All notable changes to Nocturne will be documented in this file.

## [Unreleased]

- Removed the oversized `thunder-rain-window-soft` CC0 candidate from the mainstream candidate pack.

### Changed
- Nothing yet.

## [v0.1.0-alpha.8] - 2026-06-29

- Removed three questionable optional CC0 candidates (`underwater-ambience`, `aircon-room-tone`, `night-ambience-crickets`) after embedded metadata/duration checks did not match the intended Freesound sources.
- Fixed provenance screenshot references to use the bundled `.jpg` screenshots.
- Stripped embedded metadata from processed Core Sound Pack MP3s and updated hashes/provenance.
- Removed Python bytecode/cache files from the release package.
- Clarified that the legacy Pixabay fetcher is deprecated and explicit-only; normal install uses generated beds plus bundled library sounds.
- Updated generated-media licensing notes for all eight procedural starter beds and clarified that `static/rain.mp4` is not part of the CC0 audio pack.

## [v0.1.0-alpha.5] - 2026-06-09

### Added

- Added `docs/MAINSTREAM_CC0_CANDIDATE_PACK.md` with a rain-skewed but mainstream Freesound CC0 review shortlist.
- Added `audio_sources.mainstream_cc0.csv` as a prefilled metadata sheet for importing reviewed CC0 candidates.
- Added `docs/PROCEDURAL_STARTER_SOUNDS.md` explaining what the generated rain/storm/wind placeholders do and do not claim to be.
- Added inbox/provenance screenshot READMEs for the manual curation workflow.

## [v0.1.0-alpha.4] - 2026-06-09

### Added
- Reworked first-run audio around a generated procedural starter pack: soft rain noise, window rain noise, heavy rain noise, distant storm noise, soft wind noise, pink noise, brown noise, and white noise.
- Added a Freesound/CC0 curation workflow with `docs/FREESOUND_CC0_WORKFLOW.md`, `docs/FREESOUND_RAIN_STARTER.md`, `audio_sources.template.csv`, `sounds/inbox/`, and provenance folders.
- Extended `scripts/import_sound_pack.py` with metadata CSV import, SHA-256 capture, and optional credit/provenance generation.
- Added `scripts/write_audio_credits.py` to regenerate `AUDIO_CREDITS.md` and `AUDIO_PROVENANCE.md` from `sounds/sound_library.json`.

### Changed
- Mixer defaults now point to generated starter sounds instead of missing legacy Pixabay MP3s.
- `check_audio_contract.py` now validates the sound-library manifest and generated starter beds.

## [v0.1.0-alpha.3] - 2026-06-09

### Ambient library
- Reworked the Onsen/Sky mixer into 8 assignable slots backed by `sounds/sound_library.json`.
- Added a sound picker so each mixer slot can choose from a larger local library while keeping only 8 active controls.
- Added per-slot visual look overrides using the existing rain/storm/fire/noise animation themes.
- Added `sounds/library/` as the preferred home for generated or curated Core Sound Pack loops.
- Added `scripts/import_sound_pack.py` to copy a folder of generated audio into `sounds/library/` and update the manifest.

### Documentation
- Added alpha feedback instructions with a copyable build label, `/api/version`, and a `scripts/stamp_build.py` release-stamping helper.
- Clarified where sleeping/ambient mixer files go versus personal radio tracks, including the non-recursive `sounds/` contract.
- Added `scripts/README.md` to explain what works immediately after install versus what requires `fetch_media.py`.
- Added README hero/gallery images so first-time visitors see Nocturne before the setup details.
- Reframed README positioning around the self-hosted LAN use case and clarified what Nocturne is not.
- Moved Settings/location guidance earlier in the README to reduce first-run confusion.
- Added `LAUNCH_CHECKLIST.md` with launch framing, asset checklist, and first-week posting rhythm.

### Radio
- Added two lightweight Radio deck effects: `drift` for slowed playback down to 0.75× with pitch preservation disabled where browsers allow it, and `space` for a short synthetic reverb.
- Kept both new Radio effects neutral by default and persisted their slider values in browser `localStorage`.

### Release polish
- Fixed stale alpha fallback labels in the static HTML and alpha feedback template.
- Re-applied saved Radio warmth when the audio graph is first created, so the slider and sound no longer drift out of sync.
- Added a Python 3.10+ installer guard and created `sounds/library/` during install.
- Added a friendly startup line: `Nocturne is ready at http://127.0.0.1:8000/`.
- Added lower-bound dependency versions in `requirements.txt` for more reliable future installs.
- Renamed shipped static assets from draft-style names to `static/dashboard.html` and `static/rain.mp4`.
- Removed internal fix-log notes from the release artifact; `LAUNCH_CHECKLIST.md` remains as the public launch aid.
- Built release zips cleanly without Python bytecode cache directories.

### Installer / media workflow
- Added `scripts/fetch_media.py --init --open-source-pages` to create `media_sources.json`, list the source pages, and optionally open them.
- Updated Windows media fetcher and install guidance to point to the lower-friction manifest setup flow.
- Renamed manifest instructions from ambiguous `url` to clearer `download_url` while keeping backward compatibility with older `url` manifests.
- Rejected Pixabay source-page URLs before download and added response validation to prevent saving HTML pages as `.mp3` files.
- Updated installer media detection so a source page no longer counts as a usable download URL.
- Improved optional media fetching so Pixabay source pages can be auto-resolved into current CDN MP3 URLs, with manual DevTools capture kept as a fallback.
- Made optional media fetching non-fatal during install, so CDN/markup failures cannot abort the base install.
- Made media downloads continue file-by-file and keep/write receipts for successful downloads even if another optional file fails.
- Expanded Pixabay resolver support to include `/download/audio/` CDN URL forms.
- Fixed Windows `.bat` Python detection when `python` exists but the `py` launcher does not.
- Marked missing mixer audio channels as unavailable in the UI instead of letting them appear active but silent.
- Added macOS launcher guidance for Gatekeeper / execute-bit friction.

## [v0.1.0] - 2026-05

Initial public release.

### Features
- **Five modes** sharing a cohesive bedside aesthetic:
  - Onsen — ambient 8-channel mixer + looping visual
  - Sky — mixer + moon phase + local weather (Open-Meteo)
  - Radio — personal late-night broadcasts from `sounds/radio/`
  - Utility — local Strudel code sketchbook (off by default) with clean handoff to strudel.cc
  - Dashboard — embedded Raspberry Pi terminal / weather screen
- **8-channel ambient mixer contract** (exactly 7 MP3s + pinknoise.wav). Brown and white noise are generated for optional/manual use only.
- **Sky weather** with city search (via Open-Meteo geocode), browser geolocation, or manual coordinates + timezone + temperature unit choice. Location changes invalidate the weather cache.
- **Radio mode** — dynamic listing of any supported audio files dropped into `sounds/radio/`.
- **Utility mode** gated off by default. When disabled, `/api/songs*` routes return 404. Starter sketch is original ("Evening Loop").
- **Strudel handoff** sends *only* the current sketch code via URL hash. All metadata and files stay local on the Nocturne server.
- **Dashboard iframe** is loaded on entry and unloaded to `about:blank` on exit to avoid background CPU/render work.
- **Media provenance model** — no third-party audio binaries are committed to the repository. Optional downloads via `media_sources.json` (or `.default.json`) + `scripts/fetch_media.py`, which records full receipts (hashes, source pages, timestamps) in `sounds/MEDIA_MANIFEST.generated.json`.
- **Local-first / trusted-LAN design** — zero accounts, cloud services, or external authentication. Intended for use on a personal network (Raspberry Pi 5, Mac mini, or desktop). Settings and volumes persist locally.
- **Settings GUI** for enabling/disabling modes and configuring Sky location without editing JSON.
- **Procedural noise** always available (`scripts/generate_noise.py`); pink noise is the default visible channel.
- Cross-platform installers and launchers (Windows .bat, macOS .command, install.sh, systemd unit).

### Documentation
- Clear Quick Start, media fetching instructions, and provenance notes.
- `MEDIA_LICENSES.md`, `sounds/README.md`, and `check_audio_contract.py` all agree on the exact 8-channel contract.

### Constraints honored for v0.1
- No frontend framework rewrite.
- No accounts/cloud/SaaS.
- Third-party MP3s never committed.
- Utility and song-writing surface fully hidden when disabled.

---

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
