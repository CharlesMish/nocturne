#!/usr/bin/env python3
"""Non-destructive FastAPI smoke test for Nocturne's release-critical routes."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
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

        with TestClient(nocturne.app) as client:
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

            quarantine = client.get("/sounds/inbox/quarantine-seam-risk/rain-inside-house.mp3")
            expect(quarantine.status_code == 404, "original seam-risk quarantine is denied", checks)
            baked = client.get("/sounds/inbox/seam-baked/rain-inside-house-seam-baked.m4a")
            expect(baked.status_code == 404, "seam-baked audition candidate is also denied", checks)

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

            persisted = json.loads(nocturne.SETTINGS_PATH.read_text(encoding="utf-8"))
            expect(persisted == enabled.json(), "settings are atomically persisted as valid JSON", checks)
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
