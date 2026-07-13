**Hopeful Skeptic Review**  
**Artifact:** `nocturne-alpha10-product-v0.3.0.zip` (build label `v0.1.0-alpha.10 · 2026-07-11 · product-v0.3.0`)  
**Protocol:** Hopeful Skeptic Core v0.4.1 (direct general review; no Project Edition yet)  
**Role:** Independent auditor + release-gate / implementation-readiness reviewer  
**Mode:** Static package inspection + limited script execution (audio contract, JSON consistency). No full browser runtime, no clean-repro install of the full audio set, no live Media Session / lock-screen device matrix, no human audition of loops.  
**Coverage:** Risk-prioritized full on the alpha.10 product-pass claims (local scenes, Media Session + visibility resume, web-app manifest/icons, offline cyclic-crossfade baker + quarantine/detached evidence, packaging honesty, catalog contract, platform caveats). Residual: full browser/device matrix, overnight survival, subjective loop comfort, and the detached evidence bundle itself.

### Decision Summary

**Overall disposition:** Strong, unusually honest alpha product package that is ready for careful field testing by people who understand the stated limits. It does **not** need a rewrite. A few moderate/major-but-non-blocking improvements and one verification gap should be closed before treating the new platform features as “field-proven.”

**Critical findings:** None that block distribution of this alpha or make the package actively misleading.

**Major findings / highest-leverage items:**
1. Platform integration (Media Session + return-from-background notice + install identity) is correctly feature-detected and carefully caveated in docs/UI, but remains **unverified by actual multi-device lock-screen / app-switch / long-return testing** inside this package. The code path exists; the field evidence does not yet.
2. Local scenes are a clean, useful addition (browser-local only, capped, normalizes well) but have no server-side export/import or conflict story; that is fine for alpha but should be called out so testers don’t invent expectations.
3. Seam-baking + quarantine discipline is excellent (numerical screen + `audition_required` + public path guard + detached evidence). The one rendered candidate is correctly kept non-public; promotion still correctly requires human audition.

**Highest-leverage repairs (non-blocking for this alpha):**
- Explicitly document (and ideally script) a minimal “device integration field matrix” that must be filled before any claim language moves from “feature-detected / offered” to “works on X”.
- Add a one-line scene schema version + max-size note so future UI changes don’t silently break saved scenes.
- Confirm (or add) that the rain video size reduction transform is fully recorded in the detached evidence the same way the seam-bake is.

**Verified / well-supported strengths that must be preserved:**
- Ruthless honesty about what a browser tab cannot promise (no SW, no Wake Lock claim, explicit “not an alarm”, visible resume path only).
- Clean public/quarantine boundary (`NocturneSoundsStaticFiles` denies `inbox/`, contract scripts enforce it, excluded_sounds retained with reason + SHA, evidence detached).
- Canonical catalog + embedded fallback stay in lockstep (version 6, same 8 Tonight defaults, same SHA-256s, same status model: core / optional / experimental / quarantined).
- Install path is robust (procedural beds generated locally, optional legacy fetch never blocks, Tonight works without generation).
- Provenance and licensing records are unusually complete for an alpha (AUDIO_PROVENANCE.md + screenshots references + hashes + edits notes).

**Material unresolved questions / residual risk:**
- Does Media Session actually surface usable lock-screen controls on the intended phones, and does the visibility snapshot correctly detect real OS kills vs. mere suspension?
- Are the eight Tonight loops subjectively comfortable for 30–90 min bedside use (the numerical seam work does not answer this)?
- Scene restore after a long background kill + page reload.
- Whether the reduced rain.mp4 retains the intended visual quality under the new size.

---

### Atomic Findings Ledger

**F1**  
- **Decision object:** Platform integration claims (Media Session, visibility resume, install identity)  
- **Severity:** Major (changes how much trust testers can put in “device integration” language)  
- **Confidence:** High (code present; field matrix absent)  
- **Evidence status:** Confirmed finding (code + docs) + plausible concern (untested on devices)  
- **Verification state:** Statically inspected; not executed on target devices  
- **Type:** implementation drift / user experience / evidence gap  
- **Concern:** `registerMediaSession`, `updatePlatformCards`, `inspectPlaybackAfterReturn`, and the Settings platform cards correctly detect and expose capabilities and surface a resume notice. Docs and UI text repeatedly refuse to claim overnight survival or lock-screen reliability. However the package itself contains no recorded results from the matrix it recommends (localhost, plain LAN HTTP, trusted HTTPS, lock, 2/10 min return, ambient vs Radio).  
- **Evidence:** `static/index.html` ~7995–8119, `docs/PLATFORM_BEHAVIOR.md`, `ALPHA_FEEDBACK.md`, CHANGELOG.  
- **Interpretation:** The code implements “honest best-effort”; the packaging still treats the feature as shipping.  
- **Alternative:** It may work well on some phones and be invisible/useless on others; only device data discriminates.  
- **Discriminator:** Run the exact field matrix in PLATFORM_BEHAVIOR.md and attach results (or a “device-matrix-pending” flag) before any future release note softens the caveats.  
- **Error origin:** implementation drift (docs ahead of verification)  
- **Priority:** Before next alpha that markets “better device integration”  
- **Disposition:** Verify + Preserve with caveat  
- **Suggested repair:** Add a short `docs/DEVICE_MATRIX_RESULTS.md` (or section in ALPHA_FEEDBACK) that starts empty and is filled by testers; keep all current “not an alarm / no overnight promise” language.  
- **Preservation constraint:** Do not remove the detection or the visible resume notice; they are correctly designed.

