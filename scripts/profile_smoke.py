#!/usr/bin/env python3
"""Check the two shared-source Nocturne presentation profiles."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402
import main as nocturne  # noqa: E402


def expect(value: bool, message: str, checks: list[str]) -> None:
    if not value:
        raise AssertionError(message)
    checks.append(message)


def main() -> int:
    checks: list[str] = []
    with TestClient(nocturne.app) as client:
        for profile_id, rain_video, appearance in (("nocturne", True, True), ("nocturne-pi", False, False)):
            os.environ["NOCTURNE_PROFILE"] = profile_id
            response = client.get("/api/profile")
            expect(response.status_code == 200, f"{profile_id} profile endpoint responds", checks)
            data = response.json()
            expect(data.get("id") == profile_id, f"{profile_id} identity is preserved", checks)
            expect(data.get("visuals", {}).get("rain_video") is rain_video, f"{profile_id} rain-video capability is correct", checks)
            expect(
                data.get("visuals", {}).get("appearance_customization") is appearance,
                f"{profile_id} appearance capability is correct",
                checks,
            )
            version = client.get("/api/version").json()
            expect(version.get("profile") == profile_id, f"{profile_id} appears in version diagnostics", checks)

        page = client.get("/").text
        expect('data-full-src="/rain.mp4' in page, "full video is opt-in after profile resolution", checks)
        expect('<source src="/rain.mp4' not in page, "HTML does not eagerly request the full video", checks)
        still = client.get("/rain-still.webp")
        expect(still.status_code == 200 and still.content.startswith(b"RIFF"), "Pi still image is served", checks)
    os.environ.pop("NOCTURNE_PROFILE", None)
    print(json.dumps({"schema": "nocturne.profile-smoke.v1", "overall": "PASS", "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"schema": "nocturne.profile-smoke.v1", "overall": "FAIL", "error": str(exc)}, indent=2))
        raise
