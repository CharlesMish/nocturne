# Nocturne Alpha Feedback Notes

Thanks for trying Nocturne. The most useful bug reports include the build label, device/browser, mode, and the smallest steps that reproduce the issue.

## Build identity

The app exposes build information in three places:

- Settings → Build
- the page footer
- `http://127.0.0.1:8000/api/version`

Current packaged alpha label:

```text
v0.1.0-alpha.8-candidate · 2026-06-09 · unknown
```

Before making a new zip from a git checkout, stamp the build metadata:

```bash
python scripts/stamp_build.py --version 0.1.0-alpha.8-candidate
```

That updates `nocturne_build.json` with the version, UTC build time, git commit, and git commit date.

## Feedback template

```text
Build label:
Device / OS:
Browser:
How I launched it: local only / LAN / Pi service
Mode: Onsen / Sky / Radio / Utility / Dashboard / Settings
What I expected:
What happened:
Steps to reproduce:
Screenshots or console errors:
Audio files present? generated noise only / Core Sound Pack / radio tracks added
```

## Things to check first

- Does `python3 install.py` finish even if optional media fetches fail?
- Does the terminal print `Nocturne is ready at http://127.0.0.1:8000/` when launched locally?
- Does Radio show tracks dropped into `sounds/radio/` after a browser refresh?
- Can Onsen/Sky slots open the sound picker, change sounds, and change visual looks?
- Do missing/unavailable sounds show clearly without breaking the mixer?
- Does Settings → Location save and change the Sky weather readout?
