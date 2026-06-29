# Nocturne launch checklist

Use this before posting a public repo link.

## Must-do before first post

- [ ] Replace the README hero with the best real photo or browser screenshot you have.
- [ ] Add a short looping GIF/video that switches Onsen → Sky → Radio.
- [ ] Verify `python3 install.py` works from a fresh clone.
- [ ] Verify generated starter beds appear after install and can be assigned through the Onsen/Sky sound picker.
- [ ] Add at least one test file to `sounds/library/`, list/import it in `sounds/sound_library.json`, refresh, and confirm a mixer slot can select it.
- [ ] Test the per-slot visual look selector on rain, storm, fire, and noise themes.
- [ ] Verify `python3 check_audio_contract.py` still explains the legacy fixed-file contract clearly.
- [ ] Drop one supported audio file into `sounds/radio/`, refresh Radio, and test warmth/drift/space at 0% and at tasteful nonzero values.
- [ ] Confirm the README says the preferred release path is a bundled/generated Core Sound Pack, not Pixabay scraping.

## Honest positioning

Use this framing:

> A self-hosted sleep/ambient web app for Raspberry Pi. You run a small Python server on your nightstand, open it from your phone, and own the whole thing.

Avoid these claims:

- “app store app” — it is a self-hosted web app.
- “internet radio” — Radio plays local files from `sounds/radio/`.
- “offline-first” — it is offline-tolerant after first load; Sky/Dashboard weather depends on Open-Meteo when available.
- “music production tool” — Utility is a local Strudel sketchbook and handoff, not built-in Strudel playback.
- “finished product” — keep the v0.1 framing.

## First-week posting rhythm

1. **Launch evening:** personal post with the best Sky/phone image.
2. **Next day:** short aesthetic post with the GIF or Radio tape-deck visual.
3. **Day 3:** practical/dev post about the architecture: one HTML file, one FastAPI file, no build step, no database, no accounts.
4. **Days 4–5:** reply to genuine responses; do not carpet-bomb related threads.
5. **Day 6–7:** one follow-up about a specific craft detail or what you learned.

No hashtags. No “please RT.” Reply like a human at a meetup, not a billboard.

## CC0 sound-pack checks

- [ ] For every bundled non-generated sound, confirm `sounds/sound_library.json` has creator, source URL, license, screenshot, hash, and edit notes.
- [ ] Regenerate `AUDIO_CREDITS.md` and `AUDIO_PROVENANCE.md` with `python scripts/write_audio_credits.py`.
- [ ] Audition all default rain slots for voices, music, sudden transients, loop seams, and harsh high-frequency buildup.
