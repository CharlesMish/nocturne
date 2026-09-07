"""Exercise the generated hosted app with real Chromium media and AudioParams.

Requires QA-only playwright. Build web/dist first. All requests are fulfilled
from that build; no API shims, fake AudioParams, or external network are used.
"""
import argparse
import json
import mimetypes
import time
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--chromium')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1] / 'dist'
artifacts = root.parent.parent / 'verification-artifacts' / 'hosted'
artifacts.mkdir(parents=True, exist_ok=True)
errors = []
checks = []
csp = next(line.split(': ', 1)[1] for line in (root / '_headers').read_text().splitlines() if line.strip().startswith('Content-Security-Policy:'))
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=args.chromium, args=['--no-sandbox'])
    for fallback in (False, True):
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.on('pageerror', lambda error: errors.append(str(error)))

        def route(request):
            url = urlparse(request.request.url)
            if url.hostname != 'nocturne.test':
                raise AssertionError(f'Unexpected external request: {url.hostname}')
            path = (root / (url.path.lstrip('/') or 'index.html')).resolve()
            if fallback and url.path == '/sounds/sound_library.json':
                request.fulfill(status=503, body='Offline manifest')
            elif root in path.parents and path.is_file():
                request.fulfill(body=path.read_bytes(), content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream', headers={'Content-Security-Policy': csp})
            else:
                request.fulfill(status=404, body='Missing')

        page.route('**/*', route)
        def wait(expression):
            # Poll via DevTools evaluation; do not require unsafe-eval in CSP.
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if page.evaluate(expression):
                    return
                page.wait_for_timeout(100)
            raise AssertionError(f'Timed out: {expression}; page errors: {errors}')

        # Observe actual media and tap the master output without replacing its
        # speakers connection, gain automation, decoding, or playback behavior.
        page.add_init_script('''
          window.qaMedia = []; window.qaMeters = [];
          const AudioNative = window.Audio;
          window.Audio = function(...args) { const a = new AudioNative(...args); qaMedia.push(a); return a; };
          window.Audio.prototype = AudioNative.prototype;
          const connect = AudioNode.prototype.connect;
          AudioNode.prototype.connect = function(destination, ...args) {
            if (destination instanceof AudioDestinationNode) {
              const meter = this.context.createAnalyser(); meter.fftSize = 2048;
              connect.call(this, meter); qaMeters.push(meter);
            }
            return connect.call(this, destination, ...args);
          };
        ''')
        page.goto('https://nocturne.test/')
        wait("document.querySelectorAll('.slot-change').length === 8 && !document.querySelector('#build-label-footer').textContent.includes('loading')")
        assert not errors, errors
        slider = page.locator('#mixer-grid input[type=range]').first
        slider.fill('40')
        page.locator('#resume-mix').click()
        wait("qaMedia.some(a => !a.paused && a.currentTime > .25 && !a.error)")
        wait('''qaMeters.some(m => {
          const data = new Float32Array(m.fftSize); m.getFloatTimeDomainData(data);
          return data.every(Number.isFinite) && data.some(x => Math.abs(x) > .00001);
        })''')
        assert page.locator('#mixer-grid .value').first.inner_text() == '40%'
        wait("document.querySelector('#bg-video').currentTime > .25 && document.querySelector('#video-stage').classList.contains('has-video')")
        assert page.locator('#bg-video').is_visible()
        page.locator('#silence').click()
        assert page.evaluate('qaMedia.every(a => a.paused)')
        assert slider.input_value() == '40'
        page.locator('#resume-mix').click()
        wait('qaMedia.some(a => !a.paused)')
        page.locator('#edit-sounds').click()
        page.locator('.slot-change').first.click()
        page.get_by_role('button', name='all', exact=True).click()
        choices = page.locator('.sound-option-select')
        assert choices.count() >= 11
        choices.last.click()
        assert slider.input_value() == '40'
        page.locator('#edit-sounds').click()
        page.screenshot(path=str(artifacts / f'desktop-{fallback}.png'))
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        page.screenshot(path=str(artifacts / f'mobile-{fallback}.png'), full_page=True)
        assert not errors, errors
        checks.append({'manifest_fallback': fallback, 'startup': 'PASS', 'real_audio_output': 'PASS', 'video_playback': 'PASS', 'silence_resume': 'PASS', 'sound_swap': 'PASS', 'phone_overflow': 'PASS'})
        page.close()
    browser.close()
report = {'overall': 'PASS', 'checks': checks, 'page_errors': errors}
(artifacts / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
