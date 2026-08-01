#!/usr/bin/env python3
"""
Rename/copy Freesound downloads into Nocturne's sounds/inbox folder.

Typical use from the root of the Nocturne alpha folder:

    python scripts/rename_freesound_downloads.py ~/Downloads

Or, if you keep this file outside the repo:

    python rename_freesound_downloads.py ~/Downloads --project /path/to/nocturne-main-cc0-candidate-alpha5

What it does:
- Reads audio_sources.mainstream_cc0.csv by default.
- Matches Freesound downloads by numeric sound ID, e.g. 518863__idomusics__rain.wav.
- Copies matched files to sounds/inbox/ using Nocturne-friendly filenames.
- If the downloaded extension differs from the CSV filename, it preserves the real extension
  and updates a copy of the CSV so import_sound_pack.py can find the file.
- Never deletes originals unless you pass --move.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from path_safety import ensure_within, require_basename

AUDIO_EXTS = {".wav", ".mp3", ".flac", ".aiff", ".aif", ".ogg", ".m4a"}
DEFAULT_CSV = "audio_sources.mainstream_cc0.csv"

# Fallback mapping from alpha5, used only if the CSV is not found.
FALLBACK_ROWS = [
    ("518863", "rain-balcony-peaceful.wav", "Rain.wav", "idomusics"),
    ("630424", "rain-heavy-open-window.wav", "Rain (Heavy)_From open window.wav", "Mar.Sounds"),
    ("527658", "indoor-raining-loop.wav", "Indoor raining loop", "Rvgerxini"),
    ("484724", "rain-tent-heavy.wav", "Heavy Rain on a tent", "Breviceps"),
    ("519297", "rain-inside-house.wav", "Rain from Inside House.wav", "phillyfan972"),
    ("789162", "rain-city-pooling.wav", "raining in the city - rain pooling up - 1", "FOSSarts"),
    ("650574", "fire-crackling-loop.wav", "fire crackling loop.wav", "soundofsong"),
    ("558967", "campfire-loop-stereo.wav", "Ambiance_Campfire_Loop_Stereo.wav", "Nox_Sound"),
    ("522298", "crickets-at-night-clean.wav", "Crickets At Night - Clean sound", "Defelozedd94"),
    # 751473 / Borgory / "Soft Wind in the Trees - Leaves rustle" is intentionally
    # omitted. The previously bundled local soft-wind-trees.mp3 did not audibly
    # match that cited source and is quarantined as unverified provenance.
    ("857809", "bavaria-meadow-loop.wav", "Bavaria Meadow Loop", "myLoop"),
    ("260263", "waves-on-shore.wav", "WavesOnTheShore.wav", "richardemoore"),
    ("332250", "flowing-water.wav", "Flowing water", "cabled_mess"),
]

@dataclass
class Row:
    sound_id: str
    filename: str
    title: str = ""
    creator: str = ""
    raw: dict[str, str] | None = None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_sound_id(text: str) -> str | None:
    match = re.search(r"/sounds/(\d+)/?", text)
    if match:
        return match.group(1)
    return None


def load_rows(csv_path: Path) -> list[Row]:
    if csv_path.exists():
        rows: list[Row] = []
        with csv_path.open(newline="", encoding="utf-8") as f:
            for raw in csv.DictReader(f):
                source_url = raw.get("source_url", "")
                sound_id = raw.get("sound_id") or extract_sound_id(source_url) or ""
                filename = raw.get("filename", "").strip()
                title = raw.get("title", "").strip() or raw.get("original_title", "").strip()
                creator = raw.get("creator", "").strip()
                if sound_id and filename:
                    filename = require_basename(filename, "CSV filename")
                    rows.append(Row(sound_id=sound_id, filename=filename, title=title, creator=creator, raw=raw))
        if rows:
            return rows
        print(f"Warning: {csv_path} existed, but I could not read usable rows from it.", file=sys.stderr)

    print(f"Note: {csv_path} not found. Using built-in alpha5 mapping.")
    return [Row(sound_id=sid, filename=fn, title=title, creator=creator, raw=None) for sid, fn, title, creator in FALLBACK_ROWS]


def iter_audio_files(root: Path, recursive: bool = True) -> Iterable[Path]:
    globber = root.rglob if recursive else root.glob
    for path in globber("*"):
        if path.is_file() and path.suffix.lower() in AUDIO_EXTS:
            yield ensure_within(root, path, "downloaded audio path")


def score_candidate(path: Path, row: Row) -> int:
    name = path.name.lower()
    stem = path.stem.lower()
    score = 0
    # Freesound usually downloads as 518863__creator__title.wav.
    if re.search(rf"(^|\D){re.escape(row.sound_id)}(\D|$)", name):
        score += 1000
    if row.creator and re.sub(r"\W+", "", row.creator.lower()) in re.sub(r"\W+", "", name):
        score += 100
    row_words = [w for w in re.split(r"[^a-z0-9]+", (row.title + " " + row.filename).lower()) if len(w) >= 4]
    score += 5 * sum(1 for w in set(row_words) if w and w in stem)
    # Prefer original-looking Freesound names over already-renamed Nocturne names.
    if "__" in name:
        score += 25
    return score


def choose_match(files: list[Path], row: Row) -> Path | None:
    scored = [(score_candidate(p, row), p) for p in files]
    scored = [(s, p) for s, p in scored if s > 0]
    if not scored:
        return None
    scored.sort(key=lambda sp: (sp[0], sp[1].stat().st_size), reverse=True)
    return scored[0][1]


def unique_destination(dest_dir: Path, filename: str, overwrite: bool) -> Path:
    filename = require_basename(filename, "destination filename")
    dest = dest_dir / filename
    if overwrite or not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    i = 2
    while True:
        candidate = dest_dir / f"{stem}-{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def rewrite_csv(original_csv: Path, output_csv: Path, filename_updates: dict[str, str], hash_updates: dict[str, str]) -> None:
    if not original_csv.exists():
        return
    with original_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    for field in ["filename", "processed_sha256", "original_sha256"]:
        if field not in fieldnames:
            fieldnames.append(field)

    for row in rows:
        sid = row.get("sound_id") or extract_sound_id(row.get("source_url", "") or "")
        if not sid:
            continue
        if sid in filename_updates:
            row["filename"] = filename_updates[sid]
        if sid in hash_updates:
            # At this stage the copied file is the app-ready file, but also the original download.
            # Keep both populated so provenance docs have a useful checksum immediately.
            row["processed_sha256"] = hash_updates[sid]
            row["original_sha256"] = hash_updates[sid]

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Copy/rename Freesound downloads into Nocturne's sounds/inbox folder.")
    parser.add_argument("downloads", nargs="?", default=str(Path.home() / "Downloads"), help="Folder containing Freesound downloads. Default: ~/Downloads")
    parser.add_argument("--project", default=".", help="Nocturne project root. Default: current folder")
    parser.add_argument("--csv", default=DEFAULT_CSV, help=f"Metadata CSV relative to project root or absolute path. Default: {DEFAULT_CSV}")
    parser.add_argument("--dest", default="sounds/inbox", help="Destination folder relative to project root. Default: sounds/inbox")
    parser.add_argument("--output-csv", default="audio_sources.renamed.csv", help="Updated CSV path relative to project root. Default: audio_sources.renamed.csv")
    parser.add_argument("--no-recursive", action="store_true", help="Do not search downloads recursively")
    parser.add_argument("--move", action="store_true", help="Move instead of copy. Default is copy, safer.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing destination files")
    parser.add_argument("--force-csv-extension", action="store_true", help="Use the exact filename from the CSV even if downloaded extension differs")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen without copying/moving files")
    args = parser.parse_args(argv)

    project = Path(args.project).expanduser().resolve()
    downloads = Path(args.downloads).expanduser().resolve()
    csv_path = Path(args.csv).expanduser()
    if not csv_path.is_absolute():
        csv_path = project / csv_path
    dest_dir = Path(args.dest).expanduser()
    if not dest_dir.is_absolute():
        dest_dir = project / dest_dir
    try:
        dest_dir = ensure_within(project / "sounds" / "inbox", dest_dir, "destination folder")
    except ValueError as exc:
        parser.error(str(exc))
    output_csv = Path(args.output_csv).expanduser()
    if not output_csv.is_absolute():
        output_csv = project / output_csv
    try:
        output_csv = ensure_within(project, output_csv, "output CSV")
    except ValueError as exc:
        parser.error(str(exc))

    if not downloads.exists():
        print(f"Downloads folder not found: {downloads}", file=sys.stderr)
        return 2

    rows = load_rows(csv_path)
    files = list(iter_audio_files(downloads, recursive=not args.no_recursive))
    if not files:
        print(f"No audio files found in {downloads}", file=sys.stderr)
        return 2

    if not args.dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

    matched = []
    missing = []
    used_sources: set[Path] = set()
    filename_updates: dict[str, str] = {}
    hash_updates: dict[str, str] = {}

    print(f"Scanning: {downloads}")
    print(f"Metadata: {csv_path if csv_path.exists() else 'built-in alpha5 mapping'}")
    print(f"Destination: {dest_dir}")
    print()

    for row in rows:
        available = [p for p in files if p not in used_sources]
        source = choose_match(available, row)
        if not source:
            missing.append(row)
            continue

        target_name = row.filename
        if not args.force_csv_extension and source.suffix.lower() != Path(row.filename).suffix.lower():
            target_name = str(Path(row.filename).with_suffix(source.suffix.lower()))

        dest = unique_destination(dest_dir, target_name, overwrite=args.overwrite)
        action = "MOVE" if args.move else "COPY"
        print(f"{action}: {source.name}")
        print(f"   -> {dest.relative_to(project) if dest.is_relative_to(project) else dest}")

        if not args.dry_run:
            if args.move:
                shutil.move(str(source), str(dest))
            else:
                shutil.copy2(source, dest)
            digest = sha256_file(dest)
            hash_updates[row.sound_id] = digest
        else:
            # Hash source in dry run too, useful for confidence.
            hash_updates[row.sound_id] = sha256_file(source)

        filename_updates[row.sound_id] = dest.name
        used_sources.add(source)
        matched.append((row, source, dest))

    print()
    print(f"Matched {len(matched)} of {len(rows)} expected sounds.")
    if missing:
        print("\nMissing / not matched yet:")
        for row in missing:
            print(f"- {row.sound_id}: {row.filename} ({row.creator} — {row.title})")

    if csv_path.exists():
        if args.dry_run:
            print(f"\nDry run: would write updated CSV to {output_csv}")
        else:
            rewrite_csv(csv_path, output_csv, filename_updates, hash_updates)
            print(f"\nWrote updated CSV: {output_csv}")
            print("Next import command:")
            print(f"  python scripts/import_sound_pack.py {dest_dir.relative_to(project) if dest_dir.is_relative_to(project) else dest_dir} --metadata-csv {output_csv.name} --generate-credits")

    return 0 if matched else 1


if __name__ == "__main__":
    raise SystemExit(main())
