# Nocturne v0.1.0-alpha.7 Patch Notes

This patch responds to first hands-on listening feedback from alpha.6.

## Product/UX fixes

- Removed stale fallback CC0 placeholder entries from the built-in frontend fallback library. These were the old `gentle-rain-cc0`, `rain-on-window-cc0`, etc. entries that appeared as missing picker options.
- Added explicit sound-source filtering in the sound picker:
  - **recorded** = bundled Freesound CC0 recordings in `sounds/library/`
  - **generated** = procedural starter beds created by `scripts/generate_noise.py` during install
- Added a **preview** button in the sound picker so sounds can be auditioned before assigning them to a mixer slot.
- Updated picker rows to show source type (`Recorded CC0` or `Generated`) alongside category and visual theme.

## Sound-pack fixes

- Removed `thunderstorm-rainstorm` from the bundled app/library because auditioning showed it did not match its label/use case well enough for a sleep-app alpha.
- Loudness-normalized remaining bundled CC0 MP3 files and stripped embedded metadata again after processing.
- Later alpha.8 provenance correction: `soft-wind-trees` was removed/quarantined because the bundled local audio did not audibly match the cited source. It is no longer an optional public-library sound.
- Renamed generated `Distant Storm Noise` to **Dark Rain Rumble Noise** so the UI no longer implies realistic occasional thunder.
- Renamed generated `Soft Wind Noise` to **Soft Air Noise**.
- Renamed generated `Brown Noise` to **Brown Noise (Deep/Subtle)** and documented that it may be quiet on small speakers.

## Defaults

Default slots now prefer audible recorded loops plus one procedural safety bed:

1. Rain on Open Window
2. Indoor Raining Loop
3. Heavy Rain on Tent
4. Gentle Rain
5. Fireplace
6. Night Crickets
7. Gentle Waves
8. Pink Noise
