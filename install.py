#!/usr/bin/env python3
"""
Nocturne installer for Raspberry Pi / macOS / Linux / Windows.

It intentionally does not bundle third-party audio. Instead it:
  1. Creates/uses .venv and installs Python dependencies.
  2. Creates sounds/, sounds/radio/, songs/, and config/.
  3. Writes a default config/nocturne.json if one does not exist.
  4. Generates the procedural noise beds locally.
  5. Optionally downloads third-party ambience from media_sources.json.

Run:
  python3 install.py

Windows:
  Double-click "Install Nocturne.bat", then "Start Nocturne.bat".

For real rain/fire/thunder media:
  cp media_sources.example.json media_sources.json
  # edit media_sources.json with source URLs
  python3 install.py --fetch-media
"""
from __future__ import annotations

import argparse
import os
import platform
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"


def _bin(name: str) -> Path:
    if platform.system().lower().startswith("win"):
        return VENV / "Scripts" / f"{name}.exe"
    return VENV / "bin" / name


def run(cmd: list[str | Path], *, env: dict[str, str] | None = None) -> None:
    printable = " ".join(shlex.quote(str(c)) for c in cmd)
    print(f"\n$ {printable}", flush=True)
    subprocess.run([str(c) for c in cmd], check=True, cwd=ROOT, env=env)


def ensure_venv() -> Path:
    if not VENV.exists():
        run([sys.executable, "-m", "venv", VENV])
    python = _bin("python")
    if not python.exists():
        raise RuntimeError(f"virtualenv python not found: {python}")
    return python


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Nocturne locally.")
    parser.add_argument("--skip-deps", action="store_true", help="do not install requirements.txt")
    parser.add_argument("--skip-noise", action="store_true", help="do not generate procedural noise beds")
    parser.add_argument("--noise-seconds", type=int, default=300, help="noise duration per generated file")
    parser.add_argument("--fetch-media", action="store_true", help="download rain/fire/thunder files from media_sources.json")
    parser.add_argument("--overwrite-media", action="store_true", help="replace existing downloaded media")
    parser.add_argument("--host", default="127.0.0.1", help="host printed in the final run command")
    parser.add_argument("--port", default="8000", help="port printed in the final run command")
    args = parser.parse_args()

    (ROOT / "sounds").mkdir(exist_ok=True)
    (ROOT / "sounds" / "radio").mkdir(exist_ok=True)
    (ROOT / "songs").mkdir(exist_ok=True)
    (ROOT / "config").mkdir(exist_ok=True)
    settings_path = ROOT / "config" / "nocturne.json"
    example_settings = ROOT / "config" / "nocturne.example.json"
    if not settings_path.exists() and example_settings.exists():
        settings_path.write_text(example_settings.read_text(encoding="utf-8"), encoding="utf-8")
        print("Created config/nocturne.json")

    python = ensure_venv()

    if not args.skip_deps:
        run([python, "-m", "pip", "install", "--upgrade", "pip"])
        run([python, "-m", "pip", "install", "-r", ROOT / "requirements.txt"])

    if not args.skip_noise:
        run([python, ROOT / "scripts" / "generate_noise.py", "--seconds", str(args.noise_seconds)])

    if args.fetch_media:
        cmd: list[str | Path] = [python, ROOT / "scripts" / "fetch_media.py", "--yes"]
        if args.overwrite_media:
            cmd.append("--overwrite")
        run(cmd)
    else:
        print("\nSkipping third-party media download.")
        print("To add real rain/fire/thunder files:")
        print("  cp media_sources.example.json media_sources.json")
        print("  # edit media_sources.json with the source URLs")
        print("  python3 install.py --fetch-media")

    print("\nNocturne is installed.")
    if platform.system().lower().startswith("win"):
        print("Run it with:")
        print(f"  .venv\\Scripts\\python.exe -m uvicorn main:app --host {args.host} --port {args.port}")
        print('Or double-click "Start Nocturne.bat".')
    else:
        print("Run it with:")
        print("  source .venv/bin/activate")
        print(f"  uvicorn main:app --host {args.host} --port {args.port}")
    if args.host == "127.0.0.1":
        print("\nFor LAN access from a phone/tablet, run with --host 0.0.0.0 deliberately.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode)
