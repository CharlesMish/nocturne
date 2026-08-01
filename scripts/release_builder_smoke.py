#!/usr/bin/env python3
"""Regression checks for dirty-tree release selection and ZIP permissions."""
from __future__ import annotations

import json
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import make_release as release  # noqa: E402


def expect(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def write(path: Path, content: str = "fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def fixture_selection(checks: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="nocturne-release-policy-") as temp:
        root = Path(temp)
        write(root / "sounds/sound_library.json", json.dumps({"sounds": [], "excluded_sounds": []}))
        allowed = {
            "README.md",
            "config/.gitkeep",
            "config/nocturne.example.json",
            "sounds/radio/README.md",
            "sounds/inbox/quarantine/README.md",
            "songs/evening-loop/code.js",
        }
        forbidden = {
            "workspace.zip",
            "workspace.zip.sha256",
            "scratch.wav",
            "config/nocturne.json",
            "config/private.json",
            "media_sources.json",
            "sounds/MEDIA_MANIFEST.generated.json",
            "sounds/radio/personal.wav",
            "sounds/inbox/quarantine/candidate.mp3",
            "songs/my-private-sketch/code.js",
            "provenance/originals/source.wav",
            "provenance/screenshots/source.jpg",
            "review_bundles/old-review.md",
            "IMPLEMENTATION_REPORT.md",
            "VERIFICATION_REPORT.md",
            "CHANGE_SUMMARY.md",
            "NOCTURNE_ALPHA13_HARDENING.patch",
        }
        for rel in allowed | forbidden:
            write(root / rel)
        selected = {path.relative_to(root).as_posix() for path in release.product_files(root)}
        expect(allowed <= selected, "release policy keeps canonical files in mutable directories", checks)
        expect(not forbidden & selected, "release policy rejects dirty-workspace fixtures", checks)


def actual_tree_selection(checks: list[str]) -> None:
    selected = {path.relative_to(ROOT).as_posix() for path in release.product_files(ROOT)}
    forbidden = {
        "A_distant_thunder.wav",
        "B_soft_thunderstorm.wav",
        "config/nocturne.json",
        "nocturne-alpha12-codex-workspace-v0.4.0-dev.zip",
        "nocturne-alpha8-generated-candidate.zip",
        "sounds/radio/aster.wav",
    }
    expect(not forbidden & selected, "live workspace junk is excluded from product selection", checks)
    required = {
        "Install Nocturne.command",
        "install.sh",
        "sounds/radio/README.md",
        "sounds/inbox/quarantine-seam-risk/README.md",
        "sounds/inbox/quarantine-unverified/README.md",
        "sounds/inbox/seam-baked/README.md",
    }
    expect(required <= selected, "required installers and boundary guides remain selected", checks)

    manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    manifest_paths = {record["path"] for record in manifest.get("files", [])}
    expect(selected - {"RELEASE_MANIFEST.json"} == manifest_paths, "source manifest paths match live product selection", checks)
    bad_sizes: list[str] = []
    bad_hashes: list[str] = []
    for record in manifest.get("files", []):
        path = ROOT / record["path"]
        if path.stat().st_size != record["size_bytes"]:
            bad_sizes.append(record["path"])
        if release.sha256(path) != record["sha256"]:
            bad_hashes.append(record["path"])
    expect(not bad_sizes, f"all source manifest sizes match: {bad_sizes}", checks)
    expect(not bad_hashes, f"all source manifest hashes match: {bad_hashes}", checks)
    expect(manifest.get("detached_evidence") == release.detached_evidence_records(ROOT), "detached evidence is catalog-driven", checks)


def executable_modes(checks: list[str]) -> None:
    installers = [ROOT / "install.sh", ROOT / "Install Nocturne.command"]
    for path in installers:
        expect(bool(path.stat().st_mode & stat.S_IXUSR), f"source installer is executable: {path.name}", checks)
    with tempfile.TemporaryDirectory(prefix="nocturne-release-modes-") as temp:
        archive_path = Path(temp) / "modes.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            for path in installers:
                release.write_member(archive, path, path.name, (2026, 1, 1, 0, 0, 0))
        with zipfile.ZipFile(archive_path) as archive:
            for path in installers:
                mode = (archive.getinfo(path.name).external_attr >> 16) & 0o777
                expect(mode == 0o755, f"ZIP preserves executable mode for {path.name}", checks)


def has_only_crlf(data: bytes) -> bool:
    return b"\n" in data and data.replace(b"\r\n", b"").find(b"\n") < 0


def launcher_line_endings(checks: list[str]) -> None:
    windows = [
        ROOT / "Install Nocturne.bat",
        ROOT / "Start Nocturne.bat",
        ROOT / "Start Nocturne LAN.bat",
        ROOT / "scripts/legacy/Fetch Ambient Media.bat",
    ]
    unix = [ROOT / "install.sh", ROOT / "Install Nocturne.command"]
    for path in windows:
        expect(has_only_crlf(path.read_bytes()), f"source Windows launcher uses CRLF: {path.relative_to(ROOT)}", checks)
    for path in unix:
        data = path.read_bytes()
        expect(b"\n" in data and b"\r" not in data, f"source Unix launcher uses LF: {path.relative_to(ROOT)}", checks)

    with tempfile.TemporaryDirectory(prefix="nocturne-release-endings-") as temp:
        archive_path = Path(temp) / "launchers.zip"
        launchers = windows + unix
        with zipfile.ZipFile(archive_path, "w") as archive:
            for path in launchers:
                release.write_member(archive, path, path.relative_to(ROOT).as_posix(), (2026, 1, 1, 0, 0, 0))
        with zipfile.ZipFile(archive_path) as archive:
            for path in windows:
                name = path.relative_to(ROOT).as_posix()
                expect(has_only_crlf(archive.read(name)), f"ZIP Windows launcher preserves CRLF: {name}", checks)
            for path in unix:
                name = path.relative_to(ROOT).as_posix()
                data = archive.read(name)
                expect(b"\n" in data and b"\r" not in data, f"ZIP Unix launcher preserves LF: {name}", checks)


def non_mutating_audit(checks: list[str]) -> None:
    root_report = ROOT / "release-audit.json"
    expect(not root_report.exists(), "repository-root release-audit.json is absent before audit", checks)
    reports = []
    for _ in range(2):
        result = subprocess.run(
            ["node", "scripts/release-audit.mjs", "--source"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        reports.append(json.loads(result.stdout))
    relevant = lambda report: {  # noqa: E731 - compact normalization for the two-run assertion.
        "mode": report.get("mode"),
        "overall": report.get("overall"),
        "counts": report.get("counts"),
        "passes": report.get("passes"),
        "warnings": report.get("warnings"),
        "errors": report.get("errors"),
    }
    expect(relevant(reports[0]) == relevant(reports[1]), "two source audits produce identical relevant results", checks)
    expect(not root_report.exists(), "two source audits create no repository-root report", checks)


def main() -> int:
    checks: list[str] = []
    fixture_selection(checks)
    actual_tree_selection(checks)
    executable_modes(checks)
    launcher_line_endings(checks)
    non_mutating_audit(checks)
    print(json.dumps({"schema": "nocturne.release-builder-smoke.v1", "overall": "PASS", "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"schema": "nocturne.release-builder-smoke.v1", "overall": "FAIL", "error": str(exc)}, indent=2))
        raise
