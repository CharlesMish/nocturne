# 🌙 Nocturne

**A tiny, beautiful sleep-sounds web app for Raspberry Pi.**

No app to install. Audio plays from *your* phone, laptop, or Echo. Volumes persist across sessions. Works great offline after first load.

> **"The Pi serves files. The browser mixes and plays. Perfect for bedside use."**

---

## Quick Start (on your Pi 5 or any Pi)

```bash
# 1. Get the project on your Pi
cd ~
# Option A: git clone (recommended)
git clone https://github.com/<yourname>/nocturne.git
# Option B: scp from your computer
# scp -r /path/to/sleepsounds pi@<pi-ip>:~/

cd nocturne

# 2. Create virtual environment & install
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Generate test sounds (brown / pink / white noise)
python make_test_noise.py

# 4. Test it
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://<pi-ip>:8000` (or `http://<hostname>.local:8000`) on your phone → **Add to Home Screen**.

**Make it run on boot:**

```bash
sudo cp sleepsounds.service /etc/systemd/system/sleepsounds.service
sudo systemctl daemon-reload
sudo systemctl enable --now sleepsounds
```

Check status:
```bash
systemctl status sleepsounds
journalctl -u sleepsounds -f
```

---

## How It Works

| Component       | Role                                      |
|-----------------|-------------------------------------------|
| `main.py`       | Tiny FastAPI backend (~30 lines)          |
| `static/app.js` | Web Audio API mixer (the clever part)     |
| `sounds/`       | Just drop audio files here                |
| Browser         | Does all playback + mixing locally        |

**Why this architecture wins:**
- Sound comes out of the device you're holding
- No Bluetooth audio from Pi needed
- Works even if Pi has no speaker
- Settings survive browser restart

---

## Patch Roadmap (Collaborative Plan)

The base app is already excellent and minimal. These patches fix the few real friction points and add the most valuable bedroom features.

We merged the best ideas from multiple AIs into one practical, prioritized plan moving forward.

### 1. "Resume Saved Mix" Button (Highest Daily Impact)

**Problem:** On reload, sliders show your saved volumes (e.g. 45% / 20% / 65%) but nothing plays until you touch every slider. This feels broken.

**Solution:** One prominent button.

```js
// Add to app.js
function resumeSavedMix() {
  ensureContext();                    // wakes AudioContext (required by browsers)
  for (const channel of channels.values()) {
    const percent = parseInt(channel.slider.value, 10);
    if (percent > 0) {
      setChannelVolume(channel, percent);
    }
  }
}

// Wire it up after boot()
const resumeBtn = document.createElement("button");
resumeBtn.textContent = "▶ Resume saved mix";
resumeBtn.className = "resume-btn";
resumeBtn.onclick = resumeSavedMix;
document.querySelector("main").prepend(resumeBtn);
```

**Result:** One tap → your entire saved mix starts playing instantly. Feels reliable and intentional.

---

### 2. Sleep Timer with Smart Fade (Most Valuable Feature)

**Better behavior than a simple countdown:**

- Buttons: **15 min • 30 min • 60 min • 90 min • Cancel**
- Waits the selected duration
- During the **final 60 seconds**, master volume gently fades to 0 (smooth, no abrupt cut)
- Stops all sounds
- Resets master slider visually so the next session isn't stuck at 0%

This matches how humans actually fall asleep.

(Implementation: `setTimeout` + `requestAnimationFrame` ramp on `masterGain.gain`. ~50 lines. Very satisfying.)

---

### 3. Phone App Polish (PWA + Fully Self-Contained)

Do these three together:

1. Add `static/manifest.json`
2. Add proper app icons + Apple meta tags in `index.html`
3. Remove Google Fonts (use system fonts: Georgia + system-ui)

**Benefits:**
- "Add to Home Screen" feels like a native app
- No external dependencies — works even if Pi has no internet
- Faster, more reliable on a bedside device

---

### 4. Defensive Backend Fixes (Prevent Future Headaches)

Small changes in `main.py`:

- Use full filename as sound `id` (prevents collisions like `rain.mp3` + `rain.wav`)
- URL-encode filenames: `f"/sounds/{quote(path.name)}"`
- Add simple `/health` endpoint

```python
from urllib.parse import quote

@app.get("/health")
def health():
    return {"ok": True, "sounds": len(sounds)}
```

---

### 5. systemd Hardening (Do This Last)

Only after everything else is working smoothly.

Add to `sleepsounds.service`:

```ini
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=/home/YOUR_USER/sleepsounds/sounds
```
