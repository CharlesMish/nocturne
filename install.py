#!/usr/bin/env python3
"""
Nocturne installer for Raspberry Pi / macOS / Linux / Windows.

It intentionally does not depend on third-party downloads. Instead it:
  1. Creates/uses .venv and installs Python dependencies.
  2. Creates sounds/, sounds/library/, sounds/inbox/, sounds/radio/, provenance/, songs/, and config/.
  3. Writes a default config/nocturne.json if one does not exist.
  4. Generates the procedural starter ambience pack locally.
  5. Optionally runs the legacy Pixabay fetcher for old fixed filenames.

Run:
  python3 install.py

Windows:
  Double-click "Install Nocturne.bat", then "Start Nocturne.bat".

Media fetching (legacy compatibility):
  - python3 install.py                 → generates the procedural starter pack; no third-party downloads
  - python3 install.py --fetch-media    → explicitly try the legacy Pixabay fetcher
  - python3 install.py --no-fetch-media → same as default, kept for scripted installs

The preferred release path is now curated CC0/user-owned sounds in sounds/library/.
The old fetcher only exists for the legacy fixed Pixabay filenames.
"""
from __future__ import annotations

import argparse
import json
import platform
import shlex
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

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


def run_fetch_media(cmd: list[str | Path]) -> None:
    printable = " ".join(shlex.quote(str(c)) for c in cmd)
    print(f"\n$ {printable}", flush=True)
    result = subprocess.run([str(c) for c in cmd], cwd=ROOT, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.returncode == 0:
        return

    # Optional ambience must never block installation. The fetcher may fail
    # because Pixabay changed page markup, rejected a headless request, returned
    # HTML for a CDN URL, or because one file failed while others succeeded.
    # In all of those cases Nocturne should still finish with generated noise.
    print("\nOptional ambient MP3s were not all downloaded.")
    print("Nocturne is still installed and will run with the procedural starter pack.")
    print("To add the full ambience set later:")
    print("  1. python scripts/fetch_media.py --init --open-source-pages")
    print("  2. Paste fresh cdn.pixabay.com/audio/...mp3 or cdn.pixabay.com/download/audio/...mp3 URLs into media_sources.json if needed")
    print("  3. python3 install.py --fetch-media")


def ensure_venv() -> Path:
    if not VENV.exists():
        run([sys.executable, "-m", "venv", VENV])
    python = _bin("python")
    if not python.exists():
        raise RuntimeError(f"virtualenv python not found: {python}")
    return python


def _is_pixabay_source_page(url: str) -> bool:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    return host in {"pixabay.com", "www.pixabay.com"} and "/sound-effects/" in parsed.path


def is_usable_download_url(url: str, *, source_page: str = "") -> bool:
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
    if source_page.strip().rstrip("/") and url.rstrip("/") == source_page.strip().rstrip("/"):
        return False
    if _is_pixabay_source_page(url):
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
        url = str(entry.get("download_url") or entry.get("url") or "")
        source_page = str(entry.get("source_page", ""))
        if is_usable_download_url(url, source_page=source_page):
            return True
    return False


def manifest_has_source_pages(path: Path) -> bool:
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
        page = str(entry.get("source_page", "")).strip()
        if page.startswith(("http://", "https://")):
            return True
    return False


def main() -> int:
    if sys.version_info < (3, 10):
        print("Nocturne needs Python 3.10 or newer.")
        print(f"You are running Python {sys.version.split()[0]}.")
        return 1

    parser = argparse.ArgumentParser(description="Install Nocturne locally.")
    parser.add_argument("--skip-deps", action="store_true", help="do not install requirements.txt")
    parser.add_argument("--skip-noise", action="store_true", help="do not generate procedural starter beds")
    parser.add_argument("--noise-seconds", type=int, default=180, help="duration per generated starter file; default: 180")
    parser.add_argument("--fetch-media", action="store_true", help="force download of ambience from media_sources.json (or .default.json)")
    parser.add_argument("--no-fetch-media", action="store_true", help="never attempt to download third-party MP3s, even if a manifest with real URLs exists")
    parser.add_argument("--overwrite-media", action="store_true", help="replace existing downloaded media")
    parser.add_argument("--host", default="127.0.0.1", help="host printed in the final run command")
    parser.add_argument("--port", default="8000", help="port printed in the final run command")
    args = parser.parse_args()
    if args.noise_seconds < 1:
        parser.error("--noise-seconds must be at least 1")

    (ROOT / "sounds").mkdir(exist_ok=True)
    (ROOT / "sounds" / "library").mkdir(exist_ok=True)
    (ROOT / "sounds" / "inbox").mkdir(exist_ok=True)
    (ROOT / "sounds" / "radio").mkdir(exist_ok=True)
    (ROOT / "provenance").mkdir(exist_ok=True)
    (ROOT / "provenance" / "screenshots").mkdir(parents=True, exist_ok=True)
    (ROOT / "provenance" / "originals").mkdir(parents=True, exist_ok=True)
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

    # Media fetch decision: legacy Pixabay fetching is explicit-only.
    media_manifest = ROOT / "media_sources.json"
    default_manifest = ROOT / "media_sources.default.json"

    chosen_manifest = None
    if media_manifest.exists():
        chosen_manifest = media_manifest
    elif default_manifest.exists():
        chosen_manifest = default_manifest

    has_real_urls = manifest_has_downloads(chosen_manifest) if chosen_manifest else False
    should_fetch_media = (not args.no_fetch_media) and args.fetch_media and bool(chosen_manifest)

    if should_fetch_media and chosen_manifest:
        cmd: list[str | Path] = [python, ROOT / "scripts" / "fetch_media.py", "--yes", "--manifest", chosen_manifest]
        if args.overwrite_media:
            cmd.append("--overwrite")
        run_fetch_media(cmd)
    elif args.fetch_media and not chosen_manifest:
        print("\nLegacy media fetch requested, but no media_sources manifest was found.")
    elif not args.no_fetch_media:
        print("\nSkipping legacy third-party MP3 download; procedural starter pack was generated.")
        if chosen_manifest and not has_real_urls:
            print(f"{chosen_manifest.name} is a deprecated placeholder manifest with no direct download URLs.")
        print("Preferred path for real rain/fire/night sounds is the bundled Core Sound Pack in sounds/library/.")

    print("\nNocturne is installed.")
    if platform.system().lower().startswith("win"):
        print("Run it with:")
        print(f"  .venv\\Scripts\\python.exe run_nocturne.py --host {args.host} --port {args.port}")
        print('Or double-click "Start Nocturne.bat".')
    else:
        print("Run it with:")
        print(f"  .venv/bin/python run_nocturne.py --host {args.host} --port {args.port}")
    if args.host == "127.0.0.1":
        print("\nFor LAN access from a phone/tablet, run with --host 0.0.0.0 deliberately.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode)
