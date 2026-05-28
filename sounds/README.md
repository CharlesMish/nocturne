# sounds/

This folder is for the **Onsen/Sky ambient mixer**.

The current Nocturne UI uses eight styled, hardcoded mixer slots. Drop your real
loop-friendly audio files directly into this folder with these exact filenames:

- `calming_rain.mp3`
- `gentle_rain.mp3`
- `heavy_rain.mp3`
- `rainstorm.mp3`
- `heavy_storm.mp3`
- `thunder.mp3`
- `fireplace.mp3`
- `pinknoise.wav`

The visible mixer labels are:

- Calming Rain
- Gentle Rain
- Heavy Rain
- Rainstorm
- Heavy Storm
- Thunder
- Fireplace
- Pink Noise

`python scripts/generate_noise.py` creates three optional WAV beds locally:

- `brown-noise.wav`
- `pinknoise.wav`
- `white-noise.wav`

Only `pinknoise.wav` is a visible mixer channel in v0.1. Brown and white are
available for manual use or future expansion.

For the seven rain/fire/thunder MP3s the easiest path is:

```bash
cp media_sources.default.json media_sources.json
# (fill the 7 'url' fields with fresh direct CDN links from the Pixabay pages)
python3 install.py --fetch-media
```

After adding/changing any files, run:

```bash
python3 check_audio_contract.py
```

It will show you the exact status of all 8 required mixer channels.

`python3 scripts/generate_noise.py` is available for quick synthetic placeholders.

## Radio mode

Radio tracks live in `sounds/radio/`, not here. Radio mode is dynamic: any
`.mp3`, `.ogg`, `.m4a`, `.wav`, `.opus`, `.webm`, or `.flac` file in
`sounds/radio/` appears in the Radio tab after a browser refresh.

## Tips

- OGG/Opus/WebM are often best for seamless loops.
- MP3 is fine for long recordings, but it can have tiny loop seams.
- Aim for 60+ second loops.
- Match loudness across files so slider values feel comparable.
