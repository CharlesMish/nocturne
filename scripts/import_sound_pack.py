#!/usr/bin/env python3
"""Import ambience loops into Nocturne's local sound library.

Quick import:
  python scripts/import_sound_pack.py ~/Downloads/nocturne-cc0-candidates --set-defaults

Curation import with metadata:
  python scripts/import_sound_pack.py sounds/inbox --metadata-csv audio_sources.csv --generate-credits

The script copies supported audio files into sounds/library/, upserts entries in
sounds/sound_library.json, records hashes, and can regenerate AUDIO_CREDITS.md /
AUDIO_PROVENANCE.md. It does not transcode, trim, or normalize files; do that
before import if needed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LIBRARY_DIR = ROOT / "sounds" / "library"
MANIFEST = ROOT / "sounds" / "sound_library.json"
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".m4a", ".opus", ".webm", ".flac"}

THEMES = {
    "mist-rain", "garden-rain", "distant-storm", "mountain-storm",
    "squall", "tempest", "hearth", "ember-noise",
}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "sound"


def titleize(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.replace("_", "-").split("-") if part)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def infer_category_and_theme(slug: str) -> tuple[str, str]:
    s = slug.lower()
    if any(k in s for k in ("fire", "hearth", "campfire", "stove", "ember")):
        return "fire", "hearth"
    if any(k in s for k in ("thunder", "storm", "tempest", "squall")):
        return "storm", "tempest"
    if any(k in s for k in ("rain", "drizzle", "window", "tent", "leaf", "leaves", "roof")):
        return "rain", "garden-rain"
    if any(k in s for k in ("wind", "breeze")):
        return "wind", "mist-rain"
    if any(k in s for k in ("cricket", "frog", "night", "forest")):
        return "night", "distant-storm"
    if any(k in s for k in ("stream", "river", "creek", "ocean", "wave", "water")):
        return "water", "garden-rain"
    if any(k in s for k in ("noise", "fan", "hum", "brown", "pink", "white")):
        return "noise", "ember-noise"
    return "ambient", "mist-rain"


def load_manifest() -> dict[str, Any]:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"version": 5, "default_slots": [], "excluded_sounds": [], "sounds": []}


def save_manifest(data: dict[str, Any]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    data["version"] = max(5, int(data.get("version") or 5))
    MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_metadata_csv(path: Path | None) -> dict[str, dict[str, str]]:
    if not path:
        return {}
    if not path.exists():
        raise SystemExit(f"metadata CSV not found: {path}")
    rows: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row.get("filename") or row.get("original_filename") or "").strip()
            if not key:
                continue
            rows[key] = {k: (v or "").strip() for k, v in row.items()}
    return rows


def apply_metadata(entry: dict[str, Any], meta: dict[str, str], src_file: Path, dest_file: Path) -> None:
    if not meta:
        return
    if meta.get("id"):
        entry["id"] = slugify(meta["id"])
    if meta.get("name"):
        entry["name"] = meta["name"]
    if meta.get("category"):
        entry["category"] = meta["category"]
    if meta.get("theme") in THEMES:
        entry["theme"] = meta["theme"]
    for key in (
        "description", "source", "source_title", "creator", "source_url", "license",
        "license_url", "downloaded_at", "screenshot", "original_filename", "edits", "notes",
        "prompt", "license_note"
    ):
        val = meta.get(key)
        if val:
            entry[key] = val
    entry.setdefault("original_filename", src_file.name)


def import_files(source_dir: Path, *, set_defaults: bool, replace: bool, dry_run: bool,
                 metadata_csv: Path | None, generate_credits: bool) -> int:
    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"Input folder not found: {source_dir}")

    files = sorted(p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS)
    if not files:
        print(f"No supported audio files found in {source_dir}")
        return 1

    if set_defaults and len(files) < 8:
        raise SystemExit("--set-defaults requires at least eight supported audio files")

    metadata = load_metadata_csv(metadata_csv)
    data = load_manifest()
    sounds = data.setdefault("sounds", [])
    by_id = {str(s.get("id")): s for s in sounds if isinstance(s, dict) and s.get("id")}
    imported_ids: list[str] = []

    if not dry_run:
        LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

    for src in files:
        meta = metadata.get(src.name, {})
        base_slug = slugify(meta.get("id") or meta.get("name") or src.stem)
        sound_id = base_slug
        dest = LIBRARY_DIR / f"{sound_id}{src.suffix.lower()}"
        n = 2
        while dest.exists() and not replace and dest.resolve() != src.resolve():
            sound_id = f"{base_slug}-{n}"
            dest = LIBRARY_DIR / f"{sound_id}{src.suffix.lower()}"
            n += 1

        category, theme = infer_category_and_theme(sound_id)
        entry = by_id.get(sound_id, {})
        entry.update({
            "id": sound_id,
            "name": entry.get("name") or titleize(sound_id),
            "category": entry.get("category") or category,
            "theme": entry.get("theme") if entry.get("theme") in THEMES else theme,
            "src": f"/sounds/library/{dest.name}",
            "source_type": entry.get("source_type") or "recorded_cc0",
            "source_label": entry.get("source_label") or "Recorded / local",
            "availability": "bundled",
            "status": entry.get("status") or "optional",
            "recommended": bool(entry.get("recommended", False)),
            "license_note": entry.get("license_note") or "User-provided. Fill in source and license details before release.",
        })
        apply_metadata(entry, meta, src, dest)
        if entry.get("theme") not in THEMES:
            entry["theme"] = theme
        entry["src"] = f"/sounds/library/{dest.name}"
        entry["sha256"] = sha256(src)
        entry["file_size_bytes"] = src.stat().st_size
        entry.setdefault("downloaded_at", date.today().isoformat())
        if entry not in sounds:
            sounds.append(entry)
        by_id[sound_id] = entry
        imported_ids.append(sound_id)

        action = "would copy" if dry_run else "copying"
        print(f"{action}: {src.name} -> sounds/library/{dest.name} [{entry['category']} / {entry['theme']}]")
        if not dry_run:
            shutil.copy2(src, dest)

    if set_defaults:
        data["default_slots"] = imported_ids[:8]
        selected = set(data["default_slots"] )
        for sound in sounds:
            if not isinstance(sound, dict):
                continue
            sound["recommended"] = str(sound.get("id")) in selected
            if sound.get("status") != "experimental":
                sound["status"] = "core" if sound["recommended"] else "optional"
        print("default_slots set to:", ", ".join(data["default_slots"]))

    if not dry_run:
        max_order = 0
        for index, sound in enumerate(sounds, start=1):
            if not isinstance(sound, dict):
                continue
            order = sound.get("sort_order")
            if not isinstance(order, int):
                order = index * 10
                sound["sort_order"] = order
            max_order = max(max_order, order)
        save_manifest(data)
        print(f"Updated {MANIFEST.relative_to(ROOT)}")
        subprocess.run([sys.executable, ROOT / "scripts" / "sync_release_data.py"], check=True, cwd=ROOT)
        if generate_credits:
            from write_audio_credits import write_audio_docs
            write_audio_docs(ROOT)
    else:
        print("Dry run only; no files changed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Import ambience loops into sounds/library/ and sound_library.json.")
    parser.add_argument("folder", type=Path, help="folder containing mp3/wav/ogg/m4a/opus/webm/flac files")
    parser.add_argument("--set-defaults", action="store_true", help="make the first 8 imported sounds the mixer default slots")
    parser.add_argument("--replace", action="store_true", help="replace existing files with the same slug instead of creating -2 copies")
    parser.add_argument("--metadata-csv", type=Path, help="CSV with filename,id,name,category,theme,source_url,creator,license,screenshot,etc.")
    parser.add_argument("--generate-credits", action="store_true", help="regenerate AUDIO_CREDITS.md and AUDIO_PROVENANCE.md after import")
    parser.add_argument("--dry-run", action="store_true", help="print actions without copying or writing the manifest")
    args = parser.parse_args()
    return import_files(
        args.folder,
        set_defaults=args.set_defaults,
        replace=args.replace,
        dry_run=args.dry_run,
        metadata_csv=args.metadata_csv,
        generate_credits=args.generate_credits,
    )


if __name__ == "__main__":
    raise SystemExit(main())
