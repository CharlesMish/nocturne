# Changelog

All notable changes to Nocturne will be documented in this file.

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
