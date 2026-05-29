# 🌙 Nocturne

**A tiny, beautiful sleep web app for Raspberry Pi.**

Five modes share the same bedside-friendly aesthetic:

- **Onsen** — the original rainy-onsen video + 8-channel ambient mixer
- **Sky** — the ambient mixer plus a quiet moon-phase + local-weather visual
- **Radio** — a late-night personal broadcast that plays tracks from `sounds/radio/`
- **Utility** — a local Strudel code sketchbook with a handoff link to strudel.cc
- **Dashboard** — the uploaded Raspberry Pi terminal/weather screen from `static/Dashboard_v4.html`

The Pi serves files. The browser does all the mixing and playback locally on
whatever device you're holding. Volumes and the last selected mode persist in
the browser. A small in-app **Settings** panel lets non-technical users choose
which modes appear; those feature gates are saved on the server in
`config/nocturne.json`. Works offline after first load for the sleep/radio
pieces (the Sky visual just falls back to a calm "weather offline" view).
Utility mode does not serve or embed Strudel; it stores code locally and opens
the current sketch on strudel.cc when you want playback.

---

## Quick Start

```bash
cd ~/nocturne
python3 install.py
source .venv/bin/activate
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open `http://localhost:8000` on the same machine.

`python3 install.py` creates the virtualenv, installs Python dependencies, creates the local folders, and generates `pinknoise.wav`. Nocturne works with that generated pink noise before the optional rain/fire/thunder MP3 files are installed.

For phone/tablet access on your trusted LAN, run deliberately with `--host 0.0.0.0` and open `http://<pi-ip>:8000/` or `http://<hostname>.local:8000/`. Use the topbar mode switcher to jump between enabled modes. Click **Settings** to show/hide Onsen, Sky, Radio, Utility, and Dashboard without editing JSON by hand.

### Launchers

On Windows:

1. Double-click `Install Nocturne.bat`.
2. Double-click `Start Nocturne.bat`.
3. The browser should open to `http://127.0.0.1:8000/`.

For LAN access from another device, double-click `Start Nocturne LAN.bat` and allow Python through Windows Firewall for **private networks** only.

On macOS, double-click `Install Nocturne.command`; if Gatekeeper blocks it, right-click the file and choose **Open** the first time.

---

## Optional: full ambience media

The ambient mixer has eight channels. The app can start with generated `pinknoise.wav`, and the seven MP3 channels can be added later.

To verify which files are present:

```bash
python3 check_audio_contract.py
```

To install the optional MP3 ambience from source pages:

1. `cp media_sources.default.json media_sources.json`
2. Open the 7 Pixabay source pages listed inside the file.
3. In DevTools → Network tab, capture the current `cdn.pixabay.com/audio/...` direct URL for each.
4. Paste the seven URLs into the `url` fields and save.
5. Re-run `python3 install.py --fetch-media` (or just `python3 install.py`).

On Windows, `Fetch Ambient Media.bat` creates `media_sources.json` from the default manifest and opens it in Notepad the first time. After you fill the URL fields, run it again.

Useful flags:

```bash
python3 install.py --no-fetch-media
python3 install.py --fetch-media
```

The fetcher writes `sounds/MEDIA_MANIFEST.generated.json` with full provenance: source URLs, hashes, and timestamps. This keeps the public repo clean while making every file auditable.

You can also just drop your own loop-friendly files into `sounds/` using the exact filenames below — no manifest needed. Run `python3 check_audio_contract.py` afterward to see what the mixer sees.

---

## Where audio files go

| Path                  | What it's for                                       |
|-----------------------|-----------------------------------------------------|
| `sounds/`             | Files for the **ambient mixer** (8 hardcoded slots) |
| `sounds/radio/`       | Files for **Radio mode** (any number; auto-listed)  |
| `songs/`              | Local **Utility mode** Strudel sketches             |

The ambient mixer UI is styled around eight named slots. Drop your real loop-friendly
files into `sounds/` with these exact filenames:

```text
calming_rain.mp3
gentle_rain.mp3
heavy_rain.mp3
rainstorm.mp3
heavy_storm.mp3
thunder.mp3
fireplace.mp3
pinknoise.wav
```

The visible mixer labels are Calming Rain, Gentle Rain, Heavy Rain, Rainstorm,
Heavy Storm, Thunder, Fireplace, and Pink Noise.

