# Radio tracks

Drop personal radio files here (mp3, ogg, m4a, wav, opus, webm, flac) and they will
appear in the **Radio** tab of Nocturne.

These tracks are listed in `/api/radio` and are intentionally kept separate
from the ambient mixer sounds in the parent `sounds/` folder — the mixer's
listing is non-recursive, so files in this subfolder won't pollute the
ambient mixer.

Filenames become track titles: `night-drive.mp3` → "Night Drive".

No restart is required when adding or removing tracks — refresh the browser.

## Bedtime stories

Bedtime-story MP3s can use this same folder. Drop the MP3 into `sounds/radio/`,
refresh the browser, and it appears in Radio without code changes.

Track story provenance separately from CC0 ambience. Use honest labels such as
user-authored text and user-owned or user-licensed generated narration. Do not
mark story narration CC0 unless the text, voice/narration output, and license
terms are separately proven.

The optional ambience fetcher does not use this folder. `scripts/fetch_media.py`
is compatibility/archive tooling for the old fixed Onsen/Sky sleep-sound mixer
filenames in the parent `sounds/` folder.

## Radio sound controls

The Radio deck includes four local controls:

- `broadcast` — volume for the radio before master volume.
- `warmth` — lo-fi lowpass filtering.
- `drift` — slowed playback, from 1.00× down to 0.75×. No extra files are needed.
- `space` — subtle generated reverb. No impulse-response file is needed.

The drift/space controls are intentionally part of Radio only. They do not affect the Onsen/Sky ambient mixer library.
