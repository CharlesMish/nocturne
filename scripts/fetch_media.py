#!/usr/bin/env python3
"""
Download Nocturne's optional third-party ambient media from a local manifest.

Why this exists:
  Nocturne is a creative app, but a public source repo that includes raw .mp3
  files can look like a media redistribution channel. This script keeps the
  repo lightweight and lets each installer download upstream files directly.

What works without this script:
  `python3 install.py` generates `sounds/pinknoise.wav`, so the app can run
  immediately with procedural audio.

What this script adds:
  the seven optional rain/fire/thunder MP3s for the fixed Onsen/Sky mixer. It
  does not fetch Radio tracks; Radio is personal audio dropped into
  `sounds/radio/`.

Fast path:
  python scripts/fetch_media.py --init
  python scripts/fetch_media.py --yes

The fetcher first uses any direct download_url values you provide. If those are
missing, it tries to resolve current cdn.pixabay.com/audio/... or
cdn.pixabay.com/download/audio/... MP3 URLs from the committed source_page links
automatically. If Pixabay changes its page markup, it falls back to clear
manual instructions instead of saving bad files.

The script writes files into sounds/ using the exact filenames the mixer expects
and writes sounds/MEDIA_MANIFEST.generated.json with hashes/provenance receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "media_sources.json"
SOURCE_MANIFEST = ROOT / "media_sources.default.json"
EXAMPLE_MANIFEST = ROOT / "media_sources.example.json"
SOUNDS_DIR = ROOT / "sounds"
GENERATED_RECEIPTS = SOUNDS_DIR / "MEDIA_MANIFEST.generated.json"

EXPECTED_AMBIENT = {
    "calming_rain.mp3",
    "gentle_rain.mp3",
    "heavy_rain.mp3",
    "rainstorm.mp3",
    "heavy_storm.mp3",
    "thunder.mp3",
    "fireplace.mp3",
}

USER_AGENT = "Nocturne/0.1 (+https://github.com/CharlesMish/nocturne)"


def _entry_download_url(entry: dict[str, Any]) -> str:
    """Return the user-provided direct audio URL.

    New manifests should use download_url because it is harder to confuse with
    source_page. Older manifests that use url are still supported.
    """
    return str(entry.get("_resolved_download_url") or entry.get("download_url") or entry.get("url") or "").strip()


def _is_pixabay_source_page(url: str) -> bool:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    return host in {"pixabay.com", "www.pixabay.com"} and "/sound-effects/" in parsed.path


def _looks_like_mp3(first_bytes: bytes) -> bool:
    # ID3 tag or MPEG audio frame sync. This is deliberately small and cheap;
    # it catches the common "downloaded HTML as .mp3" mistake.
    return first_bytes.startswith(b"ID3") or (
        len(first_bytes) >= 2 and first_bytes[0] == 0xFF and (first_bytes[1] & 0xE0) == 0xE0
    )


def _looks_like_html(first_bytes: bytes) -> bool:
    head = first_bytes.lstrip()[:80].lower()
    return head.startswith((b"<!doctype html", b"<html", b"<head", b"<body"))


def is_usable_download_url(url: str, *, source_page: str = "") -> tuple[bool, str | None]:
    url = url.strip()
    if not url or url.startswith("TODO"):
        return False, "missing download_url"
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "download_url must start with http:// or https://"
    if "example.com" in url or "..." in url:
        return False, "download_url is still a placeholder"
    if any(ch.isspace() for ch in url):
        return False, "download_url contains whitespace"
    if "(" in url or ")" in url:
        return False, "download_url contains parentheses"

    normalized_url = url.rstrip("/")
    normalized_source = source_page.strip().rstrip("/")
    if normalized_source and normalized_url == normalized_source:
        return False, "download_url is the Pixabay source page, not the direct MP3"
    if _is_pixabay_source_page(url):
        return False, "download_url is a Pixabay web page; use a cdn.pixabay.com/audio/...mp3 or cdn.pixabay.com/download/audio/...mp3 URL"

    return True, None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    entries = data.get("files")
    if not isinstance(entries, list):
        raise ValueError("manifest must contain a 'files' list")
    return data


def _manifest_template() -> Path:
    if SOURCE_MANIFEST.exists():
        return SOURCE_MANIFEST
    if EXAMPLE_MANIFEST.exists():
        return EXAMPLE_MANIFEST
    raise FileNotFoundError("media_sources.default.json")


def _source_pages(manifest: dict[str, Any]) -> list[str]:
    pages: list[str] = []
    for entry in manifest.get("files", []):
        if not isinstance(entry, dict):
            continue
        page = str(entry.get("source_page", "")).strip()
        if page and page.startswith(("http://", "https://")):
            pages.append(page)
    return pages


def _source_page_id(source_page: str) -> str:
    """Return the numeric Pixabay media id from a source-page URL, when present."""
    parsed = urlparse(source_page.strip())
    match = re.search(r"-(\d+)/?$", parsed.path)
    return match.group(1) if match else ""


def _candidate_texts(raw: str) -> list[str]:
    """Generate decoded variants of a page body for URL extraction."""
    variants = [raw]
    # Pixabay often JSON-escapes slashes and ampersands inside hydrated state.
    variants.append(raw.replace(r"\/", "/"))
    variants.append(html.unescape(raw))
    variants.append(unquote(raw))
    variants.append(html.unescape(unquote(raw.replace(r"\/", "/"))))
    variants.append(raw.replace(r"\u0026", "&").replace(r"\/", "/"))

    seen: set[str] = set()
    unique: list[str] = []
    for value in variants:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def _clean_candidate_url(url: str) -> str:
    """Normalize a scraped CDN URL without being clever about query params."""
    url = html.unescape(url).replace(r"\/", "/").replace(r"\u0026", "&")
    # Trim common JSON/HTML punctuation that can cling to the end of a regex match.
    return url.rstrip(".,;)]}")


def extract_audio_urls(page_text: str, *, source_page: str = "") -> list[str]:
    """Extract probable Pixabay direct MP3 URLs from source-page HTML/JSON.

    The public Pixabay sound-effect page is a human-facing page, not a documented
    audio API. In practice, pages commonly include the current CDN audio URL in
    hydrated JSON. We prefer candidates containing the source page's numeric media
    id so related-track URLs do not win accidentally.
    """
    pattern = re.compile(
        r"https?://(?:cdn\.)?pixabay\.com/(?:download/)?audio/[^\s\"'<>]+?\.mp3(?:\?[^\s\"'<>]+)?",
        re.IGNORECASE,
    )
    found: list[str] = []
    seen: set[str] = set()
    for text in _candidate_texts(page_text):
        for match in pattern.finditer(text):
            candidate = _clean_candidate_url(match.group(0))
            if candidate not in seen:
                seen.add(candidate)
                found.append(candidate)

    media_id = _source_page_id(source_page)
    if media_id:
        found.sort(key=lambda u: (media_id not in u, "/audio/" not in u, len(u)))
    else:
        found.sort(key=lambda u: ("/audio/" not in u, len(u)))
    return found


def resolve_download_url_from_source_page(source_page: str) -> str:
    """Resolve a direct MP3 URL from a Pixabay sound-effect source page.

    This is a convenience resolver, not a public Pixabay API contract. It keeps
    install easy while preserving the safer provenance model: Nocturne downloads
    the media to sounds/ and serves local files instead of hotlinking Pixabay.
    """
    source_page = source_page.strip()
    if not source_page:
        raise RuntimeError("missing source_page")
    if not source_page.startswith(("http://", "https://")):
        raise RuntimeError("source_page must start with http:// or https://")

    request = urllib.request.Request(source_page, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        body = response.read().decode("utf-8", errors="replace")
    if "html" not in content_type and "json" not in content_type and not body.lstrip().startswith(("<", "{")):
        raise RuntimeError(f"source_page returned unexpected Content-Type: {content_type or 'unknown'}")

    candidates = extract_audio_urls(body, source_page=source_page)
    if not candidates:
        raise RuntimeError(
            "could not find a cdn.pixabay.com/audio/...mp3 or cdn.pixabay.com/download/audio/...mp3 URL in the source page; "
            "Pixabay may have changed its page markup"
        )
    return candidates[0]


def init_manifest(*, overwrite: bool, open_source_pages: bool) -> int:
    """Create media_sources.json from the committed source manifest.

    This is intentionally separate from fetching: the normal next step is an
    automatic best-effort resolve/download, with manual URL capture available
    only as a fallback.
    """
    template = _manifest_template()
    if DEFAULT_MANIFEST.exists() and not overwrite:
        print(f"{DEFAULT_MANIFEST.name} already exists; keeping it.")
        print("Use --overwrite to recreate it from the committed source manifest.")
    else:
        shutil.copyfile(template, DEFAULT_MANIFEST)
        print(f"Created {DEFAULT_MANIFEST.name} from {template.name}.")

    try:
        manifest = _load_manifest(DEFAULT_MANIFEST)
    except Exception as exc:  # noqa: BLE001 - CLI should show a plain error
        print(f"Could not read {DEFAULT_MANIFEST.name}: {exc}", file=sys.stderr)
        return 2

    pages = _source_pages(manifest)
    print("\nWhat works now:")
    print("  - Nocturne can already run with generated pink noise after python3 install.py.")
    print("  - Radio tracks are not fetched here; drop personal audio into sounds/radio/.")
    print("\nNext steps for the optional ambient MP3s:")
    print("  1. Run: python scripts/fetch_media.py --yes")
    print("     or: python3 install.py --fetch-media")
    print("  2. The fetcher will try to resolve direct CDN MP3 URLs from the source pages automatically.")
    print("  3. If auto-resolution fails, open the listed source pages and fill download_url manually.")

    if pages:
        print("Source pages:")
        for page in pages:
            print(f"  - {page}")

    if open_source_pages and pages:
        print("\nOpening source pages in your default browser…")
        for page in pages:
            webbrowser.open_new_tab(page)

    return 0


def _download(url: str, dest: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        first = response.read(8192)

        if "text/html" in content_type or _looks_like_html(first):
            raise RuntimeError(
                "download_url returned HTML, not audio. You probably pasted the Pixabay "
                "source page. Open that page, play/download the sound, then copy the "
                "cdn.pixabay.com/audio/...mp3 or cdn.pixabay.com/download/audio/...mp3 "
                "request from DevTools → Network."
            )

        # Some hosts use application/octet-stream for MP3s, so allow either an
        # audio/* content type or MP3-looking bytes. Reject everything else.
        if "audio" not in content_type and not _looks_like_mp3(first):
            shown_type = content_type or "unknown"
            raise RuntimeError(f"download_url did not look like an MP3/audio file (Content-Type: {shown_type})")

        with dest.open("wb") as f:
            f.write(first)
            shutil.copyfileobj(response, f)


def _entry_status(entry: dict[str, Any]) -> str | None:
    filename = str(entry.get("filename", "")).strip()
    url = _entry_download_url(entry)
    source_page = str(entry.get("source_page", "")).strip()
    if not filename:
        return "missing filename"
    if filename not in EXPECTED_AMBIENT:
        return f"unexpected filename {filename!r}"
    ok, reason = is_usable_download_url(url, source_page=source_page)
    if not ok:
        return reason or "missing download_url"
    return None


def fetch_media(
    manifest_path: Path,
    *,
    yes: bool,
    overwrite: bool,
    dry_run: bool,
    resolve_source_pages: bool,
) -> int:
    manifest = _load_manifest(manifest_path)
    files = manifest["files"]
    SOUNDS_DIR.mkdir(exist_ok=True)

    valid_entries: list[dict[str, Any]] = []
    skipped: list[tuple[str, str]] = []
    resolved_count = 0

    for raw in files:
        if not isinstance(raw, dict):
            skipped.append(("<invalid>", "entry is not an object"))
            continue

        entry = dict(raw)
        filename = str(entry.get("filename", "<unnamed>"))
        reason = _entry_status(entry)
        if not reason:
            valid_entries.append(entry)
            continue

        source_page = str(entry.get("source_page", "")).strip()
        can_resolve = resolve_source_pages and source_page and filename in EXPECTED_AMBIENT
        if can_resolve:
            try:
                resolved_url = resolve_download_url_from_source_page(source_page)
                ok, resolved_reason = is_usable_download_url(resolved_url, source_page=source_page)
                if not ok:
                    raise RuntimeError(resolved_reason or "resolved URL was not usable")
                entry["_resolved_download_url"] = resolved_url
                valid_entries.append(entry)
                resolved_count += 1
                print(f"Resolved {filename} from source page.")
                continue
            except Exception as exc:  # noqa: BLE001 - keep CLI forgiving and readable
                skipped.append((filename, f"{reason}; auto-resolve failed: {exc}"))
                continue

        skipped.append((filename, reason))

    if resolved_count:
        print(f"Auto-resolved {resolved_count} direct MP3 URL(s) from source pages.\n")

    if skipped:
        print("Some manifest entries are incomplete and will be skipped:")
        for filename, reason in skipped:
            print(f"  - {filename}: {reason}")
        print()

    if not valid_entries:
        print("No downloadable media entries found (direct URLs were missing, placeholders, source pages, or could not be auto-resolved).")
        if manifest_path == DEFAULT_MANIFEST:
            print("The committed manifest contains source pages only; auto-resolution did not find current MP3 URLs.")
        else:
            rel = manifest_path.relative_to(ROOT) if manifest_path.is_relative_to(ROOT) else manifest_path
            print(f"Edit the 'download_url' fields in {rel} with fresh direct CDN MP3 links.")
        print("Fallback manual flow:")
        print("  1. python scripts/fetch_media.py --init --open-source-pages")
        print("  2. Open DevTools → Network on each source page, play/download the sound, copy the cdn.pixabay.com/audio/...mp3 or cdn.pixabay.com/download/audio/...mp3 URL")
        print("  3. Paste each URL into media_sources.json, then run python scripts/fetch_media.py --yes")
        return 2

    print("This will download these optional media files into sounds/:")
    for entry in valid_entries:
        print(f"  - {entry['filename']}  <=  {_entry_download_url(entry)}")
    print()

    if dry_run:
        print("Dry run only; nothing downloaded.")
        return 0

    if not yes:
        reply = input("Continue? [y/N] ").strip().lower()
        if reply not in {"y", "yes"}:
            print("Cancelled.")
            return 1

    receipts: list[dict[str, Any]] = []
    failed_downloads: list[tuple[str, str]] = []
    for entry in valid_entries:
        filename = str(entry["filename"])
        url = _entry_download_url(entry)
        dest = SOUNDS_DIR / filename
        if dest.exists() and not overwrite:
            print(f"Keeping existing {filename} (use --overwrite to replace)")
        else:
            print(f"Downloading {filename}…", flush=True)
            with tempfile.NamedTemporaryFile(delete=False, dir=str(SOUNDS_DIR)) as tmp:
                tmp_path = Path(tmp.name)
            try:
                _download(url, tmp_path)
                if tmp_path.stat().st_size == 0:
                    raise RuntimeError("downloaded file is empty")
                tmp_path.replace(dest)
            except Exception as exc:  # noqa: BLE001 - continue with the rest of the optional set
                tmp_path.unlink(missing_ok=True)
                failed_downloads.append((filename, str(exc)))
                print(f"  ! Skipped {filename}: {exc}", file=sys.stderr)
                continue

        receipts.append({
            "filename": filename,
            "url": url,
            "source_page": entry.get("source_page", ""),
            "creator": entry.get("creator", ""),
            "license": entry.get("license", ""),
            "permission_note": entry.get("permission_note", ""),
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "sha256": _sha256(dest),
            "bytes": dest.stat().st_size,
        })

    if failed_downloads:
        print("\nSome optional media files could not be downloaded:", file=sys.stderr)
        for filename, reason in failed_downloads:
            print(f"  - {filename}: {reason}", file=sys.stderr)

    if not receipts:
        print("No media files were downloaded or already present.", file=sys.stderr)
        print("Nocturne still works with generated pink noise.", file=sys.stderr)
        return 2

    generated = {
        "generated_by": "scripts/fetch_media.py",
        "manifest": str(manifest_path.relative_to(ROOT)) if manifest_path.is_relative_to(ROOT) else str(manifest_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": receipts,
    }
    GENERATED_RECEIPTS.write_text(json.dumps(generated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {GENERATED_RECEIPTS.relative_to(ROOT)}")
    if failed_downloads:
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Download optional Nocturne ambient media.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="media source manifest JSON")
    parser.add_argument("--yes", action="store_true", help="download without interactive confirmation")
    parser.add_argument("--overwrite", action="store_true", help="replace existing files, or recreate media_sources.json when used with --init")
    parser.add_argument("--dry-run", action="store_true", help="validate and print planned downloads")
    parser.add_argument("--no-resolve-source-pages", action="store_true", help="do not try to resolve direct MP3 URLs from Pixabay source pages automatically")
    parser.add_argument("--init", action="store_true", help="create media_sources.json from the committed source-page manifest and print next steps")
    parser.add_argument("--open-source-pages", action="store_true", help="open the seven source pages in your default browser when used with --init")
    args = parser.parse_args()

    if args.init:
        return init_manifest(overwrite=args.overwrite, open_source_pages=args.open_source_pages)

    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = (Path.cwd() / manifest_path).resolve()

    if not manifest_path.exists():
        if manifest_path == DEFAULT_MANIFEST:
            print(f"No {DEFAULT_MANIFEST.name} found.")
            print("Create the editable manifest and source-page checklist with:")
            print("  python scripts/fetch_media.py --init --open-source-pages")
            return 2
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    try:
        return fetch_media(manifest_path, yes=args.yes, overwrite=args.overwrite, dry_run=args.dry_run, resolve_source_pages=not args.no_resolve_source_pages)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
