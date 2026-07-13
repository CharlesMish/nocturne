# Media licenses and provenance

Nocturne uses three distinct media classes. They should not be described as interchangeable.

## 1. Bundled recorded ambience

The source archive contains 11 public recordings under `sounds/library/`. Their manifest entries identify Freesound sources verified as CC0 1.0, and the supporting source screenshots and processed-file hashes are retained under `provenance/` and `sounds/sound_library.json`.

Eight of those recordings form the Tonight defaults. Three remain optional. CC0 does not require attribution, but Nocturne records the creator, source page, license, date, screenshot, filenames, edits, size, and SHA-256 where available.

`AUDIO_CREDITS.md` is the readable list. `AUDIO_PROVENANCE.md` is the audit trail.

## 2. Procedural beds generated locally

`python scripts/generate_noise.py` creates 17 WAV beds in `sounds/`. They are deterministic Nocturne synthesis outputs, not field recordings and not third-party CC0 downloads. The source archive intentionally omits those WAVs; `install.py` creates them locally.

The generator uses conservative level limiting and tail/head blending. Those processing operations are implementation facts, not proof of an inaudible seam, sleep safety, or listening comfort. Two thunder beds are marked Experimental and are never Tonight defaults.

## 3. Excluded evidence and quarantine

The public `/sounds` route denies the entire `sounds/inbox/` tree.

- The CC0 `rain-inside-house` payload is retained as non-public evidence because numerical screening found an extreme boundary discontinuity. The canonical review tree uses `sounds/inbox/quarantine-seam-risk/`; the tester ZIP detaches the payload to the companion evidence bundle. Its source/provenance remains recorded, but it is not a playable catalog entry.
- The historical `soft-wind-trees` payload did not match the cited source convincingly. The payload is not shipped; only its exclusion reason and historical hash remain.

Quarantine is not a license judgment and not a listening diagnosis. It is a release boundary pending repair, verification, and human audition.

## Legacy optional Pixabay workflow

The old fixed ambience filenames and `scripts/fetch_media.py` remain for compatibility, but the scraper is not part of the alpha.10 first-run contract. Do not rely on it for a release.

## Bundled visual media

- `static/rain.mp4`
  - Role: Onsen visual loop.
  - Source: project-specific generated visual asset created by Charles Mish using Grok Imagine, from text-to-image followed by image-to-video.
  - Boundary: this file is not part of the Freesound CC0 audio pack. Its reuse follows the project owner's permissions and the applicable tool/platform terms, not CC0.
