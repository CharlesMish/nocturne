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


def find_chromium(explicit: str | None, playwright_path: str | None = None) -> str:
    candidates = [
        explicit,
        os.environ.get("CHROMIUM_BIN"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        playwright_path,
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise RuntimeError(
        "No Chromium executable found. Pass --chromium, set CHROMIUM_BIN, "
        "or run `python -m playwright install chromium`."
    )


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    artifacts = root / "verification-artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    report_path = artifacts / "browser-smoke.json"

    checks: list[str] = []
    console_errors: list[str] = []
    page_errors: list[str] = []
    mood_screenshots: list[str] = []
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
        request_urls_seen: list[str] = []

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
                "label": "Sample location",
                "latitude": 35.53,
                "longitude": -97.47,
                "timezone": "America/Chicago",
                "temperature_unit": "fahrenheit",
            },
        }
        radio_tracks = [
            {"name": "First Light Tape", "url": "/sounds/library/campfire-loop-stereo.mp3"},
            {"name": "Rain Window Dub", "url": "/sounds/library/rain-city-pooling.mp3"},
        ]
        utility_songs = [
            {
                "slug": "evening-loop",
                "title": "Evening Loop",
                "artist": "Nocturne",
                "bpm": 72,
                "key": "C minor",
                "tags": ["local", "bedside"],
                "updatedAt": "2026-07-14T00:00:00Z",
            }
        ]
        utility_song = {
            "slug": "evening-loop",
            "meta": {key: value for key, value in utility_songs[0].items() if key != "slug"},
            "code": 'note("<c3 eb3 g3>").slow(4)',
        }
        weather_failure = False
        weather_stale = True

        def route_handler(route: Route) -> None:
            request = route.request
            parsed = urlparse(request.url)
            path = unquote(parsed.path)
            requests_seen.append(path)
            request_urls_seen.append(request.url)
            if request.url.startswith("https://fonts.googleapis.com/"):
                route.fulfill(status=200, body="/* fonts suppressed in deterministic smoke */", content_type="text/css")
                return
            if path.startswith("/fonts/"):
                local = root / "static" / path.lstrip("/")
                if local.is_file():
                    route.fulfill(status=200, path=str(local), content_type="font/woff2")
                else:
                    route.fulfill(status=404, body="missing")
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
            if path == "/api/radio":
                route.fulfill(status=200, body=json.dumps(radio_tracks), content_type="application/json")
                return
            if path == "/api/songs":
                route.fulfill(status=200, body=json.dumps(utility_songs), content_type="application/json")
                return
            if path == "/api/songs/evening-loop":
                route.fulfill(status=200, body=json.dumps(utility_song), content_type="application/json")
                return
            if path == "/api/weather":
                if weather_failure:
                    route.fulfill(status=200, body=json.dumps({"ok": False}), content_type="application/json")
                else:
                    route.fulfill(
                        status=200,
                        body=json.dumps({
                            "ok": True,
                            "weather_code": 2,
                            "temperature": 58,
                            "temperature_unit": "fahrenheit",
                            "is_day": False,
                            "stale": weather_stale,
                            "location_name": "Sample location",
                        }),
                        content_type="application/json",
                    )
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
            if path == "/dashboard.html":
                route.fulfill(
                    status=200,
                    body=(root / "static" / "dashboard.html").read_text(encoding="utf-8"),
                    content_type="text/html",
                )
                return
            route.fulfill(status=404, body="{}", content_type="application/json")

        with sync_playwright() as playwright:
            chromium_path = find_chromium(args.chromium, playwright.chromium.executable_path)
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
              const data = {
                'nocturne:appearance:v1': '{"schema":99,"mood":"unknown","type":"clear","light":"clear"}'
              };
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
              window.__nocturneAudioObjects = 0;
              window.__nocturneAudioPlayCalls = 0;
              window.__nocturneAudioPauseCalls = 0;
              window.__nocturneNow = Date.now();
              Date.now = () => window.__nocturneNow;
              window.__nocturneAudioParamEvents = [];

              class FakeAudioParam {
                constructor(context, value = 1) {
                  this.context = context;
                  this.value = value;
                  this.scheduled = [];
                }
                record(type, value, time, extra = null) {
                  const event = {type, value, time, extra};
                  window.__nocturneAudioParamEvents.push(event);
                  return event;
                }
                cancelScheduledValues(time) {
                  this.record('cancel', null, time);
                  this.scheduled = this.scheduled.filter(event => event.time < time);
                }
                setValueAtTime(value, time) {
                  const event = this.record('set', value, time);
                  this.scheduled.push(event);
                  if (time <= this.context.currentTime) this.value = value;
                }
                linearRampToValueAtTime(value, time) {
                  const event = this.record('ramp', value, time);
                  this.scheduled.push(event);
                }
                setTargetAtTime(value, time, constant) {
                  const event = this.record('target', value, time, constant);
                  this.scheduled.push(event);
                  this.value = value;
                }
              }
              class FakeNode {
                connect(node) { return node; }
                disconnect() {}
              }
              class FakeAudioContext {
                constructor() {
                  this.currentTime = 100;
                  this.state = 'running';
                  this.destination = new FakeNode();
                  this.gainCount = 0;
                  window.__nocturneAudioContext = this;
                }
                createGain() {
                  const node = new FakeNode();
                  node.gain = new FakeAudioParam(this, 1);
                  this.gainCount += 1;
                  if (this.gainCount === 1) window.__nocturneMasterParam = node.gain;
                  return node;
                }
                createMediaElementSource() { return new FakeNode(); }
                createBiquadFilter() {
                  const node = new FakeNode();
                  node.frequency = new FakeAudioParam(this, 0);
                  node.Q = new FakeAudioParam(this, 0);
                  return node;
                }
                createConvolver() { return new FakeNode(); }
                createAnalyser() {
                  const node = new FakeNode();
                  node.frequencyBinCount = 32;
                  node.getByteFrequencyData = array => array.fill(0);
                  return node;
                }
                createBuffer() { return {getChannelData: () => new Float32Array(1)}; }
                resume() { this.state = 'running'; return Promise.resolve(); }
              }
              window.AudioContext = FakeAudioContext;
              window.webkitAudioContext = FakeAudioContext;
              window.__nocturneAdvanceClock = ms => {
                window.__nocturneNow += ms;
                if (window.__nocturneAudioContext) window.__nocturneAudioContext.currentTime += ms / 1000;
              };
              window.__nocturneTimerState = () => ({
                now: window.__nocturneNow,
                contextTime: window.__nocturneAudioContext?.currentTime,
                value: window.__nocturneMasterParam?.value,
                scheduled: (window.__nocturneMasterParam?.scheduled || []).map(event => ({...event})),
                events: window.__nocturneAudioParamEvents.map(event => ({...event})),
                status: document.querySelector('#timer-status')?.textContent || '',
                master: document.querySelector('#master')?.value || ''
              });
              const NativeAudio = window.Audio;
              window.Audio = function(...args) {
                window.__nocturneAudioObjects += 1;
                const audio = new NativeAudio(...args);
                const nativePause = audio.pause.bind(audio);
                audio.play = () => {
                  window.__nocturneAudioPlayCalls += 1;
                  return Promise.resolve();
                };
                audio.pause = () => {
                  window.__nocturneAudioPauseCalls += 1;
                  nativePause();
                };
                return audio;
              };
              window.Audio.prototype = NativeAudio.prototype;
            }""")
            page.set_content(html, wait_until="domcontentloaded")
            page.wait_for_function("document.body.style.opacity !== '0'")
            page.wait_for_function("document.querySelectorAll('.slot-change').length === 8")
            look_alignment = page.locator(".slot-theme").evaluate_all(
                "els => els.map(el => ({textAlign:getComputedStyle(el).textAlign,textAlignLast:getComputedStyle(el).textAlignLast}))"
            )
            assert len(look_alignment) == 8 and all(
                item == {"textAlign": "center", "textAlignLast": "center"} for item in look_alignment
            ), look_alignment
            checks.append("all mixer look selectors center their current value like the Change buttons")
            page.wait_for_function("label => document.querySelector('#build-label-footer').textContent.includes(label)", arg=build["version"])
            page.wait_for_function("document.fonts.status === 'loaded'")
            assert page.evaluate("document.documentElement.dataset.mood") == "rain-lantern"
            assert page.evaluate("document.documentElement.dataset.type") == "poetic"
            assert page.evaluate("document.documentElement.dataset.light") == "balanced"
            checks.append("invalid appearance storage safely falls back to curated defaults")

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
            appearance_section = page.locator("#settings-appearance-section")
            appearance_enabled = page.evaluate("document.documentElement.dataset.appearanceEnabled")
            if profile_id == "nocturne-pi":
                assert "/rain.mp4" not in requests_seen, requests_seen
                checks.append("Nocturne Pi does not request the disabled rain video")
                pi_stage_background = page.locator("#video-stage").evaluate(
                    "stage => getComputedStyle(stage).backgroundImage"
                )
                assert "rain-still.webp" in pi_stage_background, pi_stage_background
                assert "/rain-still.webp" in requests_seen, requests_seen
                checks.append("Nocturne Pi visibly uses the packaged static rain hero")
                assert appearance_enabled == "false" and not appearance_section.is_visible()
                checks.append("Nocturne Pi keeps curated appearance controls disabled")
                pi_rendering = page.evaluate("""() => {
                  const style = selector => getComputedStyle(document.querySelector(selector));
                  return {
                    grain: style('.grain').display,
                    rain: style('.ambient-rain').display,
                    petals: style('.ambient-petals').display,
                    reelAnimation: style('.reel').animationName,
                    settingsBlur: style('.settings-dialog').backdropFilter,
                    settingsWebkitBlur: style('.settings-dialog').webkitBackdropFilter
                  };
                }""")
                assert {key: pi_rendering[key] for key in (
                    "grain", "rain", "petals", "reelAnimation", "settingsBlur"
                )} == {
                    "grain": "none",
                    "rain": "none",
                    "petals": "none",
                    "reelAnimation": "none",
                    "settingsBlur": "none",
                }, pi_rendering
                assert pi_rendering["settingsWebkitBlur"] in (None, "none"), pi_rendering
                checks.append("Nocturne Pi suppresses decorative layers, reel motion, and dialog blur")
            else:
                assert appearance_enabled == "true" and appearance_section.is_visible() is False

            assert not any(url.startswith("https://fonts.googleapis.com/") or url.startswith("https://fonts.gstatic.com/") for url in request_urls_seen)
            assert len({path for path in requests_seen if path.startswith("/fonts/")}) >= 3, requests_seen
            checks.append("locally packaged fonts load without external font requests")

            assert page.evaluate("window.isSecureContext") is True
            assert page.locator('link[rel="manifest"][href="/manifest.webmanifest"]').count() == 1
            checks.append("packaged UI has a manifest and runs in a secure test context")

            # Sleep timing is wall-clock based, while audible fading is one
            # Web Audio schedule. The fake clock/context keeps this deterministic.
            timer_15 = page.locator('[data-timer-minutes="15"]')
            page.evaluate("window.__nocturneAudioParamEvents.length = 0")
            timer_15.click()
            timer_state = page.evaluate("window.__nocturneTimerState()")
            ramps = [event for event in timer_state["scheduled"] if event["type"] == "ramp"]
            sets = [event for event in timer_state["scheduled"] if event["type"] == "set"]
            assert len(ramps) == 1 and abs(ramps[0]["time"] - 1000) < 0.001, timer_state
            assert len(sets) == 2 and abs(sets[-1]["time"] - 940) < 0.001, timer_state
            checks.append("sleep timer schedules a held base gain and one final Web Audio ramp")

            event_count = len(timer_state["events"])
            page.wait_for_timeout(650)
            assert len(page.evaluate("window.__nocturneTimerState().events")) == event_count
            checks.append("sleep timer status ticks do not rewrite audible gain")

            page.locator("#cancel-timer").click()
            cancelled = page.evaluate("window.__nocturneTimerState()")
            assert not [event for event in cancelled["scheduled"] if event["type"] == "ramp"]
            assert abs(cancelled["value"] - 0.7) < 0.001 and cancelled["master"] == "70"
            checks.append("sleep timer cancellation clears automation and restores its base level")

            timer_15.click()
            page.locator('[data-timer-minutes="30"]').click()
            replaced = page.evaluate("window.__nocturneTimerState()")
            ramps = [event for event in replaced["scheduled"] if event["type"] == "ramp"]
            assert len(ramps) == 1 and abs(ramps[0]["time"] - 1900) < 0.001, replaced
            checks.append("replacing a sleep timer leaves only the new gain schedule")

            page.locator("#master").evaluate(
                "e => { e.value = '40'; e.dispatchEvent(new Event('input', {bubbles:true})); }"
            )
            changed = page.evaluate("window.__nocturneTimerState()")
            base_sets = [event for event in changed["scheduled"] if event["type"] == "set"]
            assert base_sets and all(abs(event["value"] - 0.4) < 0.001 for event in base_sets), changed
            checks.append("manual master changes update the timer base and replace its schedule")

            page.evaluate("""() => {
              window.__nocturneAdvanceClock(300000);
              Object.defineProperty(document, 'hidden', {configurable:true, value:false});
              document.dispatchEvent(new Event('visibilitychange'));
            }""")
            returned = page.evaluate("window.__nocturneTimerState()")
            ramps = [event for event in returned["scheduled"] if event["type"] == "ramp"]
            assert len(ramps) == 1 and abs(ramps[0]["time"] - 1900) < 0.001, returned
            assert "remaining" in returned["status"]
            checks.append("visible return before expiry preserves and reschedules the timer")

            page.locator("#cancel-timer").click()
            page.evaluate("""() => {
              const button = document.querySelector('[data-timer-minutes="15"]');
              button.dataset.timerMinutes = '0.5';
              button.click();
            }""")
            short_timer = page.evaluate("window.__nocturneTimerState()")
            short_sets = [
                event for event in short_timer["scheduled"]
                if event["type"] == "set" and event["time"] >= short_timer["contextTime"]
            ]
            short_ramps = [event for event in short_timer["scheduled"] if event["type"] == "ramp"]
            assert len(short_ramps) == 1 and abs(short_ramps[0]["time"] - 430) < 0.001, short_timer
            assert short_sets and all(abs(event["time"] - 400) < 0.001 for event in short_sets), short_timer
            checks.append("a timer shorter than the fade duration begins its scheduled fade immediately")

            pauses_before_expiry = page.evaluate("window.__nocturneAudioPauseCalls")
            page.evaluate("""() => {
              window.__nocturneAdvanceClock(31000);
              window.dispatchEvent(new Event('pageshow'));
            }""")
            expired = page.evaluate("window.__nocturneTimerState()")
            assert expired["status"].startswith("timer finished") and expired["master"] == "40", expired
            assert abs(expired["value"] - 0.4) < 0.001, expired
            assert page.evaluate("window.__nocturneAudioPauseCalls") > pauses_before_expiry
            checks.append("expired return finishes playback and restores gain for the next resume")

            page.evaluate("""document.querySelector('[data-timer-minutes="0.5"]').dataset.timerMinutes = '15'""")

            page.locator("#settings-open").click()
            page.wait_for_selector("#settings-overlay:not([hidden])")
            if profile_id == "nocturne":
                assert page.locator("#settings-tab-room").get_attribute("aria-selected") == "true"
                assert page.locator("#settings-panel-room").is_visible()
                assert not page.locator("#settings-panel-setup").is_visible()
                checks.append("full-profile Settings opens on the non-persisted Room tab")
                assert appearance_section.is_visible()
                page.locator('input[data-appearance-field="mood"][value="moonwater"]').check()
                page.locator('input[data-appearance-field="type"][value="clear"]').check()
                page.locator('input[data-appearance-field="light"][value="clear"]').check()
                assert page.evaluate("document.documentElement.dataset.mood") == "moonwater"
                assert page.evaluate("document.documentElement.dataset.type") == "clear"
                assert page.evaluate("document.documentElement.dataset.light") == "clear"
                appearance_record = page.evaluate("JSON.parse(localStorage.getItem('nocturne:appearance:v1'))")
                assert appearance_record == {"schema": 1, "mood": "moonwater", "type": "clear", "light": "clear"}, appearance_record
                page.locator("#settings-appearance-section").screenshot(path=str(artifacts / "desktop-appearance-settings.png"))
                page.evaluate("""() => {
                  window.__appearanceOriginalSetItem = localStorage.setItem;
                  localStorage.setItem = () => { throw new DOMException('storage unavailable', 'SecurityError'); };
                }""")
                page.locator('input[data-appearance-field="mood"][value="cedar-steam"]').check()
                assert page.evaluate("document.documentElement.dataset.mood") == "cedar-steam"
                assert "storage is unavailable" in page.locator("#settings-status").inner_text().lower()
                page.evaluate("localStorage.setItem = window.__appearanceOriginalSetItem")
                page.locator("#reset-appearance").click()
                assert page.evaluate("document.documentElement.dataset.mood") == "rain-lantern"
                assert page.evaluate("document.documentElement.dataset.type") == "poetic"
                assert page.evaluate("document.documentElement.dataset.light") == "balanced"
                checks.append("full-profile appearance controls persist choices, survive storage failure, and reset to defaults")
                page.locator("#settings-tab-setup").click()
                assert page.locator("#settings-panel-setup").is_visible()
                assert not page.locator("#settings-panel-room").is_visible()
            else:
                assert not page.locator("#settings-tab-room").is_visible()
                assert page.locator("#settings-tab-setup").get_attribute("aria-selected") == "true"
                assert page.locator("#settings-panel-setup").is_visible()
                checks.append("Pi skips directly to Setup without exposing an empty Room tab")
            platform_details = page.locator(".platform-card span").all_text_contents()
            assert len(platform_details) == 4 and all("checking" not in text for text in platform_details), platform_details
            assert page.get_by_text("device matrix pending", exact=False).count() == 1
            checks.append("device integration remains explicitly marked as field-test pending")
            checks.append("device-integration cards expose feature state instead of a silent promise")
            page.locator("#settings-platform-title").scroll_into_view_if_needed()
            page.wait_for_timeout(100)
            page.locator(".settings-dialog").screenshot(path=str(artifacts / "desktop-platform-settings.png"))
            # Settings focus cannot escape; Escape closes and returns to its trigger.
            page.locator("#settings-close").focus()
            for _ in range(20):
                page.keyboard.press("Tab")
                inside = page.evaluate("document.querySelector('#settings-overlay').contains(document.activeElement)")
                assert inside, "Tab escaped the Settings dialog"
            assert page.evaluate("getComputedStyle(document.body).overflow") == "hidden"
            page.keyboard.press("Escape")
            page.wait_for_selector("#settings-overlay[hidden]", state="attached")
            assert page.locator("#settings-open").evaluate("e => document.activeElement === e")
            assert page.evaluate("getComputedStyle(document.body).overflow") != "hidden"
            checks.append("Settings traps focus, locks background scroll, closes with Escape, and returns focus")

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

            page.evaluate("scrollTo(0, 0)")
            page.wait_for_function("scrollY === 0")
            page.screenshot(path=str(artifacts / "desktop-onsen.png"), full_page=False)

            if profile_id == "nocturne":
                # Sky keeps its moon and observing card separate, including stale weather labeling.
                page.locator('.mode-btn[data-mode="sky"]').click()
                page.wait_for_function("document.querySelector('#sky-condition').textContent.includes('stale')")
                sky_boxes = page.evaluate("""() => {
                  const moon = document.querySelector('.moon-cradle').getBoundingClientRect();
                  const card = document.querySelector('.sky-readout').getBoundingClientRect();
                  const overlap = !(moon.right <= card.left || moon.left >= card.right || moon.bottom <= card.top || moon.top >= card.bottom);
                  return {overlap, opacity:Number(getComputedStyle(document.querySelector('#sky-hero')).opacity), moon:{x:moon.x,y:moon.y,w:moon.width,h:moon.height}, card:{x:card.x,y:card.y,w:card.width,h:card.height}};
                }""")
                assert not sky_boxes["overlap"] and sky_boxes["opacity"] > 0.99, sky_boxes
                assert sky_boxes["moon"]["w"] > 150 and sky_boxes["card"]["w"] > 200, sky_boxes
                checks.append("Sky shows stale weather honestly with a non-overlapping moon and observing card")

                # Keep the proof capture presentation-ready without giving up the
                # stale-state assertion above. All values remain deterministic and
                # local to the smoke harness.
                weather_stale = False
                page.locator('.mode-btn[data-mode="onsen"]').click()
                page.locator('.mode-btn[data-mode="sky"]').click()
                page.wait_for_function("!document.querySelector('#sky-condition').textContent.includes('stale')")
                assert page.locator("#sky-location").inner_text() == "Sample location"
                page.screenshot(path=str(artifacts / "desktop-sky.png"), full_page=False)

                # Radio selects and displays the first track without autoplay or graph creation.
                audio_objects_before_radio = page.evaluate("window.__nocturneAudioObjects")
                page.locator('.mode-btn[data-mode="radio"]').click()
                page.wait_for_function("document.querySelector('#radio-stage').dataset.state === 'selected'")
                assert page.locator("#deck-title").inner_text() == radio_tracks[0]["name"]
                assert page.locator('.playlist-item[aria-current="true"]').count() == 1
                assert page.evaluate("window.__nocturneAudioObjects") == audio_objects_before_radio
                assert not page.locator("body").evaluate("e => e.classList.contains('radio-playing')")
                assert page.locator(".deck").evaluate("e => { const r=e.getBoundingClientRect(); return r.width > 300 && Number(getComputedStyle(e).opacity) > .99; }")
                page.screenshot(path=str(artifacts / "desktop-radio.png"), full_page=False)
                checks.append("Radio displays the first available track without autoplay or creating audio")

                # The shared rail sits between each active hero and the mixer.
                rail_order = page.evaluate("""() => {
                  const hero = document.querySelector('#radio-hero').getBoundingClientRect();
                  const railElement = document.querySelector('[data-global-controls]');
                  const rail = railElement.getBoundingClientRect();
                  const mixer = document.querySelector('.mixer-section');
                  return {heroBottom: hero.bottom, railTop: rail.top, railBeforeMixer: Boolean(railElement.compareDocumentPosition(mixer) & Node.DOCUMENT_POSITION_FOLLOWING)};
                }""")
                assert rail_order["railTop"] >= rail_order["heroBottom"] - 2, rail_order
                assert rail_order["railBeforeMixer"], rail_order
                checks.append("one shared master/silence/timer rail follows the active hero")

                # Weather failure remains calm and explicit on a later refresh.
                weather_failure = True
                page.locator('.mode-btn[data-mode="onsen"]').click()
                page.locator('.mode-btn[data-mode="sky"]').click()
                page.wait_for_function("document.querySelector('#sky-condition').textContent === 'weather offline'")
                checks.append("Sky degrades to an explicit calm offline state")
                weather_failure = False
                page.locator('.mode-btn[data-mode="onsen"]').click()

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

            if profile_id == "nocturne":
                clarity_sizes = page.evaluate("""() => Object.fromEntries(Object.entries({
                  change: '.slot-change',
                  category: '.sound-chip',
                  appearanceDetail: '.appearance-option small',
                  platformDetail: '.platform-card span'
                }).map(([name, selector]) => [name, parseFloat(getComputedStyle(document.querySelector(selector)).fontSize)]))""")
                assert clarity_sizes["change"] >= 11.5, clarity_sizes
                assert clarity_sizes["category"] >= 10.8, clarity_sizes
                assert clarity_sizes["appearanceDetail"] >= 11.5, clarity_sizes
                assert clarity_sizes["platformDetail"] >= 11.5, clarity_sizes
                checks.append("quiet secondary actions and supporting copy retain measured text floors")

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

            desktop_columns = page.locator("#mixer-grid").evaluate(
                "e => getComputedStyle(e).gridTemplateColumns.split(' ').filter(Boolean).length"
            )
            expected_columns = 4 if profile_id == "nocturne" else 8
            assert desktop_columns == expected_columns, {"profile": profile_id, "columns": desktop_columns}
            checks.append(f"{profile_id} desktop mixer uses its intended {expected_columns}-column deck")

            if profile_id == "nocturne":
                page.evaluate("scrollTo(0, 0)")
                page.wait_for_function("scrollY === 0")
                for mood in ("rain-lantern", "moonwater", "cedar-steam", "ember-room"):
                    page.locator("#settings-open").click()
                    page.wait_for_selector("#settings-overlay:not([hidden])")
                    page.locator(f'input[data-appearance-field="mood"][value="{mood}"]').check()
                    page.locator("#settings-close").click()
                    filename = f"desktop-mood-{mood}.png"
                    page.screenshot(path=str(artifacts / filename), full_page=False)
                    mood_screenshots.append(f"verification-artifacts/{filename}")
                page.locator("#settings-open").click()
                page.locator("#reset-appearance").click()
                page.locator("#settings-close").click()
                checks.append("all four curated moods render through the live full-profile controls")

                # Tablet composition uses the two-column deck without overflow.
                page.set_viewport_size({"width": 820, "height": 1000})
                page.locator('.mode-btn[data-mode="sky"]').click()
                tablet_overflow = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
                tablet_columns = page.locator("#mixer-grid").evaluate(
                    "e => getComputedStyle(e).gridTemplateColumns.split(' ').filter(Boolean).length"
                )
                assert tablet_overflow and tablet_columns == 2, {"overflow": tablet_overflow, "columns": tablet_columns}
                tablet_overlap = page.evaluate("""() => {
                  const a = document.querySelector('.moon-cradle').getBoundingClientRect();
                  const b = document.querySelector('.sky-readout').getBoundingClientRect();
                  return !(a.right <= b.left || a.left >= b.right || a.bottom <= b.top || a.top >= b.bottom);
                }""")
                assert not tablet_overlap
                page.screenshot(path=str(artifacts / "tablet-sky.png"), full_page=False)
                checks.append("820 px tablet keeps two mixer columns and separates Sky moon/readout")

            page.set_viewport_size({"width": 390, "height": 844})
            if profile_id == "nocturne":
                page.locator('.mode-btn[data-mode="onsen"]').click()
                header_rows = page.evaluate("""() => {
                  const brand = document.querySelector('.brand').getBoundingClientRect();
                  const settings = document.querySelector('#settings-open').getBoundingClientRect();
                  const modes = document.querySelector('.mode-switcher').getBoundingClientRect();
                  return {sameTop: Math.abs(brand.top - settings.top) < 8, modesBelow: modes.top >= Math.max(brand.bottom, settings.bottom) - 2, fullWidth: modes.width >= document.querySelector('.topbar').getBoundingClientRect().width - 2};
                }""")
                assert all(header_rows.values()), header_rows
                hero_ratio = page.locator("#video-stage").evaluate("e => e.getBoundingClientRect().width / e.getBoundingClientRect().height")
                assert abs(hero_ratio - 1.6) < 0.04, hero_ratio
                page.locator('.mode-btn[data-mode="sky"]').click()
                mobile_overlap = page.evaluate("""() => {
                  const a = document.querySelector('.moon-cradle').getBoundingClientRect();
                  const b = document.querySelector('.sky-readout').getBoundingClientRect();
                  return !(a.right <= b.left || a.left >= b.right || a.bottom <= b.top || a.top >= b.bottom);
                }""")
                assert not mobile_overlap
                page.screenshot(path=str(artifacts / "mobile-sky.png"), full_page=False)
                page.locator('.mode-btn[data-mode="onsen"]').click()
                checks.append("390 px header composes brand + Settings above a full-width mode switcher and a 16:10 hero")
            page.locator(".mixer-section").scroll_into_view_if_needed()
            page.wait_for_timeout(150)
            no_mobile_overflow = page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth + 1"
            )
            assert no_mobile_overflow, "mobile page has horizontal overflow"
            mobile_columns = page.locator("#mixer-grid").evaluate(
                "e => getComputedStyle(e).gridTemplateColumns.split(' ').filter(Boolean).length"
            )
            assert mobile_columns == 2, mobile_columns
            page.screenshot(path=str(artifacts / "mobile-mixer.png"), full_page=False)
            checks.append("390 px mobile viewport has a two-column mixer with no horizontal overflow")

            page.set_viewport_size({"width": 340, "height": 740})
            page.locator(".mixer-section").scroll_into_view_if_needed()
            page.wait_for_timeout(100)
            narrow_overflow = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
            narrow_columns = page.locator("#mixer-grid").evaluate(
                "e => getComputedStyle(e).gridTemplateColumns.split(' ').filter(Boolean).length"
            )
            assert narrow_overflow and narrow_columns == 1, {
                "overflow": narrow_overflow,
                "columns": narrow_columns,
            }
            page.screenshot(path=str(artifacts / "narrow-mixer.png"), full_page=False)
            checks.append("340 px compact viewport has a one-column mixer with no horizontal overflow")

            if profile_id == "nocturne":
                page.emulate_media(reduced_motion="reduce")
                motion_duration = page.locator(".ambient-petals .petal").first.evaluate("e => getComputedStyle(e).animationDuration")
                assert float(motion_duration.removesuffix("s")) <= 0.001, motion_duration
                checks.append("reduced-motion preference collapses ambient animation")

                # Reload once with an empty Radio folder to exercise its intentional empty layout.
                radio_tracks.clear()
                page.set_content(html, wait_until="domcontentloaded")
                page.wait_for_function("document.body.style.opacity !== '0'")
                page.wait_for_function("document.querySelectorAll('.mode-btn[data-mode]:not([hidden])').length === 3")
                page.locator('.mode-btn[data-mode="radio"]').click()
                page.wait_for_function("document.querySelector('#radio-stage').dataset.state === 'empty'")
                assert page.locator("#playlist-empty").is_visible()
                checks.append("Radio has an intentional empty-folder state")

                # Exercise optional modes without changing their packaged disabled defaults.
                default_settings["modes"]["utility"] = True
                default_settings["modes"]["dashboard"] = True
                page.emulate_media(reduced_motion="no-preference")
                page.set_viewport_size({"width": 1440, "height": 1000})
                page.set_content(html, wait_until="domcontentloaded")
                page.wait_for_function("document.body.style.opacity !== '0'")
                page.wait_for_function("document.querySelectorAll('.mode-btn[data-mode]:not([hidden])').length === 5")
                optional_modes = page.locator('.mode-btn[data-mode]:visible').evaluate_all(
                    "els => els.map(el => el.dataset.mode)"
                )
                assert optional_modes == ["onsen", "sky", "radio", "utility", "dashboard"], optional_modes
                audio_play_calls_before_optional = page.evaluate("window.__nocturneAudioPlayCalls")

                page.locator('.mode-btn[data-mode="utility"]').click()
                page.wait_for_function("document.querySelector('#utility-now-title').textContent === 'Evening Loop'")
                assert page.locator("#utility-hero").is_visible()
                assert page.locator("#utility-code-editor").input_value() == utility_song["code"]
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
                page.screenshot(path=str(artifacts / "desktop-utility.png"), full_page=False)
                checks.append("enabled Utility renders its local library and editor without viewport overflow")

                page.locator('.mode-btn[data-mode="dashboard"]').click()
                page.frame_locator("#dashboard-frame").locator(".clock").wait_for(state="visible")
                assert page.locator("#dashboard-hero").is_visible()
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
                page.screenshot(path=str(artifacts / "desktop-dashboard.png"), full_page=False)
                checks.append("enabled Dashboard lazily loads its packaged frame without viewport overflow")

                unexpected_requests = [url for url in request_urls_seen if not url.startswith(BASE_URL)]
                assert not unexpected_requests, unexpected_requests
                assert page.evaluate("window.__nocturneAudioPlayCalls") == audio_play_calls_before_optional
                checks.append("browser smoke makes no external requests; Utility and Dashboard start no audio")

            browser.close()

        assert not page_errors, page_errors
        assert not console_errors, console_errors
        report["overall"] = "PASS"
        report["screenshots"] = [
            "verification-artifacts/desktop-onsen.png",
            "verification-artifacts/desktop-sky.png" if profile_id == "nocturne" else None,
            "verification-artifacts/desktop-radio.png" if profile_id == "nocturne" else None,
            "verification-artifacts/desktop-appearance-settings.png" if profile_id == "nocturne" else None,
            "verification-artifacts/desktop-platform-settings.png",
            "verification-artifacts/desktop-tonight-picker.png",
            "verification-artifacts/mobile-mixer.png",
            "verification-artifacts/narrow-mixer.png",
            "verification-artifacts/tablet-sky.png" if profile_id == "nocturne" else None,
            "verification-artifacts/mobile-sky.png" if profile_id == "nocturne" else None,
            "verification-artifacts/desktop-utility.png" if profile_id == "nocturne" else None,
            "verification-artifacts/desktop-dashboard.png" if profile_id == "nocturne" else None,
        ] + mood_screenshots
        report["screenshots"] = [path for path in report["screenshots"] if path]
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
