#!/usr/bin/env python3
"""Regression checks for dirty-tree release selection and ZIP permissions."""
from __future__ import annotations

import json
import os
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
        policy_forbidden = {
            "workspace.zip",
            "workspace.zip.sha256",
            "scratch.wav",
            "web/package.json",
            "web/src/App.tsx",
            ".github/workflows/web.yml",
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
        undeclared = {
            ".env",
            "owner-note.txt",
            "nocturne-support-report.txt",
            "pip-unpack/metadata.txt",
        }
        for rel in allowed | policy_forbidden | undeclared:
            write(root / rel)
        declared = allowed | policy_forbidden | {"sounds/sound_library.json"}
        write(
            root / "RELEASE_MANIFEST.json",
            json.dumps({"files": [{"path": rel} for rel in sorted(declared)]}),
        )
        selected = {path.relative_to(root).as_posix() for path in release.product_files(root)}
        expect(allowed <= selected, "release policy keeps canonical files in mutable directories", checks)
        expect(not policy_forbidden & selected, "release policy rejects workspace-only declared fixtures", checks)
        expect(not any(path.startswith("web/") for path in selected), "hosted web source is excluded from local product selection", checks)
        expect(".github/workflows/web.yml" not in selected, "hosted web workflow is excluded from local product selection", checks)
        expect(not undeclared & selected, "release allowlist excludes arbitrary local and support-report files", checks)


def symlink_selection(checks: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="nocturne-release-symlink-") as temp:
        root = Path(temp)
        write(root / "sounds/sound_library.json", json.dumps({"sounds": [], "excluded_sounds": []}))
        write(root / "ordinary.txt")
        (root / "inside-link.txt").symlink_to(root / "ordinary.txt")
        write(
            root / "RELEASE_MANIFEST.json",
            json.dumps({"files": [
                {"path": "inside-link.txt"},
                {"path": "sounds/sound_library.json"},
            ]}),
        )
        try:
            release.product_files(root)
        except ValueError as exc:
            expect("Symlink is not allowed" in str(exc), "release selection rejects an in-root file symlink", checks)
        else:
            raise AssertionError("release selection accepted an in-root file symlink")

    with tempfile.TemporaryDirectory(prefix="nocturne-release-symlink-") as temp:
        root = Path(temp)
        write(root / "sounds/sound_library.json", json.dumps({"sounds": [], "excluded_sounds": []}))
        write(root / "ordinary/nested.txt")
        (root / "inside-directory-link").symlink_to(root / "ordinary", target_is_directory=True)
        write(
            root / "RELEASE_MANIFEST.json",
            json.dumps({"files": [
                {"path": "inside-directory-link/nested.txt"},
                {"path": "sounds/sound_library.json"},
            ]}),
        )
        try:
            release.product_files(root)
        except ValueError as exc:
            expect("Symlink is not allowed" in str(exc), "release selection rejects an in-root directory symlink", checks)
        else:
            raise AssertionError("release selection accepted an in-root directory symlink")

    with tempfile.TemporaryDirectory(prefix="nocturne-release-symlink-") as temp, tempfile.TemporaryDirectory(prefix="nocturne-release-outside-") as outside:
        root = Path(temp)
        write(root / "sounds/sound_library.json", json.dumps({"sounds": [], "excluded_sounds": []}))
        external = Path(outside) / "outside.txt"
        write(external)
        (root / "outside-link.txt").symlink_to(external)
        write(
            root / "RELEASE_MANIFEST.json",
            json.dumps({"files": [
                {"path": "outside-link.txt"},
                {"path": "sounds/sound_library.json"},
            ]}),
        )
        try:
            release.product_files(root)
        except ValueError as exc:
            expect("Symlink is not allowed" in str(exc), "release selection rejects an out-of-root file symlink", checks)
        else:
            raise AssertionError("release selection accepted an out-of-root file symlink")


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
    expect(not any(path.startswith("web/") for path in selected), "live hosted web tree is excluded from local product selection", checks)
    expect(".github/workflows/web.yml" not in selected, "live hosted web workflow is excluded from local product selection", checks)
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


def dirty_release_policy(checks: list[str]) -> None:
    script = ROOT / "scripts" / "make_release.py"
    with tempfile.TemporaryDirectory(prefix="nocturne-dirty-release-") as temp:
        root = Path(temp) / "source"
        output = Path(temp) / "output"
        write(
            root / "nocturne_build.json",
            json.dumps({
                "version": "0.0.0-fixture",
                "build_date_utc": "2026-01-01T00:00:00Z",
                "feedback_label": "fixture",
            }),
        )
        write(root / "sounds/sound_library.json", json.dumps({"sounds": [], "excluded_sounds": []}))
        write(root / "README.md", "clean fixture\n")
        write(root / "RELEASE_MANIFEST.json", json.dumps({"files": []}))
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(
            [
                "git", "-C", str(root), "-c", "user.name=Nocturne Smoke",
                "-c", "user.email=nocturne-smoke@example.invalid", "commit", "-qm", "fixture",
            ],
            check=True,
        )
        expect(release.release_source_state(root) == "clean", "committed fixture is release-eligible", checks)

        write(root / "README.md", "uncommitted fixture change\n")
        ordinary = subprocess.run(
            [
                sys.executable, str(script), "--root", str(root), "--output-dir", str(output),
                "--product-name", "dirty-fixture", "--evidence-name", "dirty-fixture-evidence",
            ],
            capture_output=True,
            text=True,
        )
        expect(ordinary.returncode != 0, "ordinary release rejects modified tracked source", checks)
        expect("Tracked source tree is dirty" in ordinary.stderr, "dirty-tree refusal explains the opt-in", checks)
        expect(not list(output.glob("*.zip")), "dirty-tree refusal emits no archive", checks)

        development = subprocess.run(
            [
                sys.executable, str(script), "--root", str(root), "--output-dir", str(output),
                "--product-name", "dirty-fixture", "--evidence-name", "dirty-fixture-evidence",
                "--allow-dirty",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(development.stdout)
        expect(report["source"] == {"state": "dirty", "release_eligible": False}, "dirty opt-in is non-release in command output", checks)
        with zipfile.ZipFile(output / "dirty-fixture.zip") as archive:
            manifest = json.loads(archive.read("dirty-fixture/RELEASE_MANIFEST.json"))
        expect(manifest["source_state"] == "dirty", "dirty opt-in is marked in the product manifest", checks)
        expect(manifest["release_eligible"] is False, "dirty product manifest is explicitly non-release", checks)
        with zipfile.ZipFile(output / "dirty-fixture-evidence.zip") as archive:
            evidence_readme = archive.read("dirty-fixture-evidence/README.md").decode("utf-8")
        expect("DIRTY DEVELOPMENT BUILD — NOT RELEASE-ELIGIBLE" in evidence_readme, "dirty evidence archive carries the warning", checks)


def dual_release_boundaries(checks: list[str]) -> None:
    script = ROOT / "scripts" / "make_dual_release.py"
    with tempfile.TemporaryDirectory(prefix=".nocturne-tmpdir-smoke-", dir=ROOT) as local_tmp, tempfile.TemporaryDirectory(prefix="nocturne-dual-output-") as output_parent:
        parent = Path(output_parent)
        hashes: list[dict[str, str]] = []
        for run in ("one", "two"):
            output = parent / run
            env = {**os.environ, "TMPDIR": local_tmp}
            subprocess.run(
                [
                    sys.executable, str(script), "--output-dir", str(output),
                    "--release-id", "boundary-smoke", "--allow-dirty",
                ],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            run_hashes: dict[str, str] = {}
            for archive_path in sorted(output.glob("*.zip")):
                run_hashes[archive_path.name] = release.sha256(archive_path)
                with zipfile.ZipFile(archive_path) as archive:
                    names = archive.namelist()
                    expected_root = archive_path.stem
                    expect(
                        {name.split("/", 1)[0] for name in names} == {expected_root},
                        f"{archive_path.name} has exactly one package root",
                        checks,
                    )
                    expect(
                        not any("nocturne-dual-release-" in name or ".nocturne-tmpdir-smoke-" in name for name in names),
                        f"{archive_path.name} contains no temporary staging member",
                        checks,
                    )
                    if archive_path.name.startswith("nocturne-pi-"):
                        expect(
                            not any(name.endswith("/static/rain.mp4") for name in names),
                            "Pi product omits the full rain video with TMPDIR inside the checkout",
                            checks,
                        )
                    if not archive_path.name.startswith("nocturne-evidence-"):
                        expect(
                            not any("/web/" in name for name in names),
                            f"{archive_path.name} excludes the hosted web source tree",
                            checks,
                        )
                        expect(
                            not any(name.endswith("/.github/workflows/web.yml") for name in names),
                            f"{archive_path.name} excludes the hosted web workflow",
                            checks,
                        )
                        manifest_name = f"{expected_root}/RELEASE_MANIFEST.json"
                        manifest = json.loads(archive.read(manifest_name))
                        expect(
                            manifest.get("release_eligible") == (manifest.get("source_state") != "dirty"),
                            f"{archive_path.name} records source eligibility consistently",
                            checks,
                        )
            hashes.append(run_hashes)
        expect(hashes[0] == hashes[1], "dual-profile archives are byte-identical across repeated builds", checks)


def main() -> int:
    checks: list[str] = []
    fixture_selection(checks)
    symlink_selection(checks)
    actual_tree_selection(checks)
    executable_modes(checks)
    launcher_line_endings(checks)
    non_mutating_audit(checks)
    dirty_release_policy(checks)
    dual_release_boundaries(checks)
    print(json.dumps({"schema": "nocturne.release-builder-smoke.v1", "overall": "PASS", "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"schema": "nocturne.release-builder-smoke.v1", "overall": "FAIL", "error": str(exc)}, indent=2))
        raise
