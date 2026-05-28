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

Media fetching (low-friction):
  - python3 install.py                 → generates pink noise + auto-fetches MP3s
                                          if a manifest with real direct URLs exists
  - python3 install.py --no-fetch-media → skip all third-party downloads
  - python3 install.py --fetch-media    → force fetch attempt (uses media_sources.json
                                          or falls back to media_sources.default.json)

A committed media_sources.default.json contains the 7 Pixabay source pages.
Copy it to media_sources.json (gitignored) and fill fresh direct CDN URLs
(obtain via browser DevTools on the source pages) for automatic download.
"""
from __future__ import annotations

import argparse
import json
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


def is_usable_download_url(url: str) -> bool:
    url = url.strip()
    if not url or url.startswith("TODO"):
        return False
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    if "example.com" in url or "..." in url:
        return False
    if any(ch.isspace() for ch in url):
        return False
    if "(" in url or ")" in url:
        return False
    return True


def manifest_has_downloads(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    files = data.get("files") if isinstance(data, dict) else None
    if not isinstance(files, list):
        return False
    for entry in files:
        if not isinstance(entry, dict):
            continue
        url = str(entry.get("url", ""))
        if is_usable_download_url(url):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Nocturne locally.")
    parser.add_argument("--skip-deps", action="store_true", help="do not install requirements.txt")
    parser.add_argument("--skip-noise", action="store_true", help="do not generate procedural noise beds")
    parser.add_argument("--noise-seconds", type=int, default=300, help="noise duration per generated file")
    parser.add_argument("--fetch-media", action="store_true", help="force download of ambience from media_sources.json (or .default.json)")
    parser.add_argument("--no-fetch-media", action="store_true", help="never attempt to download third-party MP3s, even if a manifest with real URLs exists")
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

    # Media fetch decision (low-friction by default when usable manifest exists)
    media_manifest = ROOT / "media_sources.json"
    default_manifest = ROOT / "media_sources.default.json"

    chosen_manifest = None
    if media_manifest.exists():
        chosen_manifest = media_manifest
    elif default_manifest.exists():
        chosen_manifest = default_manifest

    has_real_urls = manifest_has_downloads(chosen_manifest) if chosen_manifest else False
    should_fetch_media = (not args.no_fetch_media) and (args.fetch_media or has_real_urls)

    if should_fetch_media and chosen_manifest:
        cmd: list[str | Path] = [python, ROOT / "scripts" / "fetch_media.py", "--yes", "--manifest", chosen_manifest]
        if args.overwrite_media:
            cmd.append("--overwrite")
        run(cmd)
    elif not args.no_fetch_media:
        # Helpful short guidance when we could not / chose not to fetch
        print("\nSkipping third-party MP3 download (procedural pink noise was generated).")
        if chosen_manifest:
            print(f"No usable direct download URLs found in {chosen_manifest.name}.")
        print("To add real rain/fire/thunder:")
        print("  1. Visit the 7 Pixabay source pages listed in media_sources.default.json")
        print("  2. In DevTools → Network tab, trigger a download and copy the cdn.pixabay.com/audio/... URL")
        print("  3. cp media_sources.default.json media_sources.json   # then fill the 'url' fields")
        print("  4. python3 install.py --fetch-media")
        print("Or pass --no-fetch-media to silence this message on future runs.")

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
