**Hopeful Skeptic Review — Nocturne v0.2-polished**  
**Derived from:** Hopeful Skeptic Core v0.4.1  
**Role:** Independent second-eyes auditor + implementation-readiness / release-gate reviewer  
**Mode:** Review only + static package inspection (full inventory of text, manifests, scripts, structure; audio files present but not auditioned; no clean install/execution of the server or noise generator performed in this environment)  
**Coverage:** Risk-prioritized full (architecture, sound contract, polish claims vs reality, audit tooling, a11y, provenance, handoff fidelity, release integrity). Residual: actual listening comfort, loop seams, browser runtime quirks, Pi-specific behavior.

### Decision Summary

**Overall disposition:** Solid craft foundation with clear protected intent, but the v0.2 polish pass is incomplete and partially self-contradictory. The release is **not yet release-ready**. The FAIL from `release-audit` is real but mostly an auditor design problem rather than a catastrophic content problem. Highest-leverage work for the next round is: (1) make the polish actually load, (2) make defaults match the handoff claims, (3) fix the release auditor so it stops treating install-time generated assets and provenance metadata as hard errors, and (4) re-stamp + re-verify.

**Critical / Major issues that change the next decision:**
- A11y polish CSS exists but is dead (not linked/inlined). Main HTML still does `outline: none` on `:focus`.
- HANDOFF + polish docs claim Waves removed from defaults; both `sounds/sound_library.json` and the embedded `DEFAULT_SOUND_LIBRARY` in `static/index.html` still contain it.
- Release audit produces 171 errors by design mismatch (generated-on-install + rich provenance metadata containing original filenames). The FAIL is currently low-signal.

**Highest-leverage repairs (do these first):**
1. Wire `nocturne-polish.css` (or inline its rules) and remove the bare `:focus { outline: none }`.
2. Align `default_slots` (JSON + embedded fallback) with the claimed “Tonight” set that excludes Waves.
3. Make `scripts/release-audit.mjs` understand the packaging model (generated paths expected missing in the zip; metadata fields are not “audio references”).
4. Re-run `stamp_build.py`, update ALPHA_FEEDBACK / footer / build label, regenerate credits if needed, and re-verify.

**Preserved strengths (do not break these):** local-first purity, honest generated-bed naming, careful CC0 provenance workflow + screenshots + hashes, reversible Silence/Resume model, intentional first Radio use, Tonight hierarchy intent, no accounts/cloud/SaaS, clear scope ceiling, good installers/launchers, bedside acceptance card, and the decision not to widen the product.

**Material residual risk:** Without a real listening pass (headphones + phone + bedside speaker, 10+ min per default) the “sleep-safe / quiet / seamless” claims remain aspirational. Software checks correctly refuse to certify that.

---

### Atomic Findings Ledger (ranked by severity + actionability)

**F1 — Polish CSS not integrated (a11y contract broken)**  
- **Severity:** Major  
- **Confidence:** High  
- **Evidence status:** Confirmed finding  
- **Verification state:** Statically inspected  
- **Type:** Implementation drift / communication  
- **Concern:** `nocturne-polish.css` contains the promised `:focus-visible`, 44px coarse-pointer targets, reduced-motion/forced-colors safeguards, and `.visually-hidden`. It is listed in `polish-edit-record.json` as a changed file. It is **not** linked or inlined in `static/index.html`. The huge inline `<style>` still contains multiple `:focus { outline: none; }` rules and zero `:focus-visible`.  
- **Evidence:** `grep` on `static/index.html` shows 0 occurrences of `focus-visible`; polish file exists at root and is never referenced; `main.py` only mounts `static/` and `sounds/`.  
- **Likely origin:** Artifact-generated (incomplete polish pass after interruption).  
- **Priority:** Immediate (before any claim of a11y polish).  
- **Disposition:** Fix  
- **Suggested repair:** Either (a) `<link rel="stylesheet" href="/nocturne-polish.css">` after moving the file under `static/`, or (b) inline the 1.8 kB rules at the end of the existing `<style>` block. Then delete or override the bare `:focus { outline: none }` rules. Re-check that reduced-motion already present in the inline CSS is not duplicated destructively.  
- **Preservation constraint:** Keep the component-local visual decisions; the polish layer was deliberately “quiet global safeguards only.”

