#!/usr/bin/env python3
"""Finalize Nocturne's curated CC0 sound pack.

Reads audio_sources.mainstream_cc0.csv, finds matching downloaded files in
sounds/inbox/, optionally transcodes them with ffmpeg, writes finished files to
sounds/library/, updates sounds/sound_library.json, and regenerates
AUDIO_CREDITS.md / AUDIO_PROVENANCE.md.

Typical use from the project root:

  python scripts/finalize_core_sound_pack.py --dry-run
  python scripts/finalize_core_sound_pack.py --transcode mp3 --set-defaults

Requires ffmpeg only when --transcode is not "copy".
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "sounds" / "inbox"
LIBRARY = ROOT / "sounds" / "library"
MANIFEST = ROOT / "sounds" / "sound_library.json"
DEFAULT_CSV = ROOT / "audio_sources.mainstream_cc0.csv"
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".m4a", ".opus", ".webm", ".flac", ".aiff", ".aif"}
PLACEHOLDER_MARKERS = ("TODO: Freesound CC0",)
DEFAULT_SLOT_ORDER = [
    "rain-balcony-peaceful",
    "rain-heavy-open-window",
    "indoor-raining-loop",
    "rain-tent-heavy",
    "fire-crackling-loop",
    "crickets-at-night-clean",
    "waves-on-shore",
    "fan-room-bed",
    "low-rumble-bed",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def save_manifest(data: dict[str, Any]) -> None:
    MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def candidate_inputs(row: dict[str, str], inbox: Path) -> list[Path]:
    filename = row.get("filename", "")
    base = Path(filename).stem
    wanted = []
    if filename:
        wanted.append(inbox / filename)
    wanted.extend(sorted(inbox.glob(base + ".*")))
    # If the Freesound original has a name in the CSV, try that too.
    original = row.get("original_filename", "")
    if original:
        wanted.append(inbox / original)
        wanted.extend(sorted(inbox.glob(Path(original).stem + ".*")))
    seen = []
    for p in wanted:
        if p not in seen and p.exists() and p.is_file() and p.suffix.lower() in AUDIO_EXTS:
            seen.append(p)
    return seen


def destination_for(row: dict[str, str], mode: str, src: Path) -> Path:
    sound_id = row["id"]
    if mode == "copy":
        suffix = src.suffix.lower()
    elif mode == "mp3":
        suffix = ".mp3"
    elif mode == "ogg":
        suffix = ".ogg"
    elif mode == "opus":
        suffix = ".opus"
    else:
        raise ValueError(mode)
    return LIBRARY / f"{sound_id}{suffix}"


def ffmpeg_cmd(src: Path, dest: Path, mode: str, bitrate: str) -> list[str]:
    if mode == "mp3":
        return [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
            "-map_metadata", "-1", "-vn", "-ac", "2", "-ar", "44100", "-b:a", bitrate,
            str(dest),
        ]
    if mode == "ogg":
        return [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
            "-map_metadata", "-1", "-vn", "-ac", "2", "-ar", "44100", "-c:a", "libvorbis", "-q:a", "4",
            str(dest),
        ]
    if mode == "opus":
        return [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
            "-map_metadata", "-1", "-vn", "-ac", "2", "-ar", "48000", "-c:a", "libopus", "-b:a", bitrate,
            str(dest),
        ]
    raise ValueError(mode)


def build_entry(row: dict[str, str], src: Path, dest: Path) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row.get("name") or row["id"].replace("-", " ").title(),
        "category": row.get("category") or "ambient",
        "theme": row.get("theme") or "mist-rain",
        "src": f"/sounds/library/{dest.name}",
        "description": row.get("notes") or "Curated CC0 ambience loop.",
        "source": row.get("source") or "Freesound",
        "source_title": row.get("source_title") or "",
        "creator": row.get("creator") or "",
        "source_url": row.get("source_url") or "",
        "license": row.get("license") or "CC0 1.0",
        "license_url": row.get("license_url") or "https://creativecommons.org/publicdomain/zero/1.0/",
        "license_note": "Curated from Freesound as CC0 1.0; verify page screenshot before public release.",
        "downloaded_at": row.get("downloaded_at") or date.today().isoformat(),
        "screenshot": row.get("screenshot") or "",
        "original_filename": row.get("original_filename") or src.name,
        "processed_filename": dest.name,
        "original_sha256": sha256(src),
        "sha256": sha256(dest),
        "file_size_bytes": dest.stat().st_size,
        "edits": row.get("edits") or "transcoded/normalized for Nocturne pack",
        "notes": row.get("notes") or "",
    }


def finalize(csv_path: Path, inbox: Path, mode: str, bitrate: str, set_defaults: bool, dry_run: bool) -> int:
    rows = [r for r in read_rows(csv_path) if r.get("id") and r.get("filename") and r.get("id") != "id"]
    if not rows:
        print(f"No usable rows in {csv_path}")
        return 1

    data = load_manifest()
    # Remove old placeholder CC0 rows. Keep generated/procedural rows.
    sounds = []
    for s in data.get("sounds", []):
        note = str(s.get("license_note", ""))
        sid = str(s.get("id", ""))
        if sid.endswith("-cc0") or any(marker in note for marker in PLACEHOLDER_MARKERS):
            continue
        sounds.append(s)
    by_id = {str(s.get("id")): s for s in sounds if isinstance(s, dict) and s.get("id")}

    imported: list[str] = []
    missing: list[str] = []
    if not dry_run:
        LIBRARY.mkdir(parents=True, exist_ok=True)

    for row in rows:
        matches = candidate_inputs(row, inbox)
        if not matches:
            missing.append(row["filename"])
            continue
        src = matches[0]
        dest = destination_for(row, mode, src)
        print(f"{row['id']}: {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")
        if not dry_run:
            if mode == "copy":
                shutil.copy2(src, dest)
            else:
                if not shutil.which("ffmpeg"):
                    print("ERROR: ffmpeg is required for transcoding. Install ffmpeg or use --transcode copy.", file=sys.stderr)
                    return 2
                subprocess.run(ffmpeg_cmd(src, dest, mode, bitrate), check=True)
            by_id[row["id"]] = build_entry(row, src, dest)
            imported.append(row["id"])
        else:
            imported.append(row["id"])

    if dry_run:
        print(f"\nWould import {len(imported)} sounds. Missing {len(missing)}.")
        if missing:
            print("Missing files:")
            for m in missing:
                print(f"  - {m}")
        return 0 if imported else 1

    data["sounds"] = list(by_id.values())
    if set_defaults:
        available = {s.get("id") for s in data["sounds"]}
        defaults = [sid for sid in DEFAULT_SLOT_ORDER if sid in available]
        # Fill to 8 with any imported sounds, then procedural fallbacks.
        for sid in imported + ["soft-rain-noise", "brown-noise", "white-noise"]:
            if len(defaults) >= 8:
                break
            if sid in available and sid not in defaults:
                defaults.append(sid)
        data["default_slots"] = defaults[:8]
    save_manifest(data)

    sys.path.insert(0, str((ROOT / "scripts").resolve()))
    from write_audio_credits import write_audio_docs
    write_audio_docs(ROOT)

    print(f"\nImported {len(imported)} sounds into sounds/library/.")
    if missing:
        print(f"Skipped {len(missing)} missing files:")
        for m in missing:
            print(f"  - {m}")
    print("Wrote sounds/sound_library.json, AUDIO_CREDITS.md, AUDIO_PROVENANCE.md")
    return 0 if imported else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize Nocturne's curated CC0 Core Sound Pack.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="metadata CSV, default audio_sources.mainstream_cc0.csv")
    parser.add_argument("--inbox", type=Path, default=INBOX, help="folder with renamed/downloaded candidates")
    parser.add_argument("--transcode", choices=["mp3", "ogg", "opus", "copy"], default="mp3", help="output format; mp3 is safest across browsers")
    parser.add_argument("--bitrate", default="128k", help="audio bitrate for mp3/opus, default 128k")
    parser.add_argument("--set-defaults", action="store_true", help="set default 8 mixer slots from imported pack")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen without writing files")
    args = parser.parse_args()
    return finalize(args.csv, args.inbox, args.transcode, args.bitrate, args.set_defaults, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
