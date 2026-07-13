#!/usr/bin/env python3
"""Create a local, reviewable Nocturne support report without uploading it."""
from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "nocturne-support-report.txt"


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def linux_memory() -> tuple[str, str]:
    path = Path("/proc/meminfo")
    if not path.exists():
        return ("unknown", "unknown")
    values: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition(":")
            if key in {"MemTotal", "MemAvailable"}:
                values[key] = value.strip()
    except OSError:
        return ("unknown", "unknown")
    return values.get("MemTotal", "unknown"), values.get("MemAvailable", "unknown")


def main() -> int:
    build = read_json(ROOT / "nocturne_build.json")
    pointer = read_json(ROOT / "nocturne_profile.json")
    profile = os.getenv("NOCTURNE_PROFILE") or pointer.get("profile") or "nocturne"
    catalog = read_json(ROOT / "sounds" / "sound_library.json")
    generated = [
        sound for sound in catalog.get("sounds", [])
        if isinstance(sound, dict) and sound.get("availability") == "install_generated"
    ]
    missing_generated = []
    for sound in generated:
        src = str(sound.get("src", ""))
        path = ROOT / src.lstrip("/")
        if not path.is_file():
            missing_generated.append(sound.get("id", src))

    required = [
        "main.py", "run_nocturne.py", "static/index.html",
        "sounds/sound_library.json", "profiles/nocturne.json",
        "profiles/nocturne-pi.json",
    ]
    missing_required = [rel for rel in required if not (ROOT / rel).is_file()]
    total_mem, available_mem = linux_memory()

    lines = [
        "Nocturne support report",
        "========================",
        "",
        "This file was created locally and was not uploaded.",
        "Review it before sharing.",
        "",
        f"Build: {build.get('feedback_label', 'unknown')}",
        f"Profile: {profile}",
        f"Operating system: {platform.system()} {platform.release()}",
        f"Architecture: {platform.machine() or 'unknown'}",
        f"Python: {platform.python_version()}",
        f"Memory total: {total_mem}",
        f"Memory available: {available_mem}",
        f"HTTPS configured in environment: {'yes' if os.getenv('NOCTURNE_SSL_CERTFILE') and os.getenv('NOCTURNE_SSL_KEYFILE') else 'no'}",
        f"Required files missing: {', '.join(missing_required) if missing_required else 'none'}",
        f"Generated beds present: {len(generated) - len(missing_generated)}/{len(generated)}",
        f"Generated beds missing: {', '.join(map(str, missing_generated)) if missing_generated else 'none'}",
        "",
        "Browser details are not read by this script. Use the Copy diagnostics",
        "control in Settings when available, then paste that section below.",
        "",
        "Browser diagnostics:",
        "(paste here)",
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT.name}. Nothing was uploaded.")
    print("Review the file before attaching it to an issue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