**F2**  
- **Decision object:** Local named scenes  
- **Severity:** Moderate  
- **Confidence:** High  
- **Evidence status:** Confirmed finding  
- **Verification state:** Statically inspected  
- **Type:** design / implementation  
- **Concern:** Scenes are pure `localStorage` (max 12), capture mixer slots + master + mode + Radio texture, normalize on load, and have a clean UI shelf. No schema version, no size/quota feedback beyond a generic failure string, no export. For alpha this is appropriate; a future UI change to slot count or radio fields can silently orphan old scenes.  
- **Evidence:** `static/index.html` ~7697–7787 + scene-shelf CSS.  
- **Discriminator:** Save → alter → apply → reload page; also save under low-quota / private-browsing conditions.  
- **Error origin:** artifact-generated (incomplete for longevity)  
- **Priority:** Next revision  
- **Disposition:** Fix (light)  
- **Suggested repair:** Add `"schema": 1` (or similar) inside each scene object and a one-line note in UI/docs that scenes are browser-local and versioned only loosely. Optionally show a “storage may be full” path more clearly.  
- **Preservation constraint:** Keep them local-only and tiny; do not add server sync.

**F3**  
- **Decision object:** Offline cyclic-crossfade baker + quarantine discipline  
- **Severity:** Minor-to-Moderate (positive) with residual risk on promotion  
- **Confidence:** High  
- **Evidence status:** Confirmed finding  
- **Verification state:** Statically inspected + contract script executed (in incomplete extract)  
- **Type:** safety / correctness / process  
- **Concern / strength:** `bake_seamless_loop.py` refuses public library paths by default, always writes `audition_required` sidecars with hashes/parameters/ffmpeg identity, applies only safety gain, and re-decodes for a codec-aware boundary metric. The one candidate remains in `sounds/inbox/` (server-denied) and is correctly detached to the companion evidence bundle. Contract and release tooling understand the detached vs product split. This is exemplary. Residual risk is only that a future human might promote on the numerical metric alone.  
- **Evidence:** `scripts/bake_seamless_loop.py`, `docs/SEAM_BAKING.md`, RELEASE_MANIFEST detached_evidence, sound_library.json excluded_sounds, main.py StaticFiles denial of inbox.  
- **Disposition:** Preserve + Monitor  
- **Suggested repair:** None required for this package; keep the promotion sequence (human audition on target transducers) as the only gate.

**F4**  
- **Decision object:** Catalog / Tonight / generated-bed contract  
- **Severity:** Minor  
- **Confidence:** High  
- **Evidence status:** Confirmed finding (sync) + expected failure under incomplete extract  
- **Verification state:** Statically inspected + `check_audio_contract.py --source` executed  
- **Type:** correctness / packaging  
- **Concern:** Embedded DEFAULT_SOUND_LIBRARY in `index.html` and `sounds/sound_library.json` are byte-for-byte consistent on version, defaults, sounds, excluded, and SHA-256s. Install generates the 17 procedural beds; Tonight 8 are bundled recorded CC0. Contract correctly treats generated files as optional in source mode. The incomplete extraction I used correctly reported missing library files; the real zip contains them (sizes and hashes match provenance).  
- **Disposition:** Cleared after checking (for the full package)  
- **Preservation constraint:** Keep the dual (file + embedded) sources of truth synchronized via the existing generation/sync scripts.

**F5**  
- **Decision object:** Packaging / evidence split / release hygiene  
- **Severity:** Minor  
- **Confidence:** High  
- **Evidence status:** Confirmed finding  
- **Verification state:** Statically inspected (RELEASE_MANIFEST, make_release.py, .gitignore, detached list)  
- **Type:** process / communication  
- **Concern:** Product ZIP is deliberately slim; quarantine payloads and transform records are detached with explicit sizes/SHAs. Transient verification artifacts are excluded. This matches the CHANGELOG claim and is good hygiene. Slight residual: the rain video size reduction is mentioned but its full transform record lives only in the detached evidence; a tester who never sees the evidence bundle cannot fully reconstruct it.  
- **Disposition:** Accept risk for alpha; optional improve  
- **Suggested repair:** One sentence in README or AUDIO_PROVENANCE pointing to the detached evidence for the video transform (mirroring the seam-bake note).

