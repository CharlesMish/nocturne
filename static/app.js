/* ---------------------------------------------------------------
   Nocturne — client-side audio mixer.

   How this works:
     1. We ask the server what audio files exist (/api/sounds).
     2. We build one HTML <audio> element per sound, set it to loop,
        and route it through the Web Audio graph:

           <audio> → MediaElementSource → GainNode → masterGain → speakers

     3. Each slider just adjusts a GainNode's value. That's the whole
        mixing engine — Web Audio handles the rest.
     4. Volumes are saved to localStorage, so reopening the page
        restores your mix.

   Browser autoplay policy: audio can only start after a user gesture.
   The "resume saved mix" button is the clean way to start every saved
   non-zero slider with one tap.
   --------------------------------------------------------------- */

const STORAGE_PREFIX = "nocturne:";
const TIMER_FADE_MS = 60_000;

let ctx = null;
let masterGain = null;
let sleepTimer = null;
const channels = new Map();  // id → { sound, audio, gain, source }

const channelsEl = document.getElementById("channels");
const emptyEl    = document.getElementById("empty-state");
const masterEl   = document.getElementById("master");
const masterValEl = document.getElementById("master-value");
const resumeBtn  = document.getElementById("resume-mix");
const silenceBtn = document.getElementById("silence");
const timerButtons = document.querySelectorAll("[data-timer-minutes]");
const cancelTimerBtn = document.getElementById("cancel-timer");
const timerStatusEl = document.getElementById("timer-status");

/* ---------- Persistence ---------- */

const saveVol = (key, value) => localStorage.setItem(STORAGE_PREFIX + key, String(value));
const loadVol = (key, fallback) => {
  const raw = localStorage.getItem(STORAGE_PREFIX + key);
  if (raw === null) return fallback;
  const n = parseFloat(raw);
  return isNaN(n) ? fallback : n;
};

function clampPercent(percent) {
  return Math.max(0, Math.min(100, Number(percent) || 0));
}

/* ---------- AudioContext (lazy) ---------- */

function ensureContext() {
  if (!ctx) {
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    masterGain = ctx.createGain();
    masterGain.gain.value = parseInt(masterEl.value, 10) / 100;
    masterGain.connect(ctx.destination);
  }
  if (ctx.state === "suspended") {
    ctx.resume();
  }
}

/* ---------- Channel setup ---------- */

function wireChannel(channel) {
  // Wire each <audio> through Web Audio the first time we touch it.
  // Doing this lazily keeps things cheap until the user actually starts mixing.
  if (channel.source) return;
  channel.source = ctx.createMediaElementSource(channel.audio);
  channel.gain = ctx.createGain();
  channel.gain.gain.value = 0;
  channel.source.connect(channel.gain);
  channel.gain.connect(masterGain);
}

function setChannelVolume(channel, percent) {
  percent = clampPercent(percent);
  ensureContext();
  wireChannel(channel);

  const value = percent / 100;
  // Smooth ramp avoids clicks/pops when dragging the slider.
  channel.gain.gain.setTargetAtTime(value, ctx.currentTime, 0.05);

  // Auto-play when raised from zero. We keep playing even at volume 0
  // because pausing & resuming costs more than a silent <audio> tag.
  if (percent > 0 && channel.audio.paused) {
    channel.audio.play().catch((err) => {
      console.warn(`Couldn't play ${channel.sound.id}:`, err);
    });
  }

  // Update the visual: glow strength + percentage text + slider fill.
  channel.el.style.setProperty("--vol", value.toFixed(3));
  channel.el.classList.toggle("active", percent > 0);
  channel.valueEl.textContent = `${Math.round(percent)}%`;
  channel.slider.value = percent;
  channel.slider.style.setProperty("--pct", `${percent}%`);

  saveVol(`vol:${channel.sound.id}`, percent);
}

function buildChannelCard(sound) {
  const card = document.createElement("div");
  card.className = "channel";
  card.dataset.id = sound.id;

  const row = document.createElement("div");
  row.className = "channel-row";

  const name = document.createElement("span");
  name.className = "channel-name";
  name.textContent = sound.name;

  const value = document.createElement("span");
  value.className = "channel-value";
  value.textContent = "0%";

  row.append(name, value);

  const slider = document.createElement("input");
  slider.type = "range";
  slider.min = 0;
  slider.max = 100;
  slider.step = 1;
  slider.value = 0;
  slider.setAttribute("aria-label", `${sound.name} volume`);

  card.append(row, slider);

  const audio = new Audio(sound.url);
  audio.loop = true;
  audio.preload = "auto";
  audio.crossOrigin = "anonymous";

  const channel = {
    sound,
    audio,
    el: card,
    slider,
    valueEl: value,
    source: null,
    gain: null,
  };
  channels.set(sound.id, channel);

  slider.addEventListener("input", () => {
    setChannelVolume(channel, parseInt(slider.value, 10));
  });

  // Restore saved volume visually. We do not auto-play on page load,
  // because browsers require a click/touch first. Use "resume saved mix".
  const saved = clampPercent(loadVol(`vol:${sound.id}`, 0));
  slider.value = saved;
  card.style.setProperty("--vol", (saved / 100).toFixed(3));
  card.classList.toggle("active", saved > 0);
  value.textContent = `${Math.round(saved)}%`;
  slider.style.setProperty("--pct", `${saved}%`);

  return card;
}

/* ---------- Master volume ---------- */

