#!/usr/bin/env python3
"""Build separate Nocturne product and evidence archives.

The product archive contains the runnable source package and concise operating
docs. Verification logs, screenshots, generated reports, and optional historical
material go to the evidence archive instead of inflating the tester download.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from path_safety import resolve_catalog_path

ROOT = Path(__file__).resolve().parents[1]
TRANSIENT_NAMES = {
    "release-audit.json",
    "verification-report.json",
    "implementation-status.json",
    "polish-edit-record.json",
}
TRANSIENT_DIRS = {"verification-artifacts", "verification-logs"}
SKIP_PARTS = {".git", ".venv", "__pycache__", "node_modules", ".cache", "dist", "build", "review_bundles"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".tmp", ".bak"}
ROOT_MEDIA_SUFFIXES = {".aac", ".flac", ".m4a", ".mp3", ".mp4", ".ogg", ".opus", ".wav", ".webm"}
LOCAL_ONLY_PATHS = {
    Path("media_sources.json"),
    Path("sounds/MEDIA_MANIFEST.generated.json"),
    Path("IMPLEMENTATION_REPORT.md"),
    Path("VERIFICATION_REPORT.md"),
    Path("CHANGE_SUMMARY.md"),
    Path("NOCTURNE_ALPHA13_HARDENING.patch"),
}
CONFIG_PRODUCT_FILES = {
    Path("config/.gitkeep"),
    Path("config/nocturne.example.json"),
}
RADIO_PRODUCT_FILES = {Path("sounds/radio/README.md")}
BUNDLED_SONG_DIRS = {Path("songs/evening-loop")}
EVIDENCE_ONLY_DIRS = {
    Path("provenance/originals"),
    Path("provenance/screenshots"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generated_audio_paths(root: Path) -> set[Path]:
    data = json.loads((root / "sounds" / "sound_library.json").read_text(encoding="utf-8"))
    paths: set[Path] = set()
    for sound in data.get("sounds", []):
        if sound.get("availability") != "install_generated":
            continue
        src = str(sound.get("src", ""))
        if not src.startswith("/sounds/"):
            raise ValueError(f"Generated sound path is outside /sounds/: {src}")
        paths.add(resolve_catalog_path(root, src.lstrip("/"), root / "sounds", "generated sound path"))
    return paths


def is_transient(rel: Path) -> bool:
    return rel.name in TRANSIENT_NAMES or any(part in TRANSIENT_DIRS for part in rel.parts)


def is_within(rel: Path, directory: Path) -> bool:
    return rel.parts[:len(directory.parts)] == directory.parts


def is_workspace_only(rel: Path) -> bool:
    """Local state and review material that must never enter a product ZIP."""
    lower_name = rel.name.lower()
    if rel in LOCAL_ONLY_PATHS:
        return True
    if lower_name.endswith(".zip") or lower_name.endswith(".zip.sha256"):
        return True
    if len(rel.parts) == 1 and rel.suffix.lower() in ROOT_MEDIA_SUFFIXES:
        return True
    if rel.parts[:1] == ("config",) and rel not in CONFIG_PRODUCT_FILES:
        return True
    if rel.parts[:2] == ("sounds", "radio") and rel not in RADIO_PRODUCT_FILES:
        return True
    if rel.parts[:1] == ("songs",) and not any(is_within(rel, directory) for directory in BUNDLED_SONG_DIRS):
        return True
    if any(is_within(rel, directory) for directory in EVIDENCE_ONLY_DIRS):
        return True
    return False


def is_detached_evidence(rel: Path) -> bool:
    """Non-public intake payloads belong in the evidence archive, not tester ZIP."""
    return len(rel.parts) >= 3 and rel.parts[:2] == ("sounds", "inbox") and rel.name.lower() != "readme.md"


def _git_tracked_paths(root: Path) -> list[Path] | None:
    """Return tracked paths when *root* is exactly a Git worktree root."""
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if Path(top).resolve() != root.resolve():
            return None
        raw = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return [Path(item.decode("utf-8", errors="surrogateescape")) for item in raw.split(b"\0") if item]


def release_source_state(root: Path) -> str:
    """Describe whether release inputs come from a clean immutable source."""
    if _git_tracked_paths(root) is None:
        return "manifest-declared"
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "-z", "--untracked-files=no", "--"],
        check=True,
        capture_output=True,
    ).stdout
    return "dirty" if status else "clean"


def enforce_release_source(root: Path, allow_dirty: bool) -> tuple[str, bool]:
    """Reject uncommitted tracked input unless a development build opts in."""
    state = release_source_state(root)
    release_eligible = state != "dirty"
    if not release_eligible and not allow_dirty:
        raise SystemExit(
            "Tracked source tree is dirty; commit or restore tracked changes before a release build, "
            "or pass --allow-dirty for an explicitly non-release development artifact."
        )
    if not release_eligible:
        print("WARNING: building a DIRTY DEVELOPMENT ARTIFACT; it is not release-eligible.", file=sys.stderr)
    return state, release_eligible


def _manifest_declared_paths(root: Path) -> list[Path] | None:
    """Use the checked release manifest as the allowlist in source archives."""
    manifest_path = root / "RELEASE_MANIFEST.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return None
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = data.get("files", [])
    if not isinstance(records, list):
        raise ValueError("RELEASE_MANIFEST.json files must be a list")
    paths: list[Path] = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise ValueError("RELEASE_MANIFEST.json contains an invalid file record")
        paths.append(Path(record["path"]))
    paths.append(Path("RELEASE_MANIFEST.json"))
    return paths


def declared_product_paths(root: Path) -> list[Path]:
    """Return the fail-closed product allowlist for a checkout or source ZIP."""
    paths = _git_tracked_paths(root)
    if paths is None:
        paths = _manifest_declared_paths(root)
    if paths is None:
        raise ValueError("Product inputs require a Git worktree or RELEASE_MANIFEST.json")
    return sorted(set(paths), key=lambda path: path.as_posix())


def regular_file(root: Path, rel: Path, label: str = "product input") -> Path:
    """Resolve one declared regular file without following filesystem aliases."""
    if rel.is_absolute() or not rel.parts or any(part in {"", ".", ".."} for part in rel.parts):
        raise ValueError(f"Unsafe {label} path: {rel}")
    path = root / rel
    candidate = root
    for part in rel.parts:
        candidate /= part
        if candidate.is_symlink():
            raise ValueError(f"Symlink is not allowed as a {label}: {rel.as_posix()}")
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError as exc:
        raise ValueError(f"Declared {label} is missing: {rel.as_posix()}") from exc
    if not stat.S_ISREG(mode):
        raise ValueError(f"Declared {label} is not a regular file: {rel.as_posix()}")
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Declared {label} resolves outside the source root: {rel.as_posix()}") from exc
    return path


def detached_evidence_records(root: Path) -> list[dict[str, object]]:
    """Build the evidence inventory from canonical catalog metadata, not directory contents."""
    data = json.loads((root / "sounds" / "sound_library.json").read_text(encoding="utf-8"))
    records: list[dict[str, object]] = []
    for item in data.get("excluded_sounds", []):
        if item.get("retention") != "evidence_bundle":
            continue
        candidates = [
            (item.get("quarantine_path"), item.get("file_size_bytes"), item.get("sha256")),
            (
                item.get("transform_sidecar"),
                item.get("transform_sidecar_size_bytes"),
                item.get("transform_sidecar_sha256"),
            ),
        ]
        for raw_path, raw_size, raw_hash in candidates:
            if not raw_path:
                continue
            candidate = resolve_catalog_path(
                root,
                str(raw_path),
                root / "sounds" / "inbox",
                "detached evidence path",
            )
            path = candidate.relative_to(root.resolve()).as_posix()
            if raw_size is None or not raw_hash:
                raise ValueError(f"Detached evidence metadata is incomplete: {path}")
            records.append({"path": path, "size_bytes": int(raw_size), "sha256": str(raw_hash)})
    return sorted(records, key=lambda record: str(record["path"]))


def detached_evidence_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for record in detached_evidence_records(root):
        path = resolve_catalog_path(
            root,
            str(record["path"]),
            root / "sounds" / "inbox",
            "detached evidence path",
        )
        if not path.is_file():
            continue
        if path.stat().st_size != record["size_bytes"] or sha256(path) != record["sha256"]:
            raise ValueError(f"Detached evidence payload differs from canonical metadata: {record['path']}")
        files.append(path)
    return files


def product_files(root: Path) -> list[Path]:
    generated = generated_audio_paths(root)
    out: list[Path] = []
    for rel in declared_product_paths(root):
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        if rel.suffix.lower() in SKIP_SUFFIXES or rel.name in {".DS_Store", "Thumbs.db"}:
            continue
        if is_transient(rel) or is_workspace_only(rel) or is_detached_evidence(rel):
            continue
        path = regular_file(root, rel)
        if path.resolve() in generated:
            continue
        out.append(path)
    return out


def transient_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        if is_transient(rel):
            out.append(regular_file(root, rel, "evidence input"))
    return out


def zip_datetime(build: dict[str, object]) -> tuple[int, int, int, int, int, int]:
    raw = str(build.get("source_date_utc") or build.get("build_date_utc") or "")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
        return (max(1980, parsed.year), parsed.month, parsed.day, 0, 0, 0)
    except Exception:
        return (2026, 1, 1, 0, 0, 0)


def write_member(zf: zipfile.ZipFile, source: Path, arcname: str, stamp: tuple[int, int, int, int, int, int]) -> None:
    info = zipfile.ZipInfo(arcname.replace(os.sep, "/"), date_time=stamp)
    mode = source.stat().st_mode
    permissions = 0o755 if mode & stat.S_IXUSR else 0o644
    info.external_attr = (permissions & 0xFFFF) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    with source.open("rb") as handle:
        zf.writestr(info, handle.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def write_bytes(zf: zipfile.ZipFile, data: bytes, arcname: str, stamp: tuple[int, int, int, int, int, int]) -> None:
    info = zipfile.ZipInfo(arcname, date_time=stamp)
    info.external_attr = (0o644 & 0xFFFF) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    zf.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def manifest_for(
    root: Path,
    files: Iterable[Path],
    package_name: str,
    build: dict[str, object],
    *,
    source_state: str,
    release_eligible: bool,
) -> dict[str, object]:
    records = []
    total = 0
    for path in files:
        rel = path.relative_to(root).as_posix()
        if rel == "RELEASE_MANIFEST.json":
            continue
        size = path.stat().st_size
        total += size
        records.append({"path": rel, "size_bytes": size, "sha256": sha256(path)})
    detached = detached_evidence_records(root)
    detached_total = sum(int(record["size_bytes"]) for record in detached)
    return {
        "schema": "nocturne.release-manifest.v2",
        "profile": "product-source",
        "package": package_name,
        "build": build,
        "source_state": source_state,
        "release_eligible": release_eligible,
        "generated_at_utc": str(build.get("build_date_utc") or build.get("source_date_utc") or "unknown"),
        "file_count": len(records),
        "total_payload_bytes_excluding_manifest": total,
        "manifest_self_excluded": True,
        "evidence_detached": True,
        "detached_evidence_file_count": len(detached),
        "detached_evidence_bytes": detached_total,
        "detached_evidence": detached,
        "files": records,
    }


def test_zip(path: Path) -> None:
    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC failed at {bad}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--product-name", required=True, help="top-level folder and product ZIP basename")
    parser.add_argument("--evidence-name", required=True, help="top-level folder and evidence ZIP basename")
    parser.add_argument("--evidence-source", type=Path, help="optional external history/media/evidence tree")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="build an explicitly non-release development artifact from modified tracked files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    source_state, release_eligible = enforce_release_source(root, args.allow_dirty)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    build = json.loads((root / "nocturne_build.json").read_text(encoding="utf-8"))
    stamp = zip_datetime(build)

    # Write a fresh product manifest, then include that manifest in the archive.
    initial_files = product_files(root)
    manifest = manifest_for(
        root,
        initial_files,
        args.product_name,
        build,
        source_state=source_state,
        release_eligible=release_eligible,
    )
    manifest_path = root / "RELEASE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    files = sorted(
        [path for path in initial_files if path.relative_to(root).as_posix() != "RELEASE_MANIFEST.json"]
        + [manifest_path],
        key=lambda path: path.relative_to(root).as_posix(),
    )

    product_zip = output_dir / f"{args.product_name}.zip"
    evidence_zip = output_dir / f"{args.evidence_name}.zip"
    for path in (product_zip, evidence_zip):
        path.unlink(missing_ok=True)

    with zipfile.ZipFile(product_zip, "w") as zf:
        for source in files:
            rel = source.relative_to(root).as_posix()
            write_member(zf, source, f"{args.product_name}/{rel}", stamp)
    test_zip(product_zip)
    product_hash = sha256(product_zip)
    (output_dir / f"{args.product_name}.zip.sha256").write_text(f"{product_hash}  {product_zip.name}\n", encoding="utf-8")

    source_label = "release-eligible" if release_eligible else "DIRTY DEVELOPMENT BUILD — NOT RELEASE-ELIGIBLE"
    evidence_readme = f"""# Nocturne evidence bundle\n\nThis archive accompanies `{product_zip.name}`. It holds verification outputs,\nprior release/process history, and source media retained for traceability rather\nthan placing those files in the tester-facing product archive.\n\nProduct SHA-256: `{product_hash}`\n\nBuild: `{build.get('feedback_label', 'unknown')}`\n\nSource state: `{source_label}`\n\nEvidence is not proof of listening comfort, overnight browser survival, screen-\nreader quality, or target Raspberry Pi performance. Those remain field tests.\n"""

    with zipfile.ZipFile(evidence_zip, "w") as zf:
        prefix = args.evidence_name
        write_bytes(zf, evidence_readme.encode("utf-8"), f"{prefix}/README.md", stamp)
        write_bytes(zf, f"{product_hash}  {product_zip.name}\n".encode("utf-8"), f"{prefix}/PRODUCT_SHA256.txt", stamp)
        write_member(zf, root / "RELEASE_MANIFEST.json", f"{prefix}/product/RELEASE_MANIFEST.json", stamp)
        for source in transient_files(root):
            rel = source.relative_to(root).as_posix()
            write_member(zf, source, f"{prefix}/current/{rel}", stamp)
        for source in detached_evidence_files(root):
            rel = source.relative_to(root).as_posix()
            write_member(zf, source, f"{prefix}/current/detached/{rel}", stamp)
        if args.evidence_source:
            evidence_source = args.evidence_source.resolve()
            if not evidence_source.is_dir():
                raise SystemExit(f"Evidence source is not a directory: {evidence_source}")
            for source in sorted(evidence_source.rglob("*")):
                if source.is_file() and not any(part in SKIP_PARTS for part in source.relative_to(evidence_source).parts):
                    rel = source.relative_to(evidence_source).as_posix()
                    write_member(zf, source, f"{prefix}/retained/{rel}", stamp)
    test_zip(evidence_zip)
    evidence_hash = sha256(evidence_zip)
    (output_dir / f"{args.evidence_name}.zip.sha256").write_text(f"{evidence_hash}  {evidence_zip.name}\n", encoding="utf-8")

    result = {
        "schema": "nocturne.release-build.v1",
        "build": build.get("feedback_label"),
        "source": {"state": source_state, "release_eligible": release_eligible},
        "product": {"path": str(product_zip), "size_bytes": product_zip.stat().st_size, "sha256": product_hash},
        "evidence": {"path": str(evidence_zip), "size_bytes": evidence_zip.stat().st_size, "sha256": evidence_hash},
        "product_files": len(files),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
