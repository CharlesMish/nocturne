"""
Nocturne — five-mode sleep app (onsen, sky, radio, utility, dashboard).

Modes:
  * Onsen: the original ambient mixer + looping rain video
  * Sky:   the ambient mixer + a moon-phase / local-weather visual
  * Radio: a late-night personal broadcast playing tracks from ./sounds/radio/
  * Utility: a local Strudel code sketchbook stored in ./songs/; opens strudel.cc for playback
  * Dashboard: static embedded Raspberry Pi terminal/weather screen

Endpoints:
  GET  /              — the web UI
  GET  /api/sounds    — ambient mixer files in ./sounds/ (one level deep, so
                        ./sounds/radio/ is automatically excluded)
  GET  /api/radio     — tracks in ./sounds/radio/
  GET  /api/weather   — cached current weather from Open-Meteo (graceful fail)
  GET  /api/geocode   — small city/place search via Open-Meteo Geocoding
  GET  /api/config    — non-secret runtime config for the UI (lat/lon, label)
  GET/PUT /api/settings — server-persisted mode visibility / feature gates
  GET  /api/songs     — Strudel code sketch metadata list (gated by Utility setting)
  GET/POST/PUT/DELETE /api/songs/... — local sketchbook CRUD
  GET  /sounds/...    — static audio (subtree, so /sounds/radio/* works too)
  GET  /health        — liveness probe

Configuration (env vars, set in nocturne.service):
  NOCTURNE_LAT             fallback/default 41.8781  (Chicago)
  NOCTURNE_LON             fallback/default -87.6298
  NOCTURNE_LOCATION_NAME   fallback/default "Chicago"
  NOCTURNE_TIMEZONE        fallback/default "America/Chicago"
  NOCTURNE_TEMPERATURE_UNIT fallback/default "fahrenheit"
  NOCTURNE_WEATHER_TTL     default 600  (seconds)
"""
from __future__ import annotations

import os
import time
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import PlainTextResponse

ROOT = Path(__file__).parent
BUILD_INFO_PATH = ROOT / "nocturne_build.json"
STATIC_DIR = ROOT / "static"
SOUNDS_DIR = ROOT / "sounds"
RADIO_DIR = SOUNDS_DIR / "radio"
SONGS_DIR = ROOT / "songs"
CONFIG_DIR = ROOT / "config"
SETTINGS_PATH = CONFIG_DIR / "nocturne.json"


class NocturneSoundsStaticFiles(StaticFiles):
    """Static sound serving that hides curation intake from /sounds/*.

    The public app should serve generated/library/radio audio, not raw
    Freesound intake files staged in sounds/inbox/.
    """

    async def get_response(self, path: str, scope):  # type: ignore[override]
        if Path(path).parts[:1] == ("inbox",):
            return PlainTextResponse("Not found", status_code=404)
        return await super().get_response(path, scope)

AUDIO_EXTS = {".mp3", ".ogg", ".m4a", ".wav", ".opus", ".webm", ".flac"}

# --------------------------------------------------------------------------- #
#  Config (env-driven, with sane defaults).
# --------------------------------------------------------------------------- #
LATITUDE = float(os.getenv("NOCTURNE_LAT", "41.8781"))
LONGITUDE = float(os.getenv("NOCTURNE_LON", "-87.6298"))
LOCATION_NAME = os.getenv("NOCTURNE_LOCATION_NAME", "Chicago")
TIMEZONE = os.getenv("NOCTURNE_TIMEZONE", "America/Chicago")
TEMPERATURE_UNIT = os.getenv("NOCTURNE_TEMPERATURE_UNIT", "fahrenheit")
WEATHER_TTL = int(os.getenv("NOCTURNE_WEATHER_TTL", "600"))

# In-memory weather cache (no DB needed for a single-process bedside service).
_weather_cache: dict[str, Any] = {"data": None, "fetched_at": 0.0, "error": None}

