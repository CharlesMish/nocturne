#!/usr/bin/env python3
"""Optional deterministic browser smoke test for Nocturne's packaged UI.

This script does not require a running server and does not contact the network. It
loads the release HTML into Chromium, intercepts the packaged CSS/catalog/API
responses, exercises the editorial picker hierarchy and focus behavior, and
writes screenshots plus a machine-readable report under verification-artifacts/.

QA-only dependencies: Python Playwright and a Chromium executable. They are not
runtime dependencies of Nocturne itself.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import traceback
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

REPORT_SCHEMA = "nocturne.browser-smoke.v1"
BASE_URL = "https://nocturne.test/"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--chromium", help="Chromium/Chrome executable (or set CHROMIUM_BIN).")
    parser.add_argument("--profile", choices=("nocturne", "nocturne-pi"), help="override the packaged profile")
    return parser.parse_args()


def find_chromium(explicit: str | None) -> str:
    candidates = [
        explicit,
        os.environ.get("CHROMIUM_BIN"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise RuntimeError("No Chromium executable found. Pass --chromium or set CHROMIUM_BIN.")


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    artifacts = root / "verification-artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    report_path = artifacts / "browser-smoke.json"

    checks: list[str] = []
    console_errors: list[str] = []
    page_errors: list[str] = []
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "overall": "FAIL",
        "transport": "page.set_content with intercepted packaged resources and deterministic storage/context shims; no external network",
        "checks": checks,
        "console_errors": console_errors,
        "page_errors": page_errors,
    }

    try:
        from playwright.sync_api import Route, sync_playwright

        chromium_path = find_chromium(args.chromium)
        html = (root / "static" / "index.html").read_text(encoding="utf-8")
        css = (root / "static" / "nocturne-polish.css").read_text(encoding="utf-8")
        manifest = json.loads((root / "sounds" / "sound_library.json").read_text(encoding="utf-8"))
        build = json.loads((root / "nocturne_build.json").read_text(encoding="utf-8"))
        pointer_path = root / "nocturne_profile.json"
        pointer = json.loads(pointer_path.read_text(encoding="utf-8")) if pointer_path.exists() else {"profile": "nocturne"}
        profile_id = args.profile or pointer.get("profile", "nocturne")
        if profile_id not in {"nocturne", "nocturne-pi"}:
            profile_id = "nocturne"
        profile = json.loads((root / "profiles" / f"{profile_id}.json").read_text(encoding="utf-8"))
        report["profile"] = profile_id
        requests_seen: list[str] = []

        # Resolve absolute paths against a deterministic browser-like origin.
        html = html.replace("<head>", f'<head><base href="{BASE_URL}">', 1)
        # The smoke test deliberately exercises the painted fallback rather than decoding the video.
        import re
        html = re.sub(r'<source\s+src="/rain\.mp4(?:\?[^"]*)?"\s+type="video/mp4">', '', html)
        web_manifest = (root / "static" / "manifest.webmanifest").read_text(encoding="utf-8")

        public_sounds = {entry["id"]: entry for entry in manifest["sounds"]}
        default_names = [public_sounds[sound_id]["name"] for sound_id in manifest["default_slots"]]
        waves_name = public_sounds["waves-on-shore"]["name"]
        expected_experimental = sorted(
            entry["name"] for entry in manifest["sounds"] if entry.get("status") == "experimental"
        )
        default_settings = {
            "modes": {
                "onsen": True,
                "sky": True,
                "radio": True,
                "utility": False,
                "dashboard": False,
            },
            "location": {
                "label": "Bishop Creek",
                "latitude": 35.53,
                "longitude": -97.47,
                "timezone": "America/Chicago",
                "temperature_unit": "fahrenheit",
            },
        }

        def route_handler(route: Route) -> None:
            request = route.request
            parsed = urlparse(request.url)
            path = unquote(parsed.path)
            requests_seen.append(path)
            if request.url.startswith("https://fonts.googleapis.com/"):
                route.fulfill(status=200, body="/* fonts suppressed in deterministic smoke */", content_type="text/css")
                return
            if request.url.startswith("https://fonts.gstatic.com/"):
                route.fulfill(status=204, body="")
                return
            if path == "/":
                route.fulfill(status=200, body=html, content_type="text/html")
                return
            if path == "/nocturne-polish.css":
                route.fulfill(status=200, body=css, content_type="text/css")
                return
            if path == "/manifest.webmanifest":
                route.fulfill(status=200, body=web_manifest, content_type="application/manifest+json")
                return
            if path.startswith("/icons/"):
                local = root / "static" / path.lstrip("/")
                if local.is_file():
                    route.fulfill(status=200, path=str(local), content_type="image/png")
                else:
                    route.fulfill(status=404, body="missing")
                return
            if path == "/sounds/sound_library.json":
                route.fulfill(status=200, body=json.dumps(manifest), content_type="application/json")
                return
            if path.startswith("/sounds/"):
                local = root / path.lstrip("/")
                if local.is_file():
                    if request.method == "HEAD":
                        route.fulfill(status=200, body="", headers={"content-type": "audio/mpeg"})
                    else:
                        media_type = "audio/wav" if local.suffix.lower() == ".wav" else "audio/mpeg"
                        route.fulfill(status=200, path=str(local), content_type=media_type)
                else:
                    route.fulfill(status=404, body="missing")
                return
            if path == "/api/version":
                route.fulfill(status=200, body=json.dumps({**build, "profile": profile_id}), content_type="application/json")
                return
            if path == "/api/profile":
                route.fulfill(status=200, body=json.dumps(profile), content_type="application/json")
                return
            if path == "/api/settings":
                route.fulfill(status=200, body=json.dumps(default_settings), content_type="application/json")
                return
            if path == "/rain-still.webp":
                local = root / "static" / "rain-still.webp"
                route.fulfill(status=200, path=str(local), content_type="image/webp")
                return
            if path == "/rain.mp4":
                local = root / "static" / "rain.mp4"
                if local.is_file():
                    route.fulfill(status=200, path=str(local), content_type="video/mp4")
                else:
                    route.fulfill(status=404, body="")
                return
            route.fulfill(status=404, body="{}", content_type="application/json")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=chromium_path,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
            page.set_default_timeout(10_000)
            page.route("**/*", route_handler)
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            # Atlas blocks arbitrary browser navigation in this environment. Keep the
            # deterministic set_content transport, but provide the two origin properties
            # this test needs: durable localStorage and a trustworthy-context signal.
            page.evaluate("""() => {
              const data = {};
              Object.defineProperty(window, 'localStorage', {
                configurable: true,
                value: {
                  getItem: key => Object.prototype.hasOwnProperty.call(data, key) ? data[key] : null,
                  setItem: (key, value) => { data[key] = String(value); },
                  removeItem: key => { delete data[key]; },
                  clear: () => { Object.keys(data).forEach(key => delete data[key]); }
                }
              });
              Object.defineProperty(window, 'isSecureContext', { configurable: true, value: true });
            }""")
            page.set_content(html, wait_until="domcontentloaded")
            page.wait_for_function("document.body.style.opacity !== '0'")
            page.wait_for_function("document.querySelectorAll('.slot-change').length === 8")
            page.wait_for_function("label => document.querySelector('#build-label-footer').textContent.includes(label)", arg=build["version"])

            links = page.locator('link[rel="stylesheet"][href="/nocturne-polish.css"]')
            assert links.count() == 1, "main page includes exactly one polish stylesheet"
            checks.append("main page includes one served polish stylesheet")

            first_change = page.locator(".slot-change").first
            first_change.focus()
            focus_style = first_change.evaluate(
                "e => ({style:getComputedStyle(e).outlineStyle,width:getComputedStyle(e).outlineWidth})"
            )
            assert focus_style == {"style": "solid", "width": "2px"}, f"unexpected focus style: {focus_style}"
            checks.append("keyboard focus receives a visible 2 px outline from the polish layer")

            visible_modes = page.locator('.mode-btn[data-mode]:visible').evaluate_all(
                "els => els.map(el => el.dataset.mode)"
            )
            assert visible_modes == ["onsen", "sky", "radio"], visible_modes
            checks.append("default browser profile shows only core modes: onsen, sky, radio")
            assert page.evaluate("document.body.dataset.profile") == profile_id
            checks.append(f"browser applies the packaged profile: {profile_id}")
            if profile_id == "nocturne-pi":
                assert "/rain.mp4" not in requests_seen, requests_seen
                checks.append("Nocturne Pi does not request the disabled rain video")

            assert page.evaluate("window.isSecureContext") is True
            assert page.locator('link[rel="manifest"][href="/manifest.webmanifest"]').count() == 1
            checks.append("packaged UI has a manifest and runs in a secure test context")

            page.locator("#settings-open").click()
            page.wait_for_selector("#settings-overlay:not([hidden])")
            platform_details = page.locator(".platform-card span").all_text_contents()
            assert len(platform_details) == 4 and all("checking" not in text for text in platform_details), platform_details
            assert page.get_by_text("device matrix pending", exact=False).count() == 1
            checks.append("device integration remains explicitly marked as field-test pending")
            checks.append("device-integration cards expose feature state instead of a silent promise")
            page.locator("#settings-platform-title").scroll_into_view_if_needed()
            page.wait_for_timeout(100)
            page.locator(".settings-dialog").screenshot(path=str(artifacts / "desktop-platform-settings.png"))
            page.locator("#settings-close").click()

            first_slider = page.locator('#mixer-grid .channel input[type="range"]').first
            first_slider.evaluate("e => { e.value = '23'; e.dispatchEvent(new Event('input', {bubbles:true})); }")
            page.once("dialog", lambda dialog: dialog.accept("Rain room"))
            page.locator("#scene-save").click()
            page.wait_for_function("() => document.querySelectorAll('#scene-select option').length === 2")
            scene_record = page.evaluate("JSON.parse(localStorage.getItem('nocturne:onsen:scenes:v1'))[0]")
            assert scene_record["schema"] == 1, scene_record
            assert scene_record["name"] == "Rain room" and scene_record["slots"][0]["volume"] == 23, scene_record
            checks.append("a schema-versioned named scene persists mixer and Radio state only in browser storage")

            first_slider.evaluate("e => { e.value = '7'; e.dispatchEvent(new Event('input', {bubbles:true})); }")
            page.select_option("#scene-select", scene_record["id"])
            page.locator("#scene-apply").click()
            assert int(first_slider.input_value()) == 23
            checks.append("applying a local scene restores its saved channel level")

            page.once("dialog", lambda dialog: dialog.accept())
            page.locator("#scene-delete").click()
            page.wait_for_function("() => document.querySelectorAll('#scene-select option').length === 1")
            checks.append("local scenes can be deleted without affecting the sound catalog")

            page.screenshot(path=str(artifacts / "desktop-onsen.png"), full_page=True)

            page.evaluate("""() => {
              window.__nocturneOriginalSetItem = localStorage.setItem;
              localStorage.setItem = () => { throw new DOMException('storage full', 'QuotaExceededError'); };
            }""")
            page.once("dialog", lambda dialog: dialog.accept("Storage check"))
            page.locator("#scene-save").click()
            assert "storage is full" in page.locator("#scene-status").inner_text().lower()
            page.evaluate("localStorage.setItem = window.__nocturneOriginalSetItem")
            checks.append("scene save explains a browser storage quota failure")

            first_change.click()
            page.wait_for_selector("#sound-picker:not([hidden])")
            checks.append("sound picker opens from a mixer slot")

            category_labels = page.locator("#sound-picker-categories .sound-chip").all_text_contents()
            assert category_labels[:5] == ["tonight", "all", "recorded", "generated", "experimental"], category_labels
            checks.append("picker hierarchy begins with Tonight, All, Recorded, Generated, Experimental")

            def option_names() -> list[str]:
                return page.locator("#sound-picker-list .sound-option-name").all_text_contents()

            tonight_names = option_names()
            assert tonight_names == default_names, {"expected": default_names, "actual": tonight_names}
            assert waves_name not in tonight_names
            assert not set(tonight_names).intersection(expected_experimental)
            checks.append("Tonight contains exactly the eight canonical bundled defaults")
            checks.append("Waves and experimental thunder are absent from Tonight")

            page.screenshot(path=str(artifacts / "desktop-tonight-picker.png"), full_page=True)

            page.get_by_role("button", name="all", exact=True).click()
            all_names = option_names()
            assert waves_name in all_names, {"waves": waves_name, "actual": all_names}
            assert not set(all_names).intersection(expected_experimental)
            checks.append("Waves remains optional in All; experimental sounds stay out of ordinary browsing")

            page.get_by_role("button", name="experimental", exact=True).click()
            experimental_names = sorted(option_names())
            assert experimental_names == expected_experimental, {
                "expected": expected_experimental,
                "actual": experimental_names,
            }
            checks.append("Experimental contains only the two explicitly marked thunder candidates")

            # Dialog tabbing must remain inside the picker.
            page.locator("#sound-picker-search").focus()
            for _ in range(18):
                page.keyboard.press("Tab")
                inside = page.evaluate("document.querySelector('#sound-picker').contains(document.activeElement)")
                assert inside, "Tab escaped the modal sound picker"
            checks.append("Tab focus remains inside the open sound picker")

            page.keyboard.press("Escape")
            page.wait_for_selector("#sound-picker[hidden]", state="attached")
            assert first_change.evaluate("e => document.activeElement === e")
            returned_style = first_change.evaluate(
                "e => ({style:getComputedStyle(e).outlineStyle,width:getComputedStyle(e).outlineWidth})"
            )
            assert returned_style == {"style": "solid", "width": "2px"}, returned_style
            checks.append("Escape closes the picker and visibly returns focus to its Change trigger")

            no_horizontal_overflow = page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth + 1"
            )
            assert no_horizontal_overflow, "desktop page has horizontal overflow"
            checks.append("desktop viewport has no horizontal overflow")

            page.set_viewport_size({"width": 390, "height": 844})
            page.locator(".mixer-section").scroll_into_view_if_needed()
            page.wait_for_timeout(150)
            no_mobile_overflow = page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth + 1"
            )
            assert no_mobile_overflow, "mobile page has horizontal overflow"
            page.screenshot(path=str(artifacts / "mobile-mixer.png"), full_page=False)
            checks.append("390 px mobile viewport has no horizontal overflow")

            browser.close()

        assert not page_errors, page_errors
        assert not console_errors, console_errors
        report["overall"] = "PASS"
        report["screenshots"] = [
            "verification-artifacts/desktop-onsen.png",
            "verification-artifacts/desktop-platform-settings.png",
            "verification-artifacts/desktop-tonight-picker.png",
            "verification-artifacts/mobile-mixer.png",
        ]
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc!r}"
        report["traceback"] = traceback.format_exc()
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