`python scripts/generate_noise.py` creates three optional WAV beds (brown, pink, white).
Only `pinknoise.wav` is a visible mixer channel in v0.1.

After adding or changing files, run `python3 check_audio_contract.py` — it will
tell you exactly which of the 8 required channels are present and their sizes.

`python scripts/fetch_media.py` (or the automatic path inside `install.py`) downloads
the seven MP3s from a local manifest when you provide current direct URLs.

Radio tracks are dynamic. Anything in `sounds/radio/` is served via `/api/radio`
and reached at `/sounds/radio/<filename>`. Supported extensions: `mp3 · ogg ·
m4a · wav · opus · webm · flac`. Filenames become track titles —
`night-drive.mp3` → "Night Drive". No restart required when adding or removing
radio files; just refresh the browser.

---

## Settings GUI

Click **Settings** in the top bar to choose which modes are visible. The app
saves those checkboxes to:

```text
config/nocturne.json
```

The default server setting is:

```json
{
  "modes": {
    "onsen": true,
    "sky": true,
    "radio": true,
    "utility": false,
    "dashboard": true
  }
}
```

Utility is off by default because it is the only mode that writes user files
under `songs/`. When Utility is off, its `/api/songs` routes return `404`, so
the sketchbook write surface is hidden as well as removed from the UI.

`config/nocturne.example.json` is committed as a reference. The live
`config/nocturne.json` file is ignored by Git because it is per-device state.

## Configuration (location + weather)

Sky mode pulls current conditions from **Open-Meteo** (no API key required)
through a small backend cache so it doesn't hammer their API. Configure the
weather location from **Settings → Location** in the app; changes are saved to
`config/nocturne.json` and the weather cache is refreshed.

Manual latitude/longitude entry always works. The **Use browser location**
button is only a convenience; browsers usually allow it on `localhost` or HTTPS,
and may block it from a phone over plain LAN HTTP.

The default location is:

```json
{
  "label": "Chicago",
  "latitude": 41.8781,
  "longitude": -87.6298,
  "timezone": "America/Chicago",
  "temperature_unit": "fahrenheit"
}
```

Environment variables are still available as fallback defaults before a saved
location exists:

| Variable                 | Default          | Notes                                  |
|--------------------------|------------------|----------------------------------------|
| `NOCTURNE_LAT`           | `41.8781`        | Latitude                               |
| `NOCTURNE_LON`           | `-87.6298`       | Longitude                              |
| `NOCTURNE_LOCATION_NAME` | `Chicago`        | What the readout shows as "where"      |
| `NOCTURNE_TIMEZONE`      | `America/Chicago` | Open-Meteo timezone                  |
| `NOCTURNE_TEMPERATURE_UNIT` | `fahrenheit`  | `fahrenheit` or `celsius`              |
| `NOCTURNE_WEATHER_TTL`   | `600`            | Seconds the backend caches a result    |

For systemd, add optional `Environment=` lines like these only if you want to
change the fallback defaults:

