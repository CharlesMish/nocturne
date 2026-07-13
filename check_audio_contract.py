#!/usr/bin/env python3
"""Check Nocturne's local audio/catalog contract.

`--source` validates a distributable source archive: bundled defaults must exist,
while deterministic procedural WAVs may be absent because install.py creates them.
`--installed` additionally requires every generated bed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SOUNDS = ROOT / "sounds"
LIBRARY = SOUNDS / "library"
RADIO = SOUNDS / "radio"
MANIFEST = SOUNDS / "sound_library.json"
GENERATOR = ROOT / "scripts" / "generate_noise.py"
AUDIO_EXTS = {".mp3", ".ogg", ".m4a", ".wav", ".opus", ".webm", ".flac"}
VALID_STATUS = {"core", "optional", "experimental"}
VALID_AVAILABILITY = {"bundled", "install_generated"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def public_path(src: str) -> Path | None:
    if not src.startswith("/sounds/"):
        return None
    return ROOT / src.lstrip("/")


def load_manifest() -> dict[str, Any]:
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError("missing sounds/sound_library.json") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid sounds/sound_library.json: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("sounds/sound_library.json must contain an object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--source", action="store_true", help="allow install-generated WAVs to be absent")
    mode.add_argument("--installed", action="store_true", help="require every manifest asset (default)")
    args = parser.parse_args()
    source_mode = args.source

    ok = True
    print(f"Nocturne audio contract ({'source' if source_mode else 'installed'} mode)\n")
    for folder in (SOUNDS, LIBRARY, RADIO):
        if folder.is_dir():
            print(f"✓ folder exists: {folder.relative_to(ROOT)}")
        else:
            print(f"✗ missing folder: {folder.relative_to(ROOT)}")
            ok = False

    try:
        data = load_manifest()
    except ValueError as exc:
        print(f"✗ {exc}")
        return 1

    sounds = data.get("sounds")
    defaults = data.get("default_slots")
    excluded = data.get("excluded_sounds", [])
    if not isinstance(sounds, list) or not sounds:
        print("✗ manifest needs a non-empty sounds[] list")
        sounds = []
        ok = False
    if not isinstance(defaults, list) or len(defaults) != 8 or len(set(defaults)) != 8:
        print("✗ default_slots must contain exactly 8 unique sound ids")
        defaults = []
        ok = False
    else:
        print("✓ default_slots has 8 unique entries")
    if not isinstance(excluded, list):
        print("✗ excluded_sounds must be a list")
        excluded = []
        ok = False

    by_id: dict[str, dict[str, Any]] = {}
    srcs: set[str] = set()
    generator_text = GENERATOR.read_text(encoding="utf-8")
    expected_generated = 0
    print("\nPublic catalog:")
    for raw in sounds:
        if not isinstance(raw, dict):
            print("✗ non-object entry in sounds[]")
            ok = False
            continue
        sid = str(raw.get("id") or "")
        src = str(raw.get("src") or "")
        status = str(raw.get("status") or "")
        availability = str(raw.get("availability") or "")
        if not sid or sid in by_id:
            print(f"✗ missing or duplicate sound id: {sid!r}")
            ok = False
            continue
        by_id[sid] = raw
        if not src.startswith("/sounds/") or src in srcs:
            print(f"✗ invalid or duplicate src for {sid}: {src!r}")
            ok = False
        srcs.add(src)
        if status not in VALID_STATUS:
            print(f"✗ invalid status for {sid}: {status!r}")
            ok = False
        if availability not in VALID_AVAILABILITY:
            print(f"✗ invalid availability for {sid}: {availability!r}")
            ok = False
        if status == "experimental" and (raw.get("recommended") is True or sid in defaults):
            print(f"✗ experimental sound is promoted: {sid}")
            ok = False

        path = public_path(src)
        if availability == "bundled":
            if path is None or not path.is_file() or path.stat().st_size == 0:
                print(f"✗ bundled sound missing/empty: {sid} ({src})")
                ok = False
                continue
            if raw.get("file_size_bytes") != path.stat().st_size:
                print(f"✗ stale size metadata: {sid}")
                ok = False
            if raw.get("sha256") and raw["sha256"] != sha256(path):
                print(f"✗ SHA-256 mismatch: {sid}")
                ok = False
        elif availability == "install_generated":
            filename = Path(src).name
            if filename not in generator_text:
                print(f"✗ generator does not name {filename} ({sid})")
                ok = False
            if path is not None and path.is_file() and path.stat().st_size > 44:
                pass
            elif source_mode:
                expected_generated += 1
            else:
                print(f"✗ missing generated bed: {filename} (run python scripts/generate_noise.py)")
                ok = False

    print("\nTonight defaults:")
    for sid in defaults:
        entry = by_id.get(str(sid))
        if not entry:
            print(f"✗ unknown default id: {sid}")
            ok = False
            continue
        path = public_path(str(entry.get("src") or ""))
        if entry.get("status") != "core" or entry.get("recommended") is not True:
            print(f"✗ default {sid} is not core/recommended")
            ok = False
        elif entry.get("availability") != "bundled":
            print(f"✗ default {sid} is not bundled")
            ok = False
        elif path is None or not path.is_file():
            print(f"✗ default {sid} file missing")
            ok = False
        else:
            print(f"✓ {sid}: {entry.get('src')}")

    print("\nQuarantine boundary:")
    excluded_ids: set[str] = set()
    for raw in excluded:
        if not isinstance(raw, dict):
            print("✗ non-object entry in excluded_sounds[]")
            ok = False
            continue
        sid = str(raw.get("id") or "")
        excluded_ids.add(sid)
        if sid in by_id or sid in defaults or raw.get("status") != "quarantined" or raw.get("public") is not False:
            print(f"✗ quarantine leak or malformed record: {sid}")
            ok = False
        retention = raw.get("retention")
        if retention not in {None, "evidence_bundle"}:
            print(f"✗ unknown quarantine retention profile for {sid}: {retention!r}")
            ok = False
        q = raw.get("quarantine_path")
        if q:
            qpath = ROOT / str(q)
            if not str(q).startswith("sounds/inbox/"):
                print(f"✗ unsafe quarantine path for {sid}: {q}")
                ok = False
            elif qpath.is_file():
                if raw.get("file_size_bytes") not in {None, qpath.stat().st_size}:
                    print(f"✗ stale quarantine size metadata for {sid}")
                    ok = False
                if raw.get("sha256") and raw.get("sha256") != sha256(qpath):
                    print(f"✗ quarantine SHA-256 mismatch for {sid}")
                    ok = False
                print(f"✓ {sid}: denied evidence at {q}")
            elif retention == "evidence_bundle":
                print(f"✓ {sid}: payload detached to the companion evidence bundle ({q})")
            else:
                print(f"✗ missing quarantine evidence for {sid}: {q}")
                ok = False
        else:
            print(f"✓ {sid}: record retained; payload not shipped")
    if "rain-inside-house" not in excluded_ids:
        print("✗ seam-risk rain is absent from excluded_sounds")
        ok = False

    radio_files = [p for p in RADIO.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS] if RADIO.exists() else []
    print(f"\nRadio tracks: {len(radio_files)} file(s) in sounds/radio/")
    if source_mode:
        print(f"Install-generated beds intentionally absent: {expected_generated}")
    print("\nResult:", "PASS" if ok else "NEEDS ATTENTION")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
