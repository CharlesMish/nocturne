# sounds/

Drop any `.mp3`, `.ogg`, `.m4a`, `.wav`, `.opus`, `.webm`, or `.flac` file
in here and it'll show up in the app on the next page reload.

The filename (minus the extension) becomes the display name. So:
- `rain-on-tent.mp3` → "Rain On Tent"
- `crackling_fire.ogg` → "Crackling Fire"

## Where to get loop-friendly sounds

- **freesound.org** — huge library, filter by Creative Commons, look for
  files tagged "loop" or "seamless". Search "rain loop", "fire crackle loop", etc.
- **mynoise.net** — has free sample loops you can download.
- **YouTube** — pull audio with `yt-dlp -x --audio-format mp3 <url>`.
  Stick to channels that label loops as seamless.

## Testing without real sounds

Run `python make_test_noise.py` from the project root to generate
brown / pink / white noise samples. They sound rough but they prove
the mixer works.

## Tips

- **OGG/Opus/WebM** are often best for seamless loops. MP3 is fine too,
  especially for long recordings, but some MP3s have tiny loop seams. WAV files are huge.
- **Aim for 60+ second loops** — too short and the seam becomes obvious.
- **Match the loudness** of your files (around -20 LUFS) so volumes
  feel comparable across the mixer.
