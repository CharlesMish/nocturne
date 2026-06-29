# Patch notes for v0.1.0-alpha.7

This release-candidate patch responds to external review of alpha.5.

- Verified that two music-video metadata strings were real embedded metadata in excluded candidate MP3 files.
- Removed `underwater-ambience`, `aircon-room-tone`, and `night-ambience-crickets` from the bundled Core Sound Pack because their embedded metadata/durations did not match the intended Freesound provenance cleanly enough for a public CC0 alpha.
- Kept the strongest 14 Freesound CC0 loops plus the eight generated procedural starter beds.
- Fixed screenshot references from `.png` to bundled `.jpg` files.
- Stripped embedded metadata from all remaining processed MP3 loops and updated SHA-256 hashes.
- Removed Python bytecode/cache files from the release artifact.
- Updated `MEDIA_LICENSES.md` to distinguish CC0 Freesound audio, generated procedural beds, legacy Pixabay compatibility, and the generated `static/rain.mp4` visual.
- Made legacy Pixabay fetching explicit-only in `install.py`; normal install now just builds the local app and generated starter beds.
