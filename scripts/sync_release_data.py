#!/usr/bin/env python3
"""Synchronize generated browser fallbacks and release-facing build labels.

The canonical sound catalog lives in sounds/sound_library.json. The canonical
build identity lives in nocturne_build.json. This script copies those exact
objects into static/index.html and refreshes marked documentation blocks so a
release never depends on hand-editing the same data twice.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "static" / "index.html"
SOUND_LIBRARY = ROOT / "sounds" / "sound_library.json"
BUILD_INFO = ROOT / "nocturne_build.json"
README = ROOT / "README.md"
ALPHA_FEEDBACK = ROOT / "ALPHA_FEEDBACK.md"

SOUND_BEGIN = "/* NOCTURNE:BEGIN GENERATED SOUND LIBRARY */"
SOUND_END = "/* NOCTURNE:END GENERATED SOUND LIBRARY */"
BUILD_BEGIN = "/* NOCTURNE:BEGIN GENERATED BUILD INFO */"
BUILD_END = "/* NOCTURNE:END GENERATED BUILD INFO */"
DOC_BEGIN = "<!-- NOCTURNE:BEGIN GENERATED BUILD ID -->"
DOC_END = "<!-- NOCTURNE:END GENERATED BUILD ID -->"


def load_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def replace_generated_object(text: str, *, declaration: str, begin: str, end: str, data: dict[str, Any]) -> str:
    rendered = json.dumps(data, indent=2, ensure_ascii=False)
    block = f"{declaration} {begin}\n{rendered}\n  {end};"
    pattern = re.compile(
        rf"{re.escape(declaration)}\s+{re.escape(begin)}.*?{re.escape(end)};",
        flags=re.DOTALL,
    )
    updated, count = pattern.subn(block, text, count=1)
    if count != 1:
        raise ValueError(f"Could not locate exactly one generated block for {declaration!r}")
    return updated


def doc_block(build: dict[str, Any]) -> str:
    version = str(build.get("version") or "unknown")
    label = str(build.get("feedback_label") or f"v{version} · unknown")
    revision = str(build.get("revision") or build.get("commit") or "unknown")
    return (
        f"{DOC_BEGIN}\n"
        f"Current packaged alpha label:\n\n"
        f"```text\n{label}\n```\n\n"
        f"To stamp another package from a Git checkout or source archive:\n\n"
        f"```bash\n"
        f"python scripts/stamp_build.py --version {version} --revision {revision}\n"
        f"```\n"
        f"{DOC_END}"
    )


def replace_doc_block(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"{re.escape(DOC_BEGIN)}.*?{re.escape(DOC_END)}", flags=re.DOTALL)
    updated, count = pattern.subn(block, text, count=1)
    if count != 1:
        raise ValueError(f"Could not locate generated build marker block in {path.relative_to(ROOT)}")
    path.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync canonical Nocturne release data into browser/doc fallbacks.")
    parser.add_argument("--check", action="store_true", help="fail if synchronization would change a file")
    args = parser.parse_args()

    sound = load_object(SOUND_LIBRARY)
    build = load_object(BUILD_INFO)
    original_index = INDEX.read_text(encoding="utf-8")
    updated_index = replace_generated_object(
        original_index,
        declaration="const DEFAULT_SOUND_LIBRARY =",
        begin=SOUND_BEGIN,
        end=SOUND_END,
        data=sound,
    )
    updated_index = replace_generated_object(
        updated_index,
        declaration="const DEFAULT_BUILD_INFO =",
        begin=BUILD_BEGIN,
        end=BUILD_END,
        data=build,
    )

    rendered_doc = doc_block(build)
    changes: list[str] = []
    if updated_index != original_index:
        changes.append(str(INDEX.relative_to(ROOT)))
        if not args.check:
            INDEX.write_text(updated_index, encoding="utf-8")

    for path in (README, ALPHA_FEEDBACK):
        original = path.read_text(encoding="utf-8")
        pattern = re.compile(rf"{re.escape(DOC_BEGIN)}.*?{re.escape(DOC_END)}", flags=re.DOTALL)
        candidate, count = pattern.subn(rendered_doc, original, count=1)
        if count != 1:
            raise ValueError(f"Could not locate generated build marker block in {path.relative_to(ROOT)}")
        if candidate != original:
            changes.append(str(path.relative_to(ROOT)))
            if not args.check:
                path.write_text(candidate, encoding="utf-8")

    if args.check and changes:
        print("Generated release data is stale:")
        for path in changes:
            print(f"- {path}")
        return 1

    if changes:
        print("Synchronized:")
        for path in changes:
            print(f"- {path}")
    else:
        print("Generated release data is already synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
