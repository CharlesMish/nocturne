# Sound inbox

Put downloaded candidate audio files here before importing them.

For the mainstream CC0 candidate pack:

1. Open `audio_sources.mainstream_cc0.csv`.
2. Download the Freesound source.
3. Screenshot the Freesound page after confirming Creative Commons 0.
4. Rename the downloaded file to the `filename` value in the CSV.
5. Put the renamed file in this folder.
6. Run:

```bash
python scripts/import_sound_pack.py sounds/inbox \
  --metadata-csv audio_sources.mainstream_cc0.csv \
  --generate-credits
```
