#!/usr/bin/env python3
"""Build Nocturne, Nocturne Pi, and one version-matched evidence archive."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import make_release as base  # noqa: E402

ROOT = SCRIPT_DIR.parent
PROFILE_IDS = ("nocturne", "nocturne-pi")


def stage_profile(root: Path, destination: Path, profile_id: str, package_name: str) -> tuple[list[Path], dict[str, object]]:
    destination.mkdir(parents=True, exist_ok=True)
    for source in base.product_files(root):
        rel = source.relative_to(root)
        if rel.as_posix() == "RELEASE_MANIFEST.json":
            continue
        if profile_id == "nocturne-pi" and rel.as_posix() == "static/rain.mp4":
            continue
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    (destination / "nocturne_profile.json").write_text(
        json.dumps({"profile": profile_id}, indent=2) + "\n", encoding="utf-8"
    )

    manifest_path = destination / "static" / "manifest.webmanifest"
    web_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if profile_id == "nocturne-pi":
        web_manifest["name"] = "Nocturne Pi — a quiet place"
        web_manifest["short_name"] = "Nocturne Pi"
        web_manifest["description"] = "A lower-resource local-first bedside sound instrument for Raspberry Pi-class systems."
    else:
        web_manifest["name"] = "Nocturne — a quiet place"
        web_manifest["short_name"] = "Nocturne"
    manifest_path.write_text(json.dumps(web_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    build = json.loads((destination / "nocturne_build.json").read_text(encoding="utf-8"))
    initial = base.product_files(destination)
    release_manifest = base.manifest_for(destination, initial, package_name, build)
    source_manifest_path = root / "RELEASE_MANIFEST.json"
    if source_manifest_path.exists():
        source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
        for key in ("evidence_detached", "detached_evidence_file_count", "detached_evidence_bytes", "detached_evidence"):
            if key in source_manifest:
                release_manifest[key] = source_manifest[key]
    release_manifest["schema"] = "nocturne.release-manifest.v3"
    release_manifest["profile"] = profile_id
    release_manifest["shared_source_build"] = build.get("feedback_label")
    (destination / "RELEASE_MANIFEST.json").write_text(
        json.dumps(release_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return base.product_files(destination), build


def write_product_zip(stage: Path, files: list[Path], output: Path, package_name: str, stamp) -> str:
    output.unlink(missing_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        for source in files:
            rel = source.relative_to(stage).as_posix()
            base.write_member(archive, source, f"{package_name}/{rel}", stamp)
    base.test_zip(output)
    digest = base.sha256(output)
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    return digest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--release-id", required=True, help="archive suffix, e.g. v0.1.0-alpha.12")
    parser.add_argument("--evidence-source", type=Path, help="optional evidence-branch snapshot to include")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    canonical_build = json.loads((root / "nocturne_build.json").read_text(encoding="utf-8"))
    stamp = base.zip_datetime(canonical_build)

    products: dict[str, dict[str, object]] = {}
    with tempfile.TemporaryDirectory(prefix="nocturne-dual-release-") as temp_dir:
        temp_root = Path(temp_dir)
        for profile_id in PROFILE_IDS:
            package_name = f"nocturne{'-pi' if profile_id == 'nocturne-pi' else ''}-{args.release_id}"
            stage = temp_root / package_name
            files, build = stage_profile(root, stage, profile_id, package_name)
            output = output_dir / f"{package_name}.zip"
            digest = write_product_zip(stage, files, output, package_name, stamp)
            products[profile_id] = {
                "package": package_name,
                "path": str(output),
                "size_bytes": output.stat().st_size,
                "sha256": digest,
                "manifest": stage / "RELEASE_MANIFEST.json",
                "build": build.get("feedback_label"),
            }

        evidence_name = f"nocturne-evidence-{args.release_id}"
        evidence_zip = output_dir / f"{evidence_name}.zip"
        evidence_zip.unlink(missing_ok=True)
        hashes = "\n".join(
            f"{record['sha256']}  {Path(str(record['path'])).name}"
            for record in products.values()
        ) + "\n"
        readme = f"""# Nocturne evidence — {args.release_id}\n\nThis archive accompanies two editions built from one source identity:\n\n- `{Path(str(products['nocturne']['path'])).name}`\n- `{Path(str(products['nocturne-pi']['path'])).name}`\n\nBuild: `{canonical_build.get('feedback_label', 'unknown')}`\n\nThe two products differ only in their presentation profile and packaged visual\nassets. Server-only versus local-display use remains a deployment dimension,\nnot another edition. Hardware, listening, screen-reader, lock-screen, and\novernight behavior require real field evidence.\n"""
        with zipfile.ZipFile(evidence_zip, "w") as archive:
            base.write_bytes(archive, readme.encode("utf-8"), f"{evidence_name}/README.md", stamp)
            base.write_bytes(archive, hashes.encode("utf-8"), f"{evidence_name}/PRODUCT_SHA256S.txt", stamp)
            for profile_id, record in products.items():
                manifest = Path(record["manifest"])
                base.write_member(archive, manifest, f"{evidence_name}/products/{profile_id}/RELEASE_MANIFEST.json", stamp)
            if args.evidence_source:
                evidence_source = args.evidence_source.resolve()
                if not evidence_source.is_dir():
                    raise SystemExit(f"Evidence source is not a directory: {evidence_source}")
                for source in sorted(evidence_source.rglob("*")):
                    if not source.is_file() or any(part in base.SKIP_PARTS for part in source.relative_to(evidence_source).parts):
                        continue
                    rel = source.relative_to(evidence_source).as_posix()
                    base.write_member(archive, source, f"{evidence_name}/branch-snapshot/{rel}", stamp)
        base.test_zip(evidence_zip)
        evidence_hash = base.sha256(evidence_zip)
        evidence_zip.with_suffix(evidence_zip.suffix + ".sha256").write_text(
            f"{evidence_hash}  {evidence_zip.name}\n", encoding="utf-8"
        )

    result = {
        "schema": "nocturne.dual-release-build.v1",
        "build": canonical_build.get("feedback_label"),
        "products": products,
        "evidence": {
            "path": str(evidence_zip),
            "size_bytes": evidence_zip.stat().st_size,
            "sha256": evidence_hash,
        },
    }
    # Paths to temporary staged manifests are not useful after this run.
    for record in result["products"].values():
        record.pop("manifest", None)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
