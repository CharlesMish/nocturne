"""
Nocturne — sleep sounds web app.

This is the entire backend. It does three things:
  1. Lists the audio files in ./sounds/ via /api/sounds
  2. Serves those audio files at /sounds/<filename>
  3. Serves the web UI (static/index.html) at /

Add a new sound by dropping any .mp3/.ogg/.m4a/.wav file into ./sounds/.
No restart needed — refresh the browser page and the list is read again.
"""
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "static"
SOUNDS_DIR = ROOT / "sounds"

AUDIO_EXTS = {".mp3", ".ogg", ".m4a", ".wav", ".opus", ".webm", ".flac"}

app = FastAPI(title="Nocturne")


@app.get("/health")
def health():
    """Tiny endpoint for checking whether the service is alive."""
    return {"ok": True}


@app.get("/api/sounds")
def list_sounds():
    """Return every audio file in the sounds/ directory."""
    if not SOUNDS_DIR.exists():
        return []

    sounds = []
    for path in sorted(SOUNDS_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTS:
            continue

        # Use the full filename as the ID so rain.mp3 and rain.wav don't collide.
        # URL-encode the filename so spaces, #, ?, etc. are safe in the browser.
        sounds.append({
            "id": path.name,
            # Turn "rain-on-tent" or "rain_on_tent" into "Rain On Tent"
            "name": path.stem.replace("-", " ").replace("_", " ").title(),
            "url": f"/sounds/{quote(path.name, safe='')}",
        })
    return sounds


# The order of these mounts matters: more specific paths first.
app.mount("/sounds", StaticFiles(directory=SOUNDS_DIR), name="sounds")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