**F6**  
- **Decision object:** Security / path / Utility surface  
- **Severity:** Minor (for trusted-LAN use)  
- **Confidence:** Medium-High  
- **Evidence status:** Strongly supported  
- **Verification state:** Statically inspected  
- **Type:** safety  
- **Concern:** Utility (Strudel sketchbook) is gated behind settings and disabled by default; slug validation is strict; song write has size limit. Sounds serving denies the entire `inbox/` tree. No obvious path-traversal in the reviewed handlers. Settings PUT requires at least one mode enabled. All good for a local-first alpha. Residual: Utility can write files under `songs/` when enabled; the UI correctly warns “only on a trusted local network.”  
- **Disposition:** Accept risk (with current defaults)  
- **Preservation constraint:** Keep Utility off by default and keep the warning.

**F7 (free-pass observation)**  
- **Decision object:** Overall product voice and anti-overclaim posture  
- **Severity:** N/A (strength)  
- **Evidence status:** Confirmed  
- **Concern:** None. The package repeatedly and consistently refuses medical, alarm, overnight, offline, and “guaranteed lock-screen” claims in README, PLATFORM_BEHAVIOR, ALPHA_FEEDBACK, Settings UI, and code comments. This is rare and valuable; do not let polish or future feature pressure erode it.

---

### Decision and Preservation Map

1. **Release- or decision-blocking issues**  
   None for alpha field distribution. The package may ship as-is for listening + device testing.

2. **Highest-leverage repairs**  
   - Capture real device-matrix results for the new platform features before any future wording softens.  
   - Light scene schema versioning / storage-failure clarity.  
   - (Optional) Explicit pointer to the video transform record in the detached evidence.

3. **Objects to keep, narrow, attribute, verify, or human-confirm**  
   - Keep: all current “not an alarm / no overnight / feature-detected only” language, inbox denial, audition_required discipline, Tonight-8 + optional/experimental shelves, local-only scenes, dual catalog sources.  
   - Verify: Media Session + visibility behavior on at least one modern iOS and one Android under the three launch contexts.  
   - Human-confirm: subjective comfort of the eight Tonight loops and any future seam-baked candidates.  
   - Do not promote the quarantined rain-inside-house seam-bake without that audition.

4. **What appears solid and should be preserved (with evidence trace)**  
   - Honest platform matrix and Settings cards (PLATFORM_BEHAVIOR.md + index.html platform cards).  
   - Catalog contract + check_audio_contract.py + release-audit.mjs + make_release.py evidence split.  
   - Provenance completeness (AUDIO_PROVENANCE.md, credits, hashes, status model).  
   - Install robustness (generated beds never block Tonight).  
   - StaticFiles inbox quarantine + excluded_sounds records.  
   - Local scenes implementation (normalise + cap + pure localStorage).  
   - Media Session registration that fails soft and only claims what the browser exposes.

5. **Open questions that actually matter**  
   - Real-world Media Session / background survival surface rates.  
   - Loop comfort under intended transducers and volumes.  
   - Scene restore after aggressive OS kills.  
   - Whether the rain video quality still feels intentional after the size cut.

6. **Coverage boundary and residual risk**  
   Fully statically inspected: packaging, catalogs, main.py, install, bake tool, key docs, index.html platform/scene code, contracts.  
   Executed: audio-contract script (incomplete extract correctly flagged missing library files).  
   Not executed: full install + generate_noise, browser UI, Media Session on devices, weather/geocode live calls, human audition, overnight runs.  
   Residual high-risk areas: device-dependent platform behavior and subjective audio quality (both correctly treated as field-test items by the package itself).

7. **Free-pass findings and reviewer self-check**  
   Re-examined: every new alpha.10 claim against code and docs; catalog sync between file and embedded fallback; path/inbox denial; scene capture/restore path; Media Session + visibility handlers; bake safety boundaries; RELEASE_MANIFEST detached list; anti-overclaim language density.  
   Nothing new of higher severity surfaced.  
   Self-check: I did not invent device failures; I did not treat “feature present in code” as “verified on phones”; I did not recommend scope expansion (no SW, no Wake Lock, no cloud, no alarm). The review stayed inside the protected intent of a quiet, local-first, honest alpha bedside instrument.

---

**Bottom line for the owner:**  
This is a high-quality, unusually self-aware product pass. Ship the alpha for field testing with the existing feedback card and platform matrix. Treat the new platform features as “correctly implemented and carefully caveated, still awaiting device evidence.” Preserve the quarantine/audition discipline and the anti-overclaim voice at all costs—they are the package’s strongest differentiators.

If you want a Project Edition of Hopeful Skeptic tailored to Nocturne (with its exact vocabulary, phase model, protected “quiet local-first” intent, and characteristic failure modes around audio seams / browser survival claims), say the word and I will compile one.