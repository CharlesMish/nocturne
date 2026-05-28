# Media licenses and provenance

Nocturne's source repository intentionally does **not** need to include third-party audio binaries.
The app is a creative work, but a public GitHub repository containing raw `.mp3` files can also act like a direct media redistribution channel. To keep the repo clean, use one of these paths:

1. Generate procedural noise locally:

   ```bash
   python scripts/generate_noise.py
   ```

   This creates:

   - `sounds/brown-noise.wav`
   - `sounds/pinknoise.wav`
   - `sounds/white-noise.wav`

2. Download third-party ambient files from source pages chosen by the installer:

   ```bash
   cp media_sources.example.json media_sources.json
   # edit media_sources.json with source URLs / creator notes
   python scripts/fetch_media.py --yes
   ```

   This writes `sounds/MEDIA_MANIFEST.generated.json` with source URLs, creator notes, hashes, byte sizes, and download timestamps.

## Expected ambient filenames

The Nocturne mixer expects these exact filenames in `sounds/`:

- `calming_rain.mp3`
- `gentle_rain.mp3`
- `heavy_rain.mp3`
- `heavy_storm.mp3`
- `thunder.mp3`
- `fireplace.mp3`
- `brown-noise.wav`
- `pinknoise.wav`
- `white-noise.wav`

## Bundled visual media

- `static/rain1.mp4` - TODO: provenance is not documented in this repository.
  Treat this as an unknown-origin bundled media asset and replace it with
  original project footage or a clearly licensed asset before public release.

## Notes for maintainers

For each downloaded file, keep at least:

- source page URL
- direct download URL, if different
- creator name / handle
- license or permission statement
- access/download date
- local filename
- SHA-256 hash

If a source explicitly says "use for any purpose" or similar, quote that in the manifest's `permission_note` field. If a platform license has ambiguous standalone-redistribution language, prefer script-based download over committing the binary file.
