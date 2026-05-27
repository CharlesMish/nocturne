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

# One-step local install: venv, Python deps, folders, generated noise beds
python3 install.py

# Run locally
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` on the same machine. For phone/tablet access on your trusted LAN, run deliberately with `--host 0.0.0.0` and open `http://<pi-ip>:8000/` or `http://<hostname>.local:8000/`. Use the topbar mode switcher to jump between enabled modes. Click **Settings** to show/hide Onsen, Sky, Radio, Utility, and Dashboard without editing JSON by hand.

### Windows double-click install

On Windows, you can use the included batch launchers instead of typing commands:

1. Double-click `Install Nocturne.bat`.
2. Double-click `Start Nocturne.bat`.
3. The browser should open to `http://127.0.0.1:8000/`.

For access from another device on your trusted LAN, double-click `Start Nocturne LAN.bat` and allow Python through Windows Firewall for **private networks** only. Then open `http://<windows-pc-ip>:8000/` from the other device.

For optional third-party ambience, double-click `Fetch Ambient Media.bat`. The first run creates `media_sources.json` and opens it in Notepad; add the source URLs/creator notes, save it, then run the fetcher again.

### Optional real ambient media

The installer generates the procedural noise beds locally. It does **not** bundle third-party rain/fire/thunder MP3 files. To let each user download those directly from the original creators/source pages:

```bash
cp media_sources.example.json media_sources.json
# edit media_sources.json with direct download URLs and creator/license notes
python3 install.py --fetch-media
```

The fetcher writes `sounds/MEDIA_MANIFEST.generated.json` with source URLs, creator notes, hashes, byte sizes, and download timestamps. This keeps the public repo lightweight while making provenance easy to audit.

---

## Where audio files go

| Path                  | What it's for                                       |
|-----------------------|-----------------------------------------------------|
| `sounds/`             | Files for the **ambient mixer** (9 hardcoded slots) |
| `sounds/radio/`       | Files for **Radio mode** (any number; auto-listed)  |
| `songs/`              | Local **Utility mode** Strudel sketches             |

The ambient mixer UI is styled around nine named slots. Drop your real loop-friendly
files into `sounds/` with these exact filenames:

```text
brown-noise.wav
calming_rain.mp3
fireplace.mp3
gentle_rain.mp3
heavy_rain.mp3
heavy_storm.mp3
pinknoise.wav
thunder.mp3
white-noise.wav
```

The visible mixer labels are Calming Rain, Gentle Rain, Heavy Rain, Heavy Storm,
Thunder, Fireplace, Brown Noise, Pink Noise, and White Noise. `python
scripts/generate_noise.py` creates the procedural WAV beds. `python
scripts/fetch_media.py` downloads the optional rain/fire/thunder MP3s from your
local `media_sources.json` manifest. `python make_test_noise.py` remains as a
quick smoke-test generator for placeholder files.

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
through a small backend cache so it doesn't hammer their API. Configure
location through environment variables:

| Variable                 | Default          | Notes                                  |
|--------------------------|------------------|----------------------------------------|
| `NOCTURNE_LAT`           | `35.4676`        | Latitude                               |
| `NOCTURNE_LON`           | `-97.5164`       | Longitude                              |
| `NOCTURNE_LOCATION_NAME` | `Oklahoma City`  | What the readout shows as "where"      |
| `NOCTURNE_WEATHER_TTL`   | `600`            | Seconds the backend caches a result    |

For systemd, add them to `/etc/systemd/system/nocturne.service`:

```ini
[Service]
Environment=NOCTURNE_LAT=35.4676
Environment=NOCTURNE_LON=-97.5164
Environment=NOCTURNE_LOCATION_NAME=Oklahoma City
ExecStart=/home/<you>/nocturne/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

then `sudo systemctl daemon-reload && sudo systemctl restart nocturne`.

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

The bundled starter sketch is `songs/say-so/`. Utility mode can create, save,
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
- `GET /api/config` — exposes `latitude`, `longitude`, `location_name`
- `GET/PUT /api/settings` — reads/saves enabled mode checkboxes in `config/nocturne.json`
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
small Settings GUI now persists mode visibility to `config/nocturne.json` and
gates Utility's backend write routes when disabled. The old unused `static/app.js`
file was removed.

---

## Make it run on boot

```bash
sudo cp nocturne.service /etc/systemd/system/nocturne.service
sudo systemctl daemon-reload
sudo systemctl enable --now nocturne
journalctl -u nocturne -f
```