DEFAULT_SETTINGS: dict[str, Any] = {
    "modes": {
        "onsen": True,
        "sky": True,
        "radio": True,
        "utility": False,
        "dashboard": False,
    },
    "location": {
        "label": LOCATION_NAME,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "timezone": TIMEZONE,
        "temperature_unit": TEMPERATURE_UNIT if TEMPERATURE_UNIT in {"fahrenheit", "celsius"} else "fahrenheit",
    }
}
VALID_MODE_KEYS = set(DEFAULT_SETTINGS["modes"].keys())
MAX_SONG_CODE_BYTES = 256 * 1024
MAX_LOCATION_LABEL_LEN = 80
MAX_TIMEZONE_LEN = 80


def _settings_copy() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_SETTINGS))


def _validate_location(raw: Any, *, strict: bool = False) -> dict[str, Any]:
    fallback = _settings_copy()["location"]
    if not isinstance(raw, dict):
        if strict:
            raise HTTPException(status_code=400, detail="location must be an object")
        return fallback

    location = dict(fallback)

    label = raw.get("label", fallback["label"])
    if not isinstance(label, str):
        if strict:
            raise HTTPException(status_code=400, detail="location label must be a string")
    else:
        label = label.strip()
        if not label or len(label) > MAX_LOCATION_LABEL_LEN:
            if strict:
                raise HTTPException(status_code=400, detail="location label must be 1-80 characters")
        else:
            location["label"] = label

    timezone = raw.get("timezone", fallback["timezone"])
    if not isinstance(timezone, str):
        if strict:
            raise HTTPException(status_code=400, detail="timezone must be a string")
    else:
        timezone = timezone.strip()
        if not timezone or len(timezone) > MAX_TIMEZONE_LEN:
            if strict:
                raise HTTPException(status_code=400, detail="timezone must be 1-80 characters")
        else:
            location["timezone"] = timezone

    for key, low, high in (("latitude", -90, 90), ("longitude", -180, 180)):
        value = raw.get(key, fallback[key])
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            if strict:
                raise HTTPException(status_code=400, detail=f"{key} must be a number")
            continue
        value = float(value)
        if value < low or value > high:
            if strict:
                raise HTTPException(status_code=400, detail=f"{key} must be between {low} and {high}")
            continue
        location[key] = value

    unit = raw.get("temperature_unit", fallback["temperature_unit"])
    if unit not in {"fahrenheit", "celsius"}:
        if strict:
            raise HTTPException(status_code=400, detail="temperature_unit must be fahrenheit or celsius")
    else:
        location["temperature_unit"] = unit

    return location


def _merge_settings(raw: Any) -> dict[str, Any]:
    settings = _settings_copy()
    if not isinstance(raw, dict):
        return settings
    modes = raw.get("modes")
    if isinstance(modes, dict):
        for key, value in modes.items():
            if key in VALID_MODE_KEYS and isinstance(value, bool):
                settings["modes"][key] = value
    if not any(settings["modes"].values()):
        settings["modes"]["onsen"] = True
    settings["location"] = _validate_location(raw.get("location"))
    return settings


def _load_settings() -> dict[str, Any]:
    try:
        raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _settings_copy()
    except json.JSONDecodeError:
        return _settings_copy()
    return _merge_settings(raw)


def _save_settings(settings: dict[str, Any]) -> dict[str, Any]:
    settings = _merge_settings(settings)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return settings


def _clear_weather_cache() -> None:
    _weather_cache["data"] = None
    _weather_cache["fetched_at"] = 0.0
    _weather_cache["error"] = None


def _mode_enabled(mode: str) -> bool:
    return bool(_load_settings()["modes"].get(mode, False))


def _require_utility_enabled() -> None:
    # Utility is the only public mode that writes files. When it is disabled,
    # hide the route surface rather than exposing a write API with 403s.
    if not _mode_enabled("utility"):
        raise HTTPException(status_code=404, detail="not found")


app = FastAPI(title="Nocturne")


DEFAULT_BUILD_INFO: dict[str, str] = {
    "version": "unknown",
    "channel": "alpha",
    "build_date_utc": "2026-06-09",
    "commit": "unknown",
    "commit_date_utc": "2026-06-09",
    "feedback_label": "unknown build · unknown date · unknown commit",
}


