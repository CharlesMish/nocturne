# Radio tracks

Drop any audio files here (mp3, ogg, m4a, wav, opus, webm, flac) and they will
appear in the **Radio** tab of Nocturne.

These tracks are listed in `/api/radio` and are intentionally kept separate
from the ambient mixer sounds in the parent `sounds/` folder — the mixer's
listing is non-recursive, so files in this subfolder won't pollute the
ambient mixer.

Filenames become track titles: `night-drive.mp3` → "Night Drive".

No restart is required when adding or removing tracks — refresh the browser.
