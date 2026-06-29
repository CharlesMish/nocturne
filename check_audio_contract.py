#!/usr/bin/env python3
"""Check Nocturne's local audio contract.

This is intentionally local-only. It validates the generated starter beds, the
sound library manifest, and the radio folder layout. It does not contact
Freesound/Pixabay/the internet.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOUNDS = ROOT / "sounds"
LIBRARY = SOUNDS / "library"
RADIO = SOUNDS / "radio"
MANIFEST = SOUNDS / "sound_library.json"

REQUIRED_GENERATED = [
    "soft-rain-noise.wav",
    "window-rain-noise.wav",
    "heavy-rain-noise.wav",
    "distant-storm-noise.wav",
    "soft-wind-noise.wav",
    "pinknoise.wav",
    "brown-noise.wav",
    "white-noise.wav",
    # Expanded procedural set (alpha.7)
    "low-rumble-bed.wav",
    "distant-train-bed.wav",
    "soft-traffic-bed.wav",
    "fan-room-bed.wav",
    "rain-on-glass-noise.wav",
    "deep-water-bed.wav",
    "ember-crackle-bed.wav",
    # Thunder audition candidates (alpha.8)
    "distant-thunder-bed.wav",
    "soft-thunderstorm-bed.wav",
]
AUDIO_EXTS = {".mp3", ".ogg", ".m4a", ".wav", ".opus", ".webm", ".flac"}


def main() -> int:
    ok = True
    print("Nocturne audio contract\n")

    for d in (SOUNDS, LIBRARY, RADIO):
        if d.exists() and d.is_dir():
            print(f"✓ folder exists: {d.relative_to(ROOT)}")
        else:
            print(f"✗ missing folder: {d.relative_to(ROOT)}")
            ok = False

    print("\nGenerated starter beds:")
    for name in REQUIRED_GENERATED:
        path = SOUNDS / name
        if path.exists() and path.stat().st_size > 44:
            print(f"✓ {name} ({path.stat().st_size / 1_048_576:.1f} MB)")
        else:
            print(f"✗ missing generated bed: {name}  (run python scripts/generate_noise.py)")
            ok = False

    print("\nSound library manifest:")
    if not MANIFEST.exists():
        print("✗ missing sounds/sound_library.json")
        return 1
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"✗ invalid JSON: {e}")
        return 1

    sounds = data.get("sounds") if isinstance(data, dict) else None
    default_slots = data.get("default_slots") if isinstance(data, dict) else None
    if not isinstance(sounds, list) or not sounds:
        print("✗ manifest needs a non-empty sounds[] list")
        ok = False
        sounds = []
    if not isinstance(default_slots, list) or len(default_slots) != 8:
        print("✗ manifest default_slots must contain exactly 8 sound ids")
        ok = False
        default_slots = []
    else:
        print("✓ default_slots has 8 entries")

    by_id = {s.get("id"): s for s in sounds if isinstance(s, dict)}
    for sid in default_slots:
        entry = by_id.get(sid)
        if not entry:
            print(f"✗ default slot references missing id: {sid}")
            ok = False
            continue
        src = str(entry.get("src") or "")
        if src.startswith("/sounds/"):
            rel = src.removeprefix("/sounds/")
            f = SOUNDS / rel
            if f.exists():
                print(f"✓ default {sid}: {src}")
            else:
                print(f"✗ default {sid} file missing: {src}")
                ok = False

    curated = [s for s in sounds if isinstance(s, dict) and str(s.get("src", "")).startswith("/sounds/library/")]
    print(f"\nCurated library entries: {len(curated)}")
    missing_curated = []
    for s in curated:
        src = str(s.get("src") or "")
        f = SOUNDS / src.removeprefix("/sounds/")
        if src and not f.exists():
            missing_curated.append(src)
    if missing_curated:
        print(f"ℹ {len(missing_curated)} curated placeholders/files are not present yet. That is okay before final curation.")

    radio_files = [p for p in RADIO.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS] if RADIO.exists() else []
    print(f"\nRadio tracks: {len(radio_files)} file(s) in sounds/radio/")

    print("\nResult:", "PASS" if ok else "NEEDS ATTENTION")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
