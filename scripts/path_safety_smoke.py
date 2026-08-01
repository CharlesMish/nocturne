#!/usr/bin/env python3
"""Traversal and containment regressions for maintenance/release scripts."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import finalize_core_sound_pack as finalize  # noqa: E402
import make_release  # noqa: E402
import rename_freesound_downloads as rename  # noqa: E402
from path_safety import require_basename, resolve_catalog_path, resolve_relative  # noqa: E402


def expect(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def rejected(callable_) -> bool:
    try:
        callable_()
    except ValueError:
        return True
    return False


def main() -> int:
    checks: list[str] = []
    expect(require_basename("rain.wav") == "rain.wav", "valid basename is accepted", checks)
    for value in ("../../escape", "/tmp/escape", r"..\..\escape", ".", ".."):
        expect(rejected(lambda value=value: require_basename(value)), f"unsafe basename is rejected: {value}", checks)

    with tempfile.TemporaryDirectory(prefix="nocturne-path-safety-") as temp:
        root = Path(temp)
        inbox = root / "sounds" / "inbox"
        library = root / "sounds" / "library"
        inbox.mkdir(parents=True)
        library.mkdir(parents=True)
        valid = inbox / "valid.wav"
        valid.write_bytes(b"RIFFfixture")

        contained = resolve_catalog_path(root, "sounds/inbox/valid.wav", inbox, "fixture")
        expect(contained == valid.resolve(), "valid contained catalog path is accepted", checks)
        for value in (
            "../../escape",
            "/tmp/escape",
            r"sounds\inbox\..\..\escape",
            "sounds/inbox/../../escape",
        ):
            expect(
                rejected(lambda value=value: resolve_catalog_path(root, value, inbox, "fixture")),
                f"catalog traversal is rejected: {value}",
                checks,
            )

        expect(
            finalize.candidate_inputs({"filename": "valid.wav"}, inbox) == [valid],
            "finalizer accepts a valid contained inbox filename",
            checks,
        )
        expect(
            rejected(lambda: finalize.candidate_inputs({"filename": "../../escape.wav"}, inbox)),
            "finalizer rejects traversal from CSV filename",
            checks,
        )
        expect(
            rejected(lambda: rename.unique_destination(inbox, "../../escape.wav", False)),
            "renamer rejects traversal in destination filename",
            checks,
        )

        manifest_path = root / "sounds" / "sound_library.json"
        manifest_path.write_text(json.dumps({
            "sounds": [],
            "excluded_sounds": [{
                "id": "valid-quarantine",
                "retention": "evidence_bundle",
                "quarantine_path": "sounds/inbox/valid.wav",
                "file_size_bytes": valid.stat().st_size,
                "sha256": make_release.sha256(valid),
            }],
        }), encoding="utf-8")
        records = make_release.detached_evidence_records(root)
        expect(records[0]["path"] == "sounds/inbox/valid.wav", "valid detached-evidence path remains functional", checks)

        manifest_path.write_text(json.dumps({
            "sounds": [],
            "excluded_sounds": [{
                "id": "escape",
                "retention": "evidence_bundle",
                "quarantine_path": "sounds/inbox/../../escape",
                "file_size_bytes": 1,
                "sha256": "0" * 64,
            }],
        }), encoding="utf-8")
        expect(rejected(lambda: make_release.detached_evidence_records(root)), "release builder rejects prefixed detached-evidence traversal", checks)

        manifest_path.write_text(json.dumps({
            "sounds": [{"availability": "install_generated", "src": "/sounds/../../escape.wav"}],
            "excluded_sounds": [],
        }), encoding="utf-8")
        expect(rejected(lambda: make_release.generated_audio_paths(root)), "release builder rejects generated catalog traversal", checks)
        expect(not (root.parent / "escape").exists(), "traversal fixtures create no escaped file", checks)

    node_probe = subprocess.run(
        [
            "node",
            "--input-type=module",
            "--eval",
            (
                "import {resolveCatalogPath} from './scripts/path_safety.mjs';"
                "import {resolve} from 'node:path';"
                "const root=resolve('.'); const inbox=resolve('sounds/inbox');"
                "const bad=['../../escape','/tmp/escape','sounds/inbox/../../escape','sounds\\\\inbox\\\\..\\\\..\\\\escape'];"
                "if(bad.some(v=>{try{resolveCatalogPath(root,v,inbox,'probe');return true}catch{return false}}))process.exit(1);"
                "resolveCatalogPath(root,'sounds/inbox/README.md',inbox,'probe');"
            ),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    expect(node_probe.returncode == 0, "release-audit JavaScript path guard rejects traversal and accepts a valid inbox path", checks)

    for casing in ("inbox", "Inbox", "INBOX", "iNbOx"):
        first = casing.casefold()
        expect(first == "inbox", f"quarantine casefold covers first-segment variant: {casing}", checks)
    expect("inbox-mixes".casefold() != "inbox", "quarantine casefold does not block unrelated inbox-mixes", checks)

    print(json.dumps({"schema": "nocturne.path-safety-smoke.v1", "overall": "PASS", "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"schema": "nocturne.path-safety-smoke.v1", "overall": "FAIL", "error": str(exc)}, indent=2))
        raise