def _load_build_info() -> dict[str, str]:
    """Build identity for alpha feedback and tester bug reports."""
    data: dict[str, Any] = {}
    if BUILD_INFO_PATH.exists():
        try:
            loaded = json.loads(BUILD_INFO_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except Exception:
            # Build metadata is helpful, not critical. Fall back quietly.
            data = {}

    info = {**DEFAULT_BUILD_INFO, **{k: str(v) for k, v in data.items() if isinstance(v, (str, int, float))}}
    if os.getenv("NOCTURNE_VERSION"):
        info["version"] = os.environ["NOCTURNE_VERSION"]
    if os.getenv("NOCTURNE_COMMIT"):
        info["commit"] = os.environ["NOCTURNE_COMMIT"]
    if os.getenv("NOCTURNE_BUILD_DATE"):
        info["build_date_utc"] = os.environ["NOCTURNE_BUILD_DATE"]
    if os.getenv("NOCTURNE_COMMIT_DATE"):
        info["commit_date_utc"] = os.environ["NOCTURNE_COMMIT_DATE"]

    commit_day = info.get("commit_date_utc", "")[:10] or info.get("build_date_utc", "")[:10]
    info["feedback_label"] = info.get("feedback_label") or f"v{info['version']} · {commit_day} · {info['commit']}"
    return {k: str(v) for k, v in info.items()}


def _local_ready_url() -> str:
    host = os.getenv("NOCTURNE_HOST", "127.0.0.1")
    port = os.getenv("NOCTURNE_PORT", "8000")
    open_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    return f"http://{open_host}:{port}/"


@app.on_event("startup")
def print_ready_message() -> None:
    # Uvicorn already prints bind details; this adds a friendlier copy/paste line
    # for non-technical alpha testers and Windows launcher users.
    print(f"Nocturne is ready at {_local_ready_url()}", flush=True)


# --------------------------------------------------------------------------- #
#  Health & config
# --------------------------------------------------------------------------- #
@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/version")
def version() -> dict[str, str]:
    """Copyable build identity for alpha feedback reports."""
    return _load_build_info()


@app.get("/api/config")
def config() -> dict[str, Any]:
    """Non-secret config the UI needs."""
    location = _load_settings()["location"]
    return {
        **location,
        "location_name": location["label"],
    }


@app.get("/api/settings")
def get_settings() -> dict[str, Any]:
    """Server-persisted feature gates used by the simple Settings UI."""
    return _load_settings()


@app.put("/api/settings")
async def put_settings(request: Request) -> dict[str, Any]:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="settings object required")
    current = _load_settings()
    previous_location = dict(current["location"])
    incoming_modes = payload.get("modes")
    if incoming_modes is not None:
        if not isinstance(incoming_modes, dict):
            raise HTTPException(status_code=400, detail="modes must be an object")
        for key, value in incoming_modes.items():
            if key not in VALID_MODE_KEYS:
                raise HTTPException(status_code=400, detail=f"unknown mode: {key}")
            if not isinstance(value, bool):
                raise HTTPException(status_code=400, detail=f"mode {key} must be true or false")
            current["modes"][key] = value
    incoming_location = payload.get("location")
    if incoming_location is not None:
        current["location"] = _validate_location(incoming_location, strict=True)
    if not any(current["modes"].values()):
        raise HTTPException(status_code=400, detail="at least one mode must remain enabled")
    saved = _save_settings(current)
    if saved["location"] != previous_location:
        _clear_weather_cache()
    return saved


# --------------------------------------------------------------------------- #
#  Audio listings
# --------------------------------------------------------------------------- #
def _audio_entry(path: Path, url_prefix: str) -> dict[str, str]:
    return {
        "id": path.name,
        "name": path.stem.replace("-", " ").replace("_", " ").title(),
        "url": f"{url_prefix}/{quote(path.name, safe='')}",
    }


@app.get("/api/sounds")
def list_sounds() -> list[dict[str, str]]:
    """Ambient mixer files. iterdir() is non-recursive, so ./sounds/radio/
    is automatically excluded — its contents live in /api/radio."""
    if not SOUNDS_DIR.exists():
        return []
    return [
        _audio_entry(p, "/sounds")
        for p in sorted(SOUNDS_DIR.iterdir(), key=lambda p: p.name.lower())
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    ]


