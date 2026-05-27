#!/usr/bin/env python3
"""
Download Nocturne's optional third-party ambient media from a local manifest.

Why this exists:
  Nocturne is a creative app, but a public source repo that includes raw .mp3
  files can look like a media redistribution channel. This script keeps the
  repo lightweight and lets each installer download the upstream files directly.

Usage:
  1. Copy media_sources.example.json to media_sources.json.
  2. Fill in the direct source/download URLs and creator fields.
  3. Run:
       python scripts/fetch_media.py --yes

The script writes files into sounds/ using the exact filenames the mixer expects
and writes sounds/MEDIA_MANIFEST.generated.json with hashes/provenance receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "media_sources.json"
EXAMPLE_MANIFEST = ROOT / "media_sources.example.json"
SOUNDS_DIR = ROOT / "sounds"
GENERATED_RECEIPTS = SOUNDS_DIR / "MEDIA_MANIFEST.generated.json"

EXPECTED_AMBIENT = {
    "calming_rain.mp3",
    "gentle_rain.mp3",
    "heavy_rain.mp3",
    "heavy_storm.mp3",
    "thunder.mp3",
    "fireplace.mp3",
}

USER_AGENT = "Nocturne/0.1 (+https://github.com/CharlesMish/nocturne)"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    entries = data.get("files")
    if not isinstance(entries, list):
        raise ValueError("manifest must contain a 'files' list")
    return data


def _download(url: str, dest: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        with dest.open("wb") as f:
            shutil.copyfileobj(response, f)


def _entry_status(entry: dict[str, Any]) -> str | None:
    filename = str(entry.get("filename", "")).strip()
    url = str(entry.get("url", "")).strip()
    if not filename:
        return "missing filename"
    if filename not in EXPECTED_AMBIENT:
        return f"unexpected filename {filename!r}"
    if not url or url.startswith("TODO") or "example.com" in url:
        return "missing url"
    return None


def fetch_media(manifest_path: Path, *, yes: bool, overwrite: bool, dry_run: bool) -> int:
    manifest = _load_manifest(manifest_path)
    files = manifest["files"]
    SOUNDS_DIR.mkdir(exist_ok=True)

    valid_entries: list[dict[str, Any]] = []
    skipped: list[tuple[str, str]] = []
    for raw in files:
        if not isinstance(raw, dict):
            skipped.append(("<invalid>", "entry is not an object"))
            continue
        reason = _entry_status(raw)
        filename = str(raw.get("filename", "<unnamed>"))
        if reason:
            skipped.append((filename, reason))
        else:
            valid_entries.append(raw)

    if skipped:
        print("Some manifest entries are incomplete and will be skipped:")
        for filename, reason in skipped:
            print(f"  - {filename}: {reason}")
        print()

    if not valid_entries:
        print("No downloadable media entries found.")
        print(f"Edit {manifest_path.relative_to(ROOT)} with source URLs, then rerun this script.")
        return 2

    print("This will download these optional media files into sounds/:")
    for entry in valid_entries:
        print(f"  - {entry['filename']}  <=  {entry['url']}")
    print()

    if dry_run:
        print("Dry run only; nothing downloaded.")
        return 0

    if not yes:
        reply = input("Continue? [y/N] ").strip().lower()
        if reply not in {"y", "yes"}:
            print("Cancelled.")
            return 1

    receipts: list[dict[str, Any]] = []
    for entry in valid_entries:
        filename = str(entry["filename"])
        url = str(entry["url"])
        dest = SOUNDS_DIR / filename
        if dest.exists() and not overwrite:
            print(f"Keeping existing {filename} (use --overwrite to replace)")
        else:
            print(f"Downloading {filename}…", flush=True)
            with tempfile.NamedTemporaryFile(delete=False, dir=str(SOUNDS_DIR)) as tmp:
                tmp_path = Path(tmp.name)
            try:
                _download(url, tmp_path)
                if tmp_path.stat().st_size == 0:
                    raise RuntimeError("downloaded file is empty")
                tmp_path.replace(dest)
            except Exception:
                tmp_path.unlink(missing_ok=True)
                raise

        receipts.append({
            "filename": filename,
            "url": url,
            "source_page": entry.get("source_page", ""),
            "creator": entry.get("creator", ""),
            "license": entry.get("license", ""),
            "permission_note": entry.get("permission_note", ""),
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "sha256": _sha256(dest),
            "bytes": dest.stat().st_size,
        })

    generated = {
        "generated_by": "scripts/fetch_media.py",
        "manifest": str(manifest_path.relative_to(ROOT)),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": receipts,
    }
    GENERATED_RECEIPTS.write_text(json.dumps(generated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {GENERATED_RECEIPTS.relative_to(ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Download optional Nocturne ambient media.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="media source manifest JSON")
    parser.add_argument("--yes", action="store_true", help="download without interactive confirmation")
    parser.add_argument("--overwrite", action="store_true", help="replace existing files")
    parser.add_argument("--dry-run", action="store_true", help="validate and print planned downloads")
    args = parser.parse_args()

    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = (Path.cwd() / manifest_path).resolve()

    if not manifest_path.exists():
        if EXAMPLE_MANIFEST.exists() and manifest_path == DEFAULT_MANIFEST:
            print(f"No {DEFAULT_MANIFEST.name} found.")
            print(f"Copy {EXAMPLE_MANIFEST.name} to {DEFAULT_MANIFEST.name}, add your source URLs, then rerun:")
            print(f"  cp {EXAMPLE_MANIFEST.name} {DEFAULT_MANIFEST.name}")
            print("  python scripts/fetch_media.py --yes")
            return 2
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    try:
        return fetch_media(manifest_path, yes=args.yes, overwrite=args.overwrite, dry_run=args.dry_run)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
