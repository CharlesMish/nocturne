#!/usr/bin/env python3
"""Stamp nocturne_build.json for alpha/release feedback.

Run this from a git checkout before making a zip so testers can report the exact
build they used:

    python scripts/stamp_build.py --version 0.1.0-alpha.2
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BUILD_PATH = ROOT / "nocturne_build.json"


def git_text(*args: str) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def load_existing() -> dict[str, Any]:
    if not BUILD_PATH.exists():
        return {}
    try:
        data = json.loads(BUILD_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Write nocturne_build.json with git build metadata.")
    parser.add_argument("--version", default=None, help="version label, e.g. 0.1.0-alpha.2")
    parser.add_argument("--channel", default="alpha", help="release channel label")
    parser.add_argument("--output", type=Path, default=BUILD_PATH, help="output JSON path")
    args = parser.parse_args()

    existing = load_existing()
    version = args.version or str(existing.get("version") or "0.1.0-alpha.1")
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    commit = git_text("rev-parse", "--short", "HEAD") or "unknown"
    commit_date = git_text("show", "-s", "--format=%cI", "HEAD") or now

    stamped = {
        "version": version,
        "channel": args.channel,
        "build_date_utc": now,
        "commit": commit,
        "commit_date_utc": commit_date,
        "feedback_label": f"v{version} · {commit_date[:10]} · {commit}",
    }
    args.output.write_text(json.dumps(stamped, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.output.relative_to(ROOT) if args.output.is_relative_to(ROOT) else args.output}")
    print(stamped["feedback_label"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
