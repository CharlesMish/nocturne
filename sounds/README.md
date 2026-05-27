# sounds/

This folder is for the **Onsen/Sky ambient mixer**.

The current Nocturne UI uses nine styled, hardcoded mixer slots. Drop your real
loop-friendly audio files directly into this folder with these exact filenames:

- `brown-noise.wav`
- `calming_rain.mp3`
- `fireplace.mp3`
- `gentle_rain.mp3`
- `heavy_rain.mp3`
- `heavy_storm.mp3`
- `pinknoise.wav`
- `thunder.mp3`
- `white-noise.wav`

The visible mixer labels are:

- Calming Rain
- Gentle Rain
- Heavy Rain
- Heavy Storm
- Thunder
- Fireplace
- Brown Noise
- Pink Noise
- White Noise

`python scripts/generate_noise.py` creates the procedural WAV beds locally:

- `brown-noise.wav`
- `pinknoise.wav`
- `white-noise.wav`

For rain/fire/thunder MP3 files, copy `media_sources.example.json` to
`media_sources.json`, fill in the source URLs and creator/license notes, then run:

```bash
python scripts/fetch_media.py --yes
```

`python make_test_noise.py` remains available as a quick smoke-test generator for
synthetic placeholder files. It writes WAV files directly and uses `ffmpeg` for
the MP3 slots when `ffmpeg` is installed.

## Radio mode

Radio tracks live in `sounds/radio/`, not here. Radio mode is dynamic: any
`.mp3`, `.ogg`, `.m4a`, `.wav`, `.opus`, `.webm`, or `.flac` file in
`sounds/radio/` appears in the Radio tab after a browser refresh.

## Tips

- OGG/Opus/WebM are often best for seamless loops.
- MP3 is fine for long recordings, but it can have tiny loop seams.
- Aim for 60+ second loops.
- Match loudness across files so slider values feel comparable.
