# Nocturne CC0 candidate download checklist

Patched: removed `thunder-rain-window-soft.wav` because the source file is too large for the core pack.

Download the original file from each Freesound page while logged in, then screenshot the page showing title, creator, and CC0 license.

## Rain / storm bias

- [ ] rain-balcony-peaceful.wav — Rain.wav — idomusics — https://freesound.org/people/idomusics/sounds/518863/
- [ ] rain-heavy-open-window.wav — Rain (Heavy)_From open window.wav — Mar.Sounds — https://freesound.org/people/Mar.Sounds/sounds/630424/
- [ ] indoor-raining-loop.wav — Indoor raining loop — Rvgerxini — https://freesound.org/people/Rvgerxini/sounds/527658/
- [ ] rain-tent-heavy.wav — Heavy Rain on a tent — Breviceps — https://freesound.org/people/Breviceps/sounds/484724/
- [ ] rain-inside-house.wav — Rain from Inside House.wav — phillyfan972 — https://freesound.org/people/phillyfan972/sounds/519297/
- [ ] rain-city-pooling.wav — raining in the city - rain pooling up - 1 — FOSSarts — https://freesound.org/people/FOSSarts/sounds/789162/

## Fire

- [ ] fire-crackling-loop.wav — fire crackling loop.wav — soundofsong — https://freesound.org/people/soundofsong/sounds/650574/
- [ ] campfire-loop-stereo.wav — Ambiance_Campfire_Loop_Stereo.wav — Nox_Sound — https://freesound.org/people/Nox_Sound/sounds/558967/

## Night / nature

- [ ] crickets-at-night-clean.wav — Crickets At Night - Clean sound — Defelozedd94 — https://freesound.org/people/Defelozedd94/sounds/522298/
- [x] soft-wind-trees.wav — removed/quarantined from the public library. The bundled local audio did not audibly match the previously cited Borgory/Freesound source, so provenance is unverified and no CC0 claim should be made for the local file.
- [ ] bavaria-meadow-loop.wav — Bavaria Meadow Loop — myLoop — https://freesound.org/people/myLoop/sounds/857809/

## Water / room tone

- [ ] waves-on-shore.wav — WavesOnTheShore.wav — richardemoore — https://freesound.org/people/richardemoore/sounds/260263/
- [ ] flowing-water.wav — Flowing water — cabled_mess — https://freesound.org/people/cabled_mess/sounds/332250/

## After downloading

From the Nocturne project root:

```bash
python scripts/rename_freesound_downloads.py ~/Downloads --dry-run
python scripts/rename_freesound_downloads.py ~/Downloads
python scripts/import_sound_pack.py sounds/inbox --metadata-csv audio_sources.renamed.csv --generate-credits
```