**F2 — Waves still in defaults despite handoff claim**  
- **Severity:** Major  
- **Confidence:** High  
- **Evidence status:** Confirmed finding  
- **Verification state:** Statically inspected  
- **Type:** Implementation drift  
- **Concern:** HANDOFF.md and `docs/POLISH_PASS_V0_2.md` explicitly say “Waves is removed from defaults rather than silently altered.” `docs/IMPLEMENTATION_STATUS.md` already flags “Waves default removal — NOT CONFIRMED.” Both sources of truth still list it:  
  `default_slots: ['rain-heavy-open-window', 'rain-balcony-peaceful', 'rain-tent-heavy', 'fire-crackling-loop', 'crickets-at-night-clean', 'waves-on-shore', 'fan-room-bed', 'low-rumble-bed']`  
  (identical in `sounds/sound_library.json` and the embedded `DEFAULT_SOUND_LIBRARY` inside `static/index.html`).  
- **Priority:** Immediate  
- **Disposition:** Fix (or retract the claim)  
- **Suggested repair:** Decide the real Tonight set (recommend 6 recorded + 2 generated safety beds, or pure recorded if you want zero install-time dependency for defaults). Update both the JSON and the embedded fallback in lockstep. Re-generate any fallback docs. Update IMPLEMENTATION_STATUS.  
- **Preservation constraint:** Do not silently alter the sound itself; just stop shipping it as ordinary default.

**F3 — Release audit is high-false-positive and currently low-signal**  
- **Severity:** Major (blocks clean release signal)  
- **Confidence:** High  
- **Evidence status:** Confirmed finding  
- **Verification state:** Statically inspected + audit log read  
- **Type:** Measurement mismatch / tooling  
- **Concern:** `scripts/release-audit.mjs` scans every text file for any literal string that looks like an audio path (`…\.mp3|wav|…`) and errors if the file does not exist on disk. This correctly catches real missing assets but also:
  - every generated `.wav` (intentionally absent until `install.py` / `generate_noise.py`)
  - every original filename and `src` inside `sound_library.json` provenance fields
  - documentation examples, MEDIA_LICENSES, AUDIO_PROVENANCE, README, etc.
  Result: 171 errors, 12 audio assets “pass”, overall FAIL. The FAIL is true but almost useless for deciding whether the package is shippable.  
- **Priority:** Before next release stamp  
- **Disposition:** Fix  
- **Suggested repair (minimal):**  
  - Whitelist known install-time generated paths.  
  - Only treat `src` fields (or explicit path-like attributes) as hard references; ignore `original_filename`, `source_title`, free-text notes.  
  - Exclude `docs/`, `AUDIO_*.md`, `MEDIA_LICENSES.md`, `PATCH_NOTES*`, provenance, and the audit script itself from the hard-reference check (or make them warnings).  
  - Keep the duplicate-payload, empty-audio, quarantine-leak, and interaction-signal checks — those are valuable.  
- **Alternative:** Keep the strict audit for a “shipped-with-all-generated” mode and add a “source-only / generated-on-install” mode.

**F4 — Build / feedback identity drift**  
- **Severity:** Moderate  
- **Confidence:** High  
- **Evidence status:** Confirmed  
- **Concern:** `nocturne_build.json` still shows `v0.1.0-alpha.8 · 2026-06-30 · 47e3d82` while HANDOFF, verification timestamps, and polish work are 2026-07-11. ALPHA_FEEDBACK.md and the page footer still advertise the old label. Users (and you) will paste the wrong build into bug reports.  
- **Priority:** Immediate before any external share  
- **Disposition:** Fix  
- **Suggested repair:** `python scripts/stamp_build.py --version 0.1.0-alpha.9` (or whatever the next label is) after the real fixes land. Update ALPHA_FEEDBACK template and any hard-coded strings.