```ini
[Service]
Environment=NOCTURNE_LAT=41.8781
Environment=NOCTURNE_LON=-87.6298
Environment=NOCTURNE_LOCATION_NAME=Chicago
Environment=NOCTURNE_TIMEZONE=America/Chicago
Environment=NOCTURNE_TEMPERATURE_UNIT=fahrenheit
ExecStart=/home/<you>/nocturne/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

then run `sudo systemctl daemon-reload && sudo systemctl restart nocturne`
after installing the service.

### Graceful degradation

If Open-Meteo is unreachable, the API returns the last cached result tagged
`stale: true`, and the UI shows a slightly desaturated scene with
`(stale)` appended to the condition line. If there's no cached result at all
(first boot, no network), the UI falls back to a calm clear-night render
with `weather offline` in the readout. No errors, no broken state.

---

## The five modes

### Onsen
Untouched. The looping rain video and 8-channel mixer behave exactly as
before.

### Sky
Mixer still visible and functional. The video stage is replaced by a wide
night-sky scene rendered with the same layer-and-parallax system as the
onsen scene. The moon is an SVG whose terminator is computed client-side
from the synodic month (no API needed). Cloud, rain, snow, fog, and
lightning layers are toggled by weather class (`w-clear`, `w-rain`, etc.)
when the backend returns a current WMO weather code. A small monospace
readout at the bottom-left shows condition + temperature, moon name +
illumination, and location.

### Radio
A tape-deck on the left, a playlist on the right. Tracks are loaded from
`sounds/radio/` and played through a Web Audio graph that lands at the
same master gain node as the mixer, so:

- The **master volume** still trims the radio (existing global control).
- A separate **broadcast** slider on the deck controls the radio's own gain.
- A **warmth** slider applies an optional low-pass (22050 → 2500 Hz,
  logarithmic) for a lo-fi tilt — left at 0% for full fidelity by default.

Sleep-friendly behavior:
- Shuffle on by default; toggleable.
- Auto-advance on track end.
- Errors auto-skip after 1.5 s.
- The "silence all" button on the main control row stops the mixer *and*
  the radio in one tap.

The deck reels rotate only while a track is playing. A VU-style segmented
meter is driven by an `AnalyserNode` and only animates while radio mode is
visible (saves Pi CPU when it's not on screen).


### Dashboard
The uploaded `Dashboard_v4.html` is served from `static/Dashboard_v4.html` and embedded as a fifth Nocturne mode. It stays self-contained inside an iframe so its fixed full-screen CRT layout, canvas animations, keyboard preset switching, and CSS variables do not conflict with the main Nocturne interface. The iframe loads only when Dashboard mode is selected and unloads when you leave that mode to avoid extra background rendering on the Pi.


### Utility
A workbench-style Strudel code sketchbook lives inside the fourth topbar mode. It is
intentionally more "tool" than sleep scene, but it uses Nocturne's stone,
lantern, sakura, and paper colors so it still belongs in the same app. Nocturne
only saves the code and metadata locally; the **open in strudel** button creates
a long `https://strudel.cc/#...` URL for the current code and opens it in a new tab.

Sketches are stored on disk as:

```text
songs/<slug>/meta.json
songs/<slug>/code.js
```

The bundled starter sketch is `songs/evening-loop/`. Utility mode can create, save,
duplicate, and delete sketches through the FastAPI backend. The visible editor
is a plain textarea, so it works over ordinary LAN HTTP and does not require
`AudioWorklet`, HTTPS, CDN scripts, or Strudel runtime code inside Nocturne.

---

## How modes interact with audio

Audio state is **independent of view mode** for Onsen / Sky / Radio / Dashboard. Switching
those tabs only changes what's visible; it doesn't pause or resume anything.
Utility mode is separate: it does not play audio inside Nocturne; playback happens after opening the sketch on strudel.cc.
This means:

- You can leave ambient rain playing and switch to Radio to add music on top.
- Coming back to Onsen or Sky shows the mixer with its current volumes.
- Dashboard is visual-only; switching to it does not change ambient or radio playback.
- "Silence all" is the single panic button that stops everything.

To save CPU on the Pi, the rain video is paused when not visible (it's
muted, so this only saves rendering cost), and the radio VU meter stops
animating when not visible.

---

## What changed in this update

**New endpoints** (`main.py`):

- `GET /api/radio` — lists `sounds/radio/` tracks
- `GET /api/weather` — cached current weather from Open-Meteo
- `GET /api/config` — exposes non-secret location config for the UI
- `GET/PUT /api/settings` — reads/saves enabled modes and Sky weather location in `config/nocturne.json`
- `GET /api/songs` — lists saved Utility sketches when Utility is enabled
- `GET/POST/PUT/DELETE /api/songs/...` — loads, saves, duplicates, and deletes sketches when Utility is enabled

**New dependency:** `httpx` (added to `requirements.txt`).

**Sleep timer:** 15 / 30 / 60 / 90 minute buttons now fade the master
volume during the final minute, then pause the mixer and radio without
overwriting your saved mix.

**Frontend:** the existing `static/index.html` was extended in-place
(everything still in one self-contained file, matching the existing
pattern). The sleep timer now lives in the active page and fades the
shared master bus before pausing both ambient channels and radio. The
fourth Utility mode was merged from the uploaded Strudel Sketchbook, then
changed to a code-only handoff workflow that opens sketches on strudel.cc. A
small Settings GUI now persists mode visibility and Sky weather location to
`config/nocturne.json` and gates Utility's backend write routes when disabled.
The old unused `static/app.js` file was removed.

---

## Make it run on boot

Edit `nocturne.service` first: replace `YOUR_USER` with your Pi username.
Sky weather location can be changed later from the in-app Settings panel.

```bash
sudo cp nocturne.service /etc/systemd/system/nocturne.service
sudo systemctl daemon-reload
sudo systemctl enable --now nocturne
journalctl -u nocturne -f
```
