#!/usr/bin/env python3
"""Non-destructive FastAPI smoke test for Nocturne's release-critical routes."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402
import main as nocturne  # noqa: E402


def expect(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def main() -> int:
    checks: list[str] = []
    bundled_song = nocturne._read_song("evening-loop")
    expect(
        isinstance(bundled_song["meta"], dict) and isinstance(bundled_song["code"], str),
        "bundled Utility song metadata and code remain readable",
        checks,
    )
    invalid_env = os.environ.copy()
    invalid_env.update({
        "NOCTURNE_LAT": "north",
        "NOCTURNE_LON": "nan",
        "NOCTURNE_WEATHER_TTL": "0",
    })
    env_probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json, main; "
                "print(json.dumps([main.LATITUDE, main.LONGITUDE, main.WEATHER_TTL]))"
            ),
        ],
        cwd=ROOT,
        env=invalid_env,
        capture_output=True,
        text=True,
        check=True,
    )
    fallback_values = json.loads(env_probe.stdout.strip().splitlines()[-1])
    expect(
        fallback_values == [41.8781, -87.6298, 600],
        "invalid numeric environment config falls back without crashing startup",
        checks,
    )

    with tempfile.TemporaryDirectory(prefix="nocturne-runtime-smoke-") as temp:
        temp_root = Path(temp)
        nocturne.CONFIG_DIR = temp_root / "config"
        nocturne.SETTINGS_PATH = nocturne.CONFIG_DIR / "nocturne.json"
        nocturne.SONGS_DIR = temp_root / "songs"
        nocturne._clear_weather_cache()

        ready_output = StringIO()
        with redirect_stdout(ready_output), TestClient(nocturne.app) as client:
            response = client.get("/health")
            expect(response.status_code == 200 and response.json() == {"ok": True}, "health endpoint returns ok", checks)

            build = json.loads((ROOT / "nocturne_build.json").read_text(encoding="utf-8"))
            response = client.get("/api/version")
            expect(response.status_code == 200, "version endpoint is available", checks)
            expect(response.json().get("feedback_label") == build["feedback_label"], "API build label matches canonical build JSON", checks)

            response = client.get("/")
            expect(response.status_code == 200, "main page is served", checks)
            expect('/nocturne-polish.css' in response.text, "main page loads the served polish stylesheet", checks)
            expect("fonts.googleapis.com" not in response.text and "fonts.gstatic.com" not in response.text, "main page has no external font dependency", checks)
            dashboard = client.get("/dashboard.html")
            expect(
                dashboard.status_code == 200 and "fonts.googleapis.com" not in dashboard.text and "fonts.gstatic.com" not in dashboard.text,
                "optional Dashboard has no external font dependency",
                checks,
            )

            response = client.get("/nocturne-polish.css")
            expect(response.status_code == 200 and ":focus-visible" in response.text, "polish stylesheet is reachable and contains focus treatment", checks)
            for font in ("fraunces-latin.woff2", "fraunces-italic-latin.woff2", "manrope-latin.woff2", "jetbrains-mono-latin.woff2"):
                asset = client.get(f"/fonts/{font}")
                expect(asset.status_code == 200 and asset.content.startswith(b"wOF2"), f"local font is served: {font}", checks)

            active_profile = client.get("/api/profile").json()
            expected_short_name = "Nocturne Pi" if active_profile.get("id") == "nocturne-pi" else "Nocturne"
            response = client.get("/manifest.webmanifest")
            expect(response.status_code == 200 and response.json().get("short_name") == expected_short_name, "profile-specific web app manifest is served", checks)
            for icon in ("/icons/nocturne-192.png", "/icons/nocturne-512.png", "/icons/nocturne-maskable-512.png"):
                asset = client.get(icon)
                expect(asset.status_code == 200 and asset.content.startswith(b"\x89PNG"), f"install icon is served: {icon}", checks)
            still = client.get("/rain-still.webp")
            expect(still.status_code == 200 and still.content.startswith(b"RIFF"), "Pi-compatible rain still is served", checks)
            video = client.get("/rain.mp4")
            if active_profile.get("visuals", {}).get("rain_video", True):
                expect(video.status_code == 200 and 0 < len(video.content) < 4_000_000, "optimized rain video is served below 4 MB", checks)
            else:
                expect(video.status_code == 404, "Pi package omits the disabled rain video", checks)

            response = client.get("/sounds/sound_library.json")
            expect(response.status_code == 200, "canonical sound manifest is publicly readable", checks)
            manifest = response.json()
            expect(len(manifest.get("default_slots", [])) == 8, "manifest exposes exactly eight defaults", checks)
            by_id = {sound["id"]: sound for sound in manifest.get("sounds", [])}
            for sound_id in manifest["default_slots"]:
                source = by_id[sound_id]["src"]
                asset = client.get(source)
                expect(asset.status_code == 200 and len(asset.content) > 0, f"default asset is served: {sound_id}", checks)

            for casing in ("inbox", "Inbox", "INBOX", "iNbOx"):
                denied = client.get(f"/sounds/{casing}/README.md")
                expect(
                    denied.status_code == 404
                    and denied.text == "Sound intake is not public"
                    and denied.headers.get("content-type", "").startswith("text/plain"),
                    f"custom intake denial handles first-segment casing: {casing}",
                    checks,
                )
            for path in (
                "/sounds/%69nbox/README.md",
                "/sounds/library/%2e%2e/inbox/README.md",
                "/sounds/library/%2E%2E/Inbox/README.md",
            ):
                denied = client.get(path)
                expect(
                    denied.status_code == 404 and denied.text == "Sound intake is not public",
                    f"encoded/traversal intake path is denied by the custom guard: {path}",
                    checks,
                )

            settings = client.get("/api/settings").json()
            expect(settings["modes"] == {"onsen": True, "sky": True, "radio": True, "utility": False, "dashboard": False}, "default profile exposes only Onsen, Sky, and Radio", checks)
            expect(client.get("/api/songs").status_code == 404, "Utility write surface is hidden while disabled", checks)

            invalid = client.put("/api/settings", json={"modes": {key: False for key in settings["modes"]}})
            expect(invalid.status_code == 400, "settings reject disabling every mode", checks)
            invalid = client.put("/api/settings", json={"modes": {"unknown": True}})
            expect(invalid.status_code == 400, "settings reject unknown modes", checks)

            enabled = client.put("/api/settings", json={"modes": {"utility": True}})
            expect(enabled.status_code == 200 and enabled.json()["modes"]["utility"] is True, "Utility can be deliberately enabled", checks)
            expect(client.get("/api/songs").status_code == 200, "Utility route becomes available only after enablement", checks)

            base_payload = {
                "slug": "base-song",
                "meta": {
                    "title": "Base song",
                    "artist": "Nocturne",
                    "bpm": 72,
                    "key": "C minor",
                    "tags": ["local"],
                    "notes": "fixture",
                    "transpose": 0,
                    "createdAt": "caller-controlled",
                },
                "code": 'note("c3")',
            }
            created = client.post("/api/songs", json=base_payload)
            expect(created.status_code == 200, "Utility create accepts a valid object body", checks)
            stored_base = client.get("/api/songs/base-song").json()
            expect(
                stored_base["meta"]["createdAt"] != "caller-controlled"
                and stored_base["meta"]["updatedAt"],
                "Utility timestamps remain server-managed",
                checks,
            )
            updated = client.put(
                "/api/songs/base-song",
                json={"meta": {**base_payload["meta"], "title": "Updated"}, "code": 'note("d3")'},
            )
            expect(updated.status_code == 200, "Utility update accepts a valid object body", checks)
            duplicated = client.post(
                "/api/songs/base-song/duplicate",
                json={"newSlug": "base-song-copy", "title": "Copied"},
            )
            expect(duplicated.status_code == 200, "Utility duplicate accepts a valid object body", checks)
            numeric_slug = client.post(
                "/api/songs",
                json={"slug": 7, "meta": {"title": "invalid slug"}, "code": "x"},
            )
            expect(numeric_slug.status_code == 400, "Utility rejects a non-string slug without HTTP 500", checks)

            invalid_json_bodies = {
                "array": "[]",
                "string": '"text"',
                "number": "1",
                "null": "null",
                "malformed": '{"broken":',
            }
            write_routes = (
                ("POST", "/api/songs"),
                ("PUT", "/api/songs/base-song"),
                ("POST", "/api/songs/base-song/duplicate"),
            )
            for method, path in write_routes:
                for label, raw in invalid_json_bodies.items():
                    rejected = client.request(
                        method,
                        path,
                        content=raw,
                        headers={"content-type": "application/json"},
                    )
                    expect(
                        rejected.status_code == 400,
                        f"{method} {path} rejects {label} JSON with HTTP 400",
                        checks,
                    )

            oversized_meta = client.post(
                "/api/songs",
                json={"slug": "large-meta", "meta": {"notes": "x" * (nocturne.MAX_SONG_META_BYTES + 1)}, "code": "x"},
            )
            expect(oversized_meta.status_code == 413, "Utility rejects metadata above 32 KiB", checks)
            deep_meta = {"a": {"b": {"c": {"d": {"e": "too deep"}}}}}
            excessive_depth = client.post(
                "/api/songs",
                json={"slug": "deep-meta", "meta": deep_meta, "code": "x"},
            )
            expect(excessive_depth.status_code == 400, "Utility rejects metadata beyond four container levels", checks)
            oversized_code = client.post(
                "/api/songs",
                json={"slug": "large-code", "meta": {"title": "large"}, "code": "x" * (nocturne.MAX_SONG_CODE_BYTES + 1)},
            )
            expect(oversized_code.status_code == 413, "Utility preserves the 256 KiB code cap", checks)

            before_song_failure = nocturne._read_song("base-song")
            real_replace = os.replace
            song_folder = nocturne.SONGS_DIR / "base-song"

            def fail_staged_song_replace(source, destination):
                source_path = Path(source)
                if Path(destination) == song_folder and source_path.name.endswith(".tmp"):
                    raise OSError("simulated staged song replacement failure")
                return real_replace(source, destination)

            try:
                with patch.object(nocturne.os, "replace", side_effect=fail_staged_song_replace):
                    nocturne._write_song(
                        "base-song",
                        {"title": "should not replace"},
                        'note("e3")',
                        created_at=before_song_failure["meta"]["createdAt"],
                    )
            except OSError:
                pass
            else:
                raise AssertionError("simulated staged song replacement failure did not propagate")
            expect(
                nocturne._read_song("base-song") == before_song_failure,
                "failed staged update preserves the previous readable song pair",
                checks,
            )
            expect(
                not list(nocturne.SONGS_DIR.glob(".*.tmp"))
                and not list(nocturne.SONGS_DIR.glob(".*.backup")),
                "song writes leave no staging files after success or simulated failure",
                checks,
            )

            with patch.object(nocturne, "_clear_weather_cache", wraps=nocturne._clear_weather_cache) as clear_cache:
                unchanged = client.put("/api/settings", json={"modes": {"utility": True}})
                expect(unchanged.status_code == 200 and clear_cache.call_count == 0, "omitting location leaves it unchanged without clearing weather", checks)

                starting_location = unchanged.json()["location"]
                label_only = client.put("/api/settings", json={"location": {"label": "Bedroom"}})
                expected_label_only = {**starting_location, "label": "Bedroom"}
                expect(label_only.status_code == 200 and label_only.json()["location"] == expected_label_only, "label-only location update preserves omitted fields", checks)
                expect(clear_cache.call_count == 1, "weather cache clears after a real location change", checks)

                repeated = client.put("/api/settings", json={"location": {"label": "Bedroom"}})
                expect(repeated.status_code == 200 and clear_cache.call_count == 1, "weather cache does not clear when resulting location is unchanged", checks)

                coordinate_only = client.put("/api/settings", json={"location": {"latitude": 12.5}})
                expect(
                    coordinate_only.status_code == 200
                    and coordinate_only.json()["location"] == {**expected_label_only, "latitude": 12.5},
                    "coordinate-only location update preserves omitted fields",
                    checks,
                )

                complete_location = {
                    "label": "Boundary",
                    "latitude": -90,
                    "longitude": 180,
                    "timezone": "UTC",
                    "temperature_unit": "celsius",
                }
                complete = client.put("/api/settings", json={"location": complete_location})
                expect(complete.status_code == 200 and complete.json()["location"] == complete_location, "complete finite boundary location is accepted", checks)

            for raw, label in (
                ('{"location":{"latitude":91}}', "out-of-range latitude"),
                ('{"location":{"longitude":-181}}', "out-of-range longitude"),
                ('{"location":{"latitude":NaN}}', "NaN latitude"),
                ('{"location":{"latitude":Infinity}}', "positive infinity latitude"),
                ('{"location":{"longitude":-Infinity}}', "negative infinity longitude"),
                ('{"location":{"latitude":true}}', "boolean latitude"),
            ):
                invalid_location = client.put(
                    "/api/settings",
                    content=raw,
                    headers={"content-type": "application/json"},
                )
                expect(invalid_location.status_code == 400, f"settings reject {label}", checks)

            persisted = json.loads(nocturne.SETTINGS_PATH.read_text(encoding="utf-8"))
            expect(persisted == client.get("/api/settings").json(), "settings are atomically persisted as valid JSON", checks)
            temp_pattern = f".{nocturne.SETTINGS_PATH.name}.*.tmp"
            expect(not list(nocturne.CONFIG_DIR.glob(temp_pattern)), "successful settings writes leave no temporary file", checks)

            before_failure = nocturne.SETTINGS_PATH.read_bytes()
            failed_update = enabled.json()
            failed_update["modes"]["dashboard"] = True
            try:
                with patch.object(nocturne.os, "replace", side_effect=OSError("simulated replacement failure")):
                    nocturne._save_settings(failed_update)
            except OSError:
                pass
            else:
                raise AssertionError("simulated atomic replacement failure did not propagate")
            expect(nocturne.SETTINGS_PATH.read_bytes() == before_failure, "failed settings replacement preserves the previous file", checks)
            expect(not list(nocturne.CONFIG_DIR.glob(temp_pattern)), "failed settings replacement cleans up its temporary file", checks)

        expect(
            f"Nocturne is ready at {nocturne._local_ready_url()} [{nocturne._profile_id()}]" in ready_output.getvalue(),
            "lifespan startup preserves the ready-message output",
            checks,
        )

    report = {
        "schema": "nocturne.runtime-smoke.v1",
        "overall": "PASS",
        "checks": checks,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"schema": "nocturne.runtime-smoke.v1", "overall": "FAIL", "error": str(exc)}, indent=2))
        raise