**F5 — Dual catalog drift risk (JSON vs embedded fallback)**  
- **Severity:** Moderate  
- **Confidence:** High  
- **Evidence status:** Strongly supported  
- **Type:** Implementation drift / maintainability  
- **Concern:** `static/index.html` embeds a full copy of the sound library (~29 entries + default_slots) as `DEFAULT_SOUND_LIBRARY`. Runtime prefers `/sounds/sound_library.json` but falls back to the embedded one. Any future change must be made in two places; they already drifted on the Waves claim.  
- **Priority:** Next revision (or now if you touch defaults)  
- **Disposition:** Fix (or accept + document)  
- **Suggested repair:** Prefer generating the fallback from the JSON at build/stamp time, or document a single-source rule + a check in release-audit that the two are byte-identical after normalization.

**F6 — Default slots still mix install-time generated assets**  
- **Severity:** Moderate (becomes Major if install fails)  
- **Confidence:** Medium-High  
- **Evidence status:** Confirmed for the current set  
- **Concern:** Two of the eight “Tonight” slots are generated (`fan-room-bed`, `low-rumble-bed`). If a user skips install or the generator fails, those slots are missing/unavailable. The UI does mark unavailable channels, but the ordinary first-run experience is weaker.  
- **Priority:** Before release (decide)  
- **Disposition:** Human-confirm + Fix or Accept risk  
- **Suggested repair:** Either make all eight defaults recorded CC0 only, or keep 1–2 generated safety beds and document “after install.py” clearly in README + first-run copy.

**F7 — Quarantine / experimental boundary is documentation-only in this tree**  
- **Severity:** Minor–Moderate  
- **Confidence:** Medium  
- **Evidence status:** Plausible concern  
- **Concern:** soft-wind-trees and other seam-risk items are mentioned in PATCH_NOTES / HANDOFF as quarantined, but there is no `sounds/inbox/quarantine-…` tree or runtime filter that would prevent a future import script from re-exposing them. The release-audit only warns on the word “quarantine” in docs.  
- **Priority:** Next revision  
- **Disposition:** Monitor / light Fix (add a real quarantine path or an explicit “excluded_ids” list in the library JSON that the picker honors).

**F8 — Index.html size and monolith**  
- **Severity:** Minor (maintainability)  
- **Confidence:** High  
- **Type:** Scope / long-term  
- **Concern:** ~267 kB single HTML with huge inline CSS + full library fallback + all mode UIs. This is intentional (no build step) and fits the “one HTML file” aesthetic, but it makes surgical polish harder and increases the chance of accidental breakage when editing.  
- **Priority:** Optional  
- **Disposition:** Accept risk for now (protected by the “no frontend framework rewrite” constraint).

**Cleared after checking (or low materiality):**
- Python compile and whitespace checks pass.  
- 12 CC0 MP3s are present and non-empty.  
- Provenance (AUDIO_PROVENANCE, screenshots, hashes, honest “Generated” labels) is unusually strong for an alpha.  
- Silence/Resume, aria-pressed, reduced-motion, Tonight surface, intentional Radio first-use all have static signals.  
- No accounts, no cloud, no analytics, Utility gated, Dashboard optional — protected intent intact.  
- Installers (bat/command/sh/service) and ready-message are present and sensible.

---

### Decision and Preservation Map

1. **Release- or decision-blocking**  
   - A11y polish not actually active (F1).  
   - Defaults contradict the handoff claims (F2).  
   - Release audit cannot currently give a trustworthy green light (F3).  
   - Build label is stale (F4).

2. **Highest-leverage repairs (ordered)**  
   1. Integrate polish CSS + kill bare `outline: none`.  
   2. Decide and lock the real 8-slot Tonight set (remove Waves or keep it and fix the docs). Update both catalogs.  
   3. Teach release-audit the packaging model (generated-on-install + provenance metadata).  
   4. Stamp new build, regenerate any credits if needed, re-run verification.  
   5. Optional but high value: make defaults 100 % recorded CC0 so first-run never depends on the generator.

