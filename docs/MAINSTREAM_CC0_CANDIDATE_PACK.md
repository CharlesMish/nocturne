# Mainstream CC0 candidate pack

This is a review-first shortlist for Nocturne's bundled sound library. It is
intentionally **not all rain**, but it does lean a little rain-heavy because rain
is central to Nocturne's identity.

No files are bundled from this list yet. Download each candidate manually from
Freesound, verify that the page still says **Creative Commons 0**, screenshot the
page, rename the downloaded file to the `filename` in
`audio_sources.mainstream_cc0.csv`, and import it.

## Proposed default 8

These are the eight I would test first as the public-alpha default mixer. The former `thunder-rain-window-soft.wav` candidate was removed because the original download is far too large for Nocturne's core pack:

1. Gentle Rain — `rain-balcony-peaceful.wav`
2. Rain on Window — `rain-heavy-open-window.wav`
3. Indoor Rain Loop — `indoor-raining-loop.wav`
4. Fireplace — `fire-crackling-loop.wav`
5. Night Crickets — `crickets-at-night-clean.wav`
6. Soft Wind — removed/quarantined; the bundled local `soft-wind-trees.mp3` did not audibly match the previously cited source, so it is not part of the public alpha library.
7. Gentle Waves — `waves-on-shore.wav`
8. Pink Noise — generated locally by `scripts/generate_noise.py`

That gives the first impression a rain-forward sound without making the product
feel like a rain-only app.

## Rain candidates

- **Rain.wav** by `idomusics` — peaceful balcony rain, very popular, likely a strong default gentle-rain sound.
- **Rain (Heavy)_From open window.wav** by `Mar.Sounds` — indoor heavy rain from an open window.
- **Indoor raining loop** by `Rvgerxini` — short loopable indoor rain/drips; good for testing loops.
- **Heavy Rain on a tent** by `Breviceps` — camping/tent texture, nice variety from window rain.
- **Rain from Inside House.wav** by `phillyfan972` — attic/inside-house rain; lower priority, but useful if it auditions well.
- **Thunderstorm and Rainstorm.WAV** by `FreeToUseSounds` — stormier option; only use if it is not too startling.
- **raining in the city - rain pooling up - 1** by `FOSSarts` — short outdoor city/rain texture; likely needs looping/editing.

Removed from this shortlist: `thunder-rain-window-soft.wav` / guidofm, because the source file is roughly 555 MB.

## Non-rain candidates

- **fire crackling loop.wav** by `soundofsong` — soft outdoor fire loop.
- **Ambiance_Campfire_Loop_Stereo.wav** by `Nox_Sound` — clean stereo campfire; compare against soundofsong and keep one.
- **Crickets At Night - Clean sound** by `Defelozedd94` — strong night ambience candidate.
- **Night Ambience** by `parret` — long crickets/insects/night bed; may be too large but likely excellent if trimmed.
- **Soft Wind in the Trees - Leaves rustle** by `Borgory` — removed as an active candidate for the bundled file. The local audio did not audibly match the cited source, so provenance is unverified.
- **Bayerwald Wiesn - Bavaria Meadow** by `myLoop` — meadow/crickets/breeze; verify birds are not too bright for sleep.
- **WavesOnTheShore.wav** by `richardemoore` — gentle lapping water, clean loop candidate.
- **Flowing water** by `cabled_mess` — synthetic flowing water/rain wash; compare against real stream candidates.
- **Underwater Ambience** by `Fission9` — darker/deep ocean tone; optional, moodier than mainstream.
- **Empty Office Space Room Tone with Aircon SFX** by `Soup_UnderScore` — neutral hum/room tone; good for people who like fan/AC sounds.

## Review rules

Reject anything with:

- music or voices;
- obvious birds if the goal is sleep/night;
- sharp thunder cracks or sudden pops;
- audible loops/clicks;
- too much city traffic;
- hiss that becomes tiring after two minutes;
- license mismatch, missing CC0 label, or unclear provenance.

Keep screenshots in `provenance/screenshots/` and original downloads in
`provenance/originals/` if you want a stronger audit trail.

## Import flow

1. Download candidate files from Freesound.
2. Screenshot each sound page after confirming CC0.
3. Rename each downloaded file to the `filename` column in `audio_sources.mainstream_cc0.csv`.
4. Put renamed files in `sounds/inbox/`.
5. Run:

```bash
python scripts/import_sound_pack.py sounds/inbox \
  --metadata-csv audio_sources.mainstream_cc0.csv \
  --generate-credits
```

To make the first eight imported files the mixer defaults:

```bash
python scripts/import_sound_pack.py sounds/inbox \
  --metadata-csv audio_sources.mainstream_cc0.csv \
  --set-defaults \
  --generate-credits \
  --replace
```