function setMaster(percent, options = {}) {
  const { persist = true, fromTimer = false } = options;
  percent = clampPercent(percent);
  ensureContext();

  const value = percent / 100;
  masterGain.gain.setTargetAtTime(value, ctx.currentTime, 0.05);
  masterEl.value = percent;
  masterValEl.textContent = `${Math.round(percent)}%`;
  masterEl.style.setProperty("--pct", `${percent}%`);

  if (persist) {
    saveVol("master", percent);
  }
  if (sleepTimer && !fromTimer) {
    sleepTimer.baseMaster = percent;
  }
}

masterEl.addEventListener("input", () => {
  setMaster(parseInt(masterEl.value, 10));
});

/* ---------- Resume saved mix ---------- */

function resumeSavedMix() {
  let started = 0;

  for (const channel of channels.values()) {
    const percent = clampPercent(parseInt(channel.slider.value, 10));
    if (percent > 0) {
      setChannelVolume(channel, percent);
      started += 1;
    }
  }

  if (started === 0) {
    timerStatusEl.textContent = "raise one or more sliders, then your mix will be saved here";
  } else {
    timerStatusEl.textContent = `playing ${started} saved sound${started === 1 ? "" : "s"}`;
  }
}

resumeBtn.addEventListener("click", resumeSavedMix);

/* ---------- Sleep timer ---------- */

function formatRemaining(ms) {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes <= 0) return `${seconds}s`;
  return `${minutes}m ${String(seconds).padStart(2, "0")}s`;
}

function setActiveTimerButton(minutes) {
  for (const button of timerButtons) {
    button.classList.toggle("active", button.dataset.timerMinutes === String(minutes));
  }
}

function clearSleepTimer(message = "") {
  if (sleepTimer) {
    clearInterval(sleepTimer.intervalId);
    sleepTimer = null;
  }
  setActiveTimerButton(null);
  timerStatusEl.textContent = message;
}

function pauseAllWithoutChangingSavedMix() {
  for (const channel of channels.values()) {
    if (channel.gain && ctx) {
      const currentVol = clampPercent(parseInt(channel.slider.value, 10)) / 100;
      channel.gain.gain.cancelScheduledValues(ctx.currentTime);
      channel.gain.gain.setValueAtTime(currentVol, ctx.currentTime);
    }
    channel.audio.pause();
  }
}

function finishSleepTimer() {
  if (!sleepTimer) return;

  const baseMaster = sleepTimer.baseMaster;
  clearSleepTimer("timer finished — tap resume saved mix to play again");
  pauseAllWithoutChangingSavedMix();

  // Put the master slider back where it was before the fade, without saving
  // a temporary fade value like 0% to localStorage.
  setMaster(baseMaster, { persist: false, fromTimer: true });
}

function tickSleepTimer() {
  if (!sleepTimer) return;

  const remaining = sleepTimer.endAt - Date.now();
  if (remaining <= 0) {
    finishSleepTimer();
    return;
  }

  if (remaining <= sleepTimer.fadeMs) {
    const ratio = remaining / sleepTimer.fadeMs;
    setMaster(sleepTimer.baseMaster * ratio, { persist: false, fromTimer: true });
  }

  timerStatusEl.textContent = `sleep timer: ${formatRemaining(remaining)} remaining`;
}

function startSleepTimer(minutes) {
  ensureContext();
  clearSleepTimer();

  const durationMs = minutes * 60 * 1000;
  sleepTimer = {
    endAt: Date.now() + durationMs,
    fadeMs: Math.min(TIMER_FADE_MS, durationMs),
    baseMaster: clampPercent(parseInt(masterEl.value, 10)),
    intervalId: null,
  };

  setActiveTimerButton(minutes);
  sleepTimer.intervalId = setInterval(tickSleepTimer, 500);
  tickSleepTimer();
}

for (const button of timerButtons) {
  button.addEventListener("click", () => {
    startSleepTimer(parseInt(button.dataset.timerMinutes, 10));
  });
}

cancelTimerBtn.addEventListener("click", () => {
  if (sleepTimer) {
    const baseMaster = sleepTimer.baseMaster;
    clearSleepTimer("sleep timer cancelled");
    setMaster(baseMaster, { persist: false, fromTimer: true });
  } else {
    clearSleepTimer();
  }
});

/* ---------- Silence all ---------- */

silenceBtn.addEventListener("click", () => {
  clearSleepTimer();
  for (const channel of channels.values()) {
    channel.slider.value = 0;
    setChannelVolume(channel, 0);
    // Pause once volume is zero — the silence button means "stop".
    channel.audio.pause();
  }
});

/* ---------- Boot ---------- */

async function boot() {
  // Restore master volume visually. We don't create the AudioContext until
  // the first user gesture.
  const savedMaster = clampPercent(loadVol("master", 70));
  masterEl.value = savedMaster;
  masterValEl.textContent = `${Math.round(savedMaster)}%`;
  masterEl.style.setProperty("--pct", `${savedMaster}%`);

  let sounds;
  try {
    const res = await fetch("/api/sounds");
    sounds = await res.json();
  } catch (err) {
    emptyEl.textContent = "couldn't reach the server";
    return;
  }

  if (!sounds.length) {
    emptyEl.textContent = "drop audio files into the sounds/ folder";
    return;
  }

  emptyEl.remove();
  for (const sound of sounds) {
    channelsEl.appendChild(buildChannelCard(sound));
  }
}

boot();