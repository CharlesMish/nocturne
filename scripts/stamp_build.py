#!/usr/bin/env python3
"""Stamp one canonical Nocturne build identity and synchronize its fallbacks.

Examples:

    python scripts/stamp_build.py --version 0.1.0-alpha.10
    python scripts/stamp_build.py --version 0.1.0-alpha.10 \
        --revision product-v0.3.0 --revision-kind package

A Git checkout uses the short commit automatically. A source-archive build can
supply an explicit package revision rather than pretending it has a commit.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BUILD_PATH = ROOT / "nocturne_build.json"
SYNC_SCRIPT = ROOT / "scripts" / "sync_release_data.py"


def git_text(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def load_existing(path: Path = BUILD_PATH) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Write and synchronize Nocturne build metadata.")
    parser.add_argument("--version", default=None, help="version label, e.g. 0.1.0-alpha.10")
    parser.add_argument("--channel", default="alpha", help="release channel label")
    parser.add_argument("--revision", default=None, help="git hash or explicit source/package revision")
    parser.add_argument(
        "--revision-kind",
        choices=("git", "package", "source-archive", "manual"),
        default=None,
        help="what the revision identifies",
    )
    parser.add_argument("--source-date", default=None, help="ISO source/revision date; defaults to git date or build time")
    parser.add_argument("--output", type=Path, default=BUILD_PATH, help="output JSON path")
    parser.add_argument("--no-sync", action="store_true", help="write JSON without updating browser/docs fallbacks")
    args = parser.parse_args()

    existing = load_existing(args.output)
    version = args.version or str(existing.get("version") or "0.1.0-alpha.1")
    now = iso_now()

    git_revision = git_text("rev-parse", "--short", "HEAD")
    git_date = git_text("show", "-s", "--format=%cI", "HEAD")
    revision = args.revision or git_revision or str(existing.get("revision") or "source-archive")
    if args.revision_kind:
        revision_kind = args.revision_kind
    elif git_revision and revision == git_revision:
        revision_kind = "git"
    else:
        revision_kind = str(existing.get("revision_kind") or "source-archive")
    source_date = args.source_date or (git_date if revision_kind == "git" else None) or now
    day = source_date[:10]

    stamped: dict[str, Any] = {
        "schema": "nocturne.build.v2",
        "version": version,
        "channel": args.channel,
        "build_date_utc": now,
        "revision": revision,
        "revision_kind": revision_kind,
        "source_date_utc": source_date,
        "feedback_label": f"v{version} · {day} · {revision}",
    }
    if revision_kind == "git":
        # Retain legacy fields for older clients while making their semantics exact.
        stamped["commit"] = revision
        stamped["commit_date_utc"] = source_date

    args.output.write_text(json.dumps(stamped, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    display = args.output.relative_to(ROOT) if args.output.is_relative_to(ROOT) else args.output
    print(f"Wrote {display}")
    print(stamped["feedback_label"])

    if not args.no_sync:
        if args.output.resolve() != BUILD_PATH.resolve():
            parser.error("automatic synchronization is only available for the canonical nocturne_build.json")
        subprocess.run([sys.executable, str(SYNC_SCRIPT)], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