3. **Objects to keep / narrow / verify / human-confirm**  
   - Keep the reversible Silence → Resume model, the Tonight hierarchy language, the “intentional first Radio use,” the honest generated naming, the CC0 + generated split, the bedside acceptance card, and the explicit boundary “software checks ≠ listening evidence.”  
   - Human-confirm (you or a friend): actual 10-minute listens of the final Tonight set on phone speaker + headphones + intended bedside device. Record loops, clicks, fatigue, level jumps.  
   - Verify after fixes: `node scripts/release-audit.mjs` should produce a useful report, not 171 false positives.

4. **What appears solid and should be preserved**  
   - Local-first, zero-account, LAN/Pi-first design.  
   - Careful provenance audit trail and honest synthetic-bed language.  
   - Scope discipline (no new modes, no personalization machinery, no content funnel).  
   - Install-time generation of usable beds so the app is never completely silent.  
   - Utility and Dashboard correctly gated and write-surface-hidden when off.  
   - The overall “quiet bedside ritual” aesthetic and copy tone.

5. **Open questions that actually matter**  
   - Final Tonight set composition and whether any generated bed stays in the ordinary first-run experience.  
   - Whether the embedded library fallback should be generated at stamp time or live with dual-maintenance risk.  
   - Sleep-safety / loop quality of the current 8 defaults (only human ears can answer).  
   - Whether `soft-thunderstorm-bed` / `distant-thunder-bed` ever graduate from “audition candidate.”

6. **Coverage boundary and residual risk**  
   - Fully inspected: structure, manifests, key scripts, CSS integration, default_slots, audit logic, handoff vs reality, a11y signals, provenance docs, install flow description.  
   - Statically inspected but not executed: main.py FastAPI routes, generate_noise.py synthesis, fetch_media, full HTML/JS runtime behavior.  
   - Not reviewed / not possible here: real-device audio comfort, loop seams under long listen, browser autoplay / interruption edge cases, actual Raspberry Pi 5 CPU/memory under all modes, screen-reader announcement quality.  
   - Residual high-risk: first-run experience if generator fails; dual-catalog drift; any future “polish” that is written but not wired.

7. **Free unstructured pass (what I re-examined)**  
   Re-read HANDOFF against actual files, walked every default_slots occurrence, checked CSS loading path, scanned release-audit.mjs for its exact matching rules, compared AUDIO_CREDITS / PROVENANCE / MEDIA_LICENSES / README claims against the on-disk library, looked for any remaining Pixabay fixed-filename assumptions that could surprise a new user, and re-checked the IMPLEMENTATION_STATUS table against the tree. No additional critical defects surfaced beyond the ledger above. The strongest remaining feeling is that the *intent* of the v0.2 polish is excellent and the *execution* is one wiring + one consistency pass away from being trustworthy.

---

### Practical next-round build list (actionable)

1. **Wire the polish** (F1) — 15–30 min.  
2. **Lock Tonight defaults** (F2 + F6) — decide set, edit both catalogs, update docs.  
3. **Tame the auditor** (F3) — make it respect generated-on-install + provenance.  
4. **Stamp + verify** (F4) — new label, clean release-audit, re-generate verification-report.  
5. **Human listening pass** using the Bedside Acceptance Card — only then promote anything.  
6. (Optional) Generate the embedded fallback from the JSON so dual maintenance dies.  
7. Re-read `docs/IMPLEMENTATION_STATUS.md` after the above; make every row match reality.

The project still feels like the same quiet, self-respecting bedside instrument it set out to be. The current tree is a clean base; the polish pass just needs its last few connections soldered and its claims made true. Once those land, this is ready for a real alpha listen cycle rather than more code churn.

I’m happy to implement any of the above (or a subset) in a follow-up turn, or to dive deeper on any single finding (e.g. draft the exact default_slots list, patch the auditor, or produce a minimal patch set). Just say the word.