@app.get("/api/radio")
def list_radio() -> list[dict[str, str]]:
    """Tracks for the radio mode. Drop audio files into ./sounds/radio/."""
    if not RADIO_DIR.exists():
        return []
    return [
        _audio_entry(p, "/sounds/radio")
        for p in sorted(RADIO_DIR.iterdir(), key=lambda p: p.name.lower())
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    ]




# --------------------------------------------------------------------------- #
#  Utility / Strudel sketchbook
# --------------------------------------------------------------------------- #
VALID_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,59}$")


def _check_slug(slug: str) -> None:
    if not VALID_SLUG.fullmatch(slug or ""):
        raise HTTPException(status_code=400, detail="invalid slug")


def _song_dir(slug: str) -> Path:
    _check_slug(slug)
    return SONGS_DIR / slug


def _read_song(slug: str) -> dict[str, Any]:
    folder = _song_dir(slug)
    meta_path = folder / "meta.json"
    code_path = folder / "code.js"
    if not folder.exists():
        raise HTTPException(status_code=404, detail="not found")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        code = code_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not found")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"bad meta.json for {slug}: {exc}")
    return {"slug": slug, "meta": meta, "code": code}


def _write_song(slug: str, meta: dict[str, Any], code: str) -> None:
    if len(str(code).encode("utf-8")) > MAX_SONG_CODE_BYTES:
        raise HTTPException(status_code=413, detail="song code is too large")
    folder = _song_dir(slug)
    folder.mkdir(parents=True, exist_ok=True)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    meta = dict(meta or {})
    meta["updatedAt"] = now
    meta.setdefault("createdAt", now)
    (folder / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (folder / "code.js").write_text(str(code), encoding="utf-8")


@app.get("/api/songs")
def list_songs() -> list[dict[str, Any]]:
    """Sketchbook library. Most recently edited first."""
    _require_utility_enabled()
    if not SONGS_DIR.exists():
        return []
    songs: list[dict[str, Any]] = []
    for folder in sorted(SONGS_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not folder.is_dir() or not VALID_SLUG.fullmatch(folder.name):
            continue
        try:
            meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        except Exception:
            continue
        songs.append({"slug": folder.name, **meta})
    songs.sort(key=lambda item: item.get("updatedAt", ""), reverse=True)
    return songs


@app.get("/api/songs/{slug}")
def get_song(slug: str) -> dict[str, Any]:
    _require_utility_enabled()
    return _read_song(slug)


@app.post("/api/songs")
async def create_song(request: Request) -> dict[str, str]:
    _require_utility_enabled()
    payload = await request.json()
    slug = payload.get("slug", "")
    _check_slug(slug)
    folder = SONGS_DIR / slug
    if folder.exists():
        raise HTTPException(status_code=409, detail="a song with this slug already exists")
    meta = payload.get("meta")
    code = payload.get("code")
    if not isinstance(meta, dict) or not isinstance(code, str):
        raise HTTPException(status_code=400, detail="meta and code required")
    _write_song(slug, meta, code)
    return {"slug": slug}


@app.put("/api/songs/{slug}")
async def update_song(slug: str, request: Request) -> dict[str, str]:
    _require_utility_enabled()
    _check_slug(slug)
    existing = _read_song(slug)
    payload = await request.json()
    meta = payload.get("meta")
    code = payload.get("code")
    if not isinstance(meta, dict) or not isinstance(code, str):
        raise HTTPException(status_code=400, detail="meta and code required")
    meta = dict(meta)
    if existing["meta"].get("createdAt"):
        meta["createdAt"] = existing["meta"]["createdAt"]
    _write_song(slug, meta, code)
    return {"slug": slug}


@app.post("/api/songs/{slug}/duplicate")
async def duplicate_song(slug: str, request: Request) -> dict[str, str]:
    _require_utility_enabled()
    src = _read_song(slug)
    payload = await request.json()
    new_slug = payload.get("newSlug", "")
    _check_slug(new_slug)
    if (SONGS_DIR / new_slug).exists():
        raise HTTPException(status_code=409, detail="newSlug already exists")
    new_meta = dict(src["meta"])
    new_meta["title"] = payload.get("title") or f"{new_meta.get('title') or slug} (copy)"
    new_meta.pop("createdAt", None)
    _write_song(new_slug, new_meta, src["code"])
    return {"slug": new_slug}


@app.delete("/api/songs/{slug}")
def delete_song(slug: str) -> dict[str, bool]:
    _require_utility_enabled()
    folder = _song_dir(slug)
    if not folder.exists():
        raise HTTPException(status_code=404, detail="not found")
    shutil.rmtree(folder)
    return {"ok": True}


# --------------------------------------------------------------------------- #
#  Weather (Open-Meteo, no API key)
# --------------------------------------------------------------------------- #
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"


def _normalise_geocode_result(item: dict[str, Any]) -> dict[str, Any] | None:
    name = item.get("name")
    latitude = item.get("latitude")
    longitude = item.get("longitude")
    if not isinstance(name, str) or not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return None
    admin1 = item.get("admin1") if isinstance(item.get("admin1"), str) else ""
    country = item.get("country") if isinstance(item.get("country"), str) else ""
    timezone = item.get("timezone") if isinstance(item.get("timezone"), str) else ""
    label = ", ".join(part for part in (name, admin1, country) if part)
    return {
        "label": label or name,
        "name": name,
        "admin1": admin1,
        "country": country,
        "latitude": float(latitude),
        "longitude": float(longitude),
        "timezone": timezone,
    }


@app.get("/api/geocode")
async def geocode(q: str) -> dict[str, Any]:
    query = q.strip()
    if len(query) < 2 or len(query) > 80:
        raise HTTPException(status_code=400, detail="search query must be 2-80 characters")
    params = {
        "name": query,
        "count": 5,
        "language": "en",
        "format": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(OPEN_METEO_GEOCODE_URL, params=params)
            r.raise_for_status()
            payload = r.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"place search unavailable: {exc}") from exc

    raw_results = payload.get("results", []) if isinstance(payload, dict) else []
    if not isinstance(raw_results, list):
        raw_results = []
    results = []
    for item in raw_results[:5]:
        if isinstance(item, dict):
            result = _normalise_geocode_result(item)
            if result is not None:
                results.append(result)
    return {"results": results}


async def _fetch_weather() -> dict[str, Any]:
    location = _load_settings()["location"]
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": "temperature_2m,weather_code,cloud_cover,is_day,wind_speed_10m",
        "timezone": location["timezone"],
        "temperature_unit": location["temperature_unit"],
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        r = await client.get(OPEN_METEO_URL, params=params)
        r.raise_for_status()
        payload = r.json()
    current = payload.get("current", {}) or {}
    return {
        "weather_code": current.get("weather_code"),
        "cloud_cover": current.get("cloud_cover"),
        "temperature": current.get("temperature_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "is_day": current.get("is_day"),
        "time": current.get("time"),
        "timezone": payload.get("timezone"),
        "location_name": location["label"],
        "temperature_unit": location["temperature_unit"],
    }


@app.get("/api/weather")
async def get_weather() -> dict[str, Any]:
    """Cached current weather. Returns stale data on transient failure
    and {ok: false, ...} only when we have nothing usable at all."""
    now = time.time()
    age = now - _weather_cache["fetched_at"]
    have = _weather_cache["data"] is not None

    if have and age < WEATHER_TTL:
        return {"ok": True, "cached": True, "age_seconds": int(age),
                **_weather_cache["data"]}

    try:
        data = await _fetch_weather()
        _weather_cache["data"] = data
        _weather_cache["fetched_at"] = now
        _weather_cache["error"] = None
        return {"ok": True, "cached": False, "age_seconds": 0, **data}
    except Exception as exc:
        _weather_cache["error"] = str(exc)
        if have:
            return {"ok": True, "cached": True, "stale": True,
                    "age_seconds": int(age), "error": str(exc),
                    **_weather_cache["data"]}
        location = _load_settings()["location"]
        return {"ok": False, "error": str(exc), "location_name": location["label"], "temperature_unit": location["temperature_unit"]}


# Order matters: specific paths first.
app.mount("/sounds", NocturneSoundsStaticFiles(directory=SOUNDS_DIR), name="sounds")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
