# Nocturne Alpha.13 Hardening Implementation Report

## Revision and scope

- Starting branch: `visual/curated-appearance`
- Starting revision: `f99a7665b8988b9c03d63b0e1512841a29daa703`
- Implementation branch: `release/alpha13-hardening`
- Verified implementation revision: `c71361f9908f8ec1b7b22b4fc0e0bc8f9458287d`
- Comparison range: `f99a7665b8988b9c03d63b0e1512841a29daa703..c71361f9908f8ec1b7b22b4fc0e0bc8f9458287d`
- Starting worktree: clean; no unrelated owner changes were present.
- Release identity remains `0.1.0-alpha.13-dev`. Final release stamping was not performed.

This report and the companion verification/change reports are delivery records
created after the implementation commit. They are deliberately excluded from
the tester-facing product selection and the self-referential evidence archive;
the exact report-delivery commit is recorded in the final handoff.

## Files changed

Implementation revision `c71361f` changes:

- `.gitattributes`, `.gitignore`
- `.github/workflows/deterministic.yml`
- `AGENTS.md`, `CHANGELOG.md`, `README.md`
- `RELEASE_MANIFEST.json`
- `docs/PROCEDURAL_STARTER_SOUNDS.md`, `docs/SOUND_LIBRARY.md`
- `install.py`, `main.py`, `static/index.html`
- `scripts/README.md`, `scripts/browser_smoke.py`
- `scripts/finalize_core_sound_pack.py`, `scripts/generate_noise.py`
- `scripts/installer_smoke.py`, `scripts/make_release.py`
- `scripts/path_safety.py`, `scripts/path_safety.mjs`, `scripts/path_safety_smoke.py`
- `scripts/release-audit.mjs`, `scripts/release_builder_smoke.py`
- `scripts/rename_freesound_downloads.py`, `scripts/runtime_smoke.py`

The delivery-only follow-up adds `IMPLEMENTATION_REPORT.md`,
`VERIFICATION_REPORT.md`, and `CHANGE_SUMMARY.md`.

## Implementation decisions

### A — constrained-hardware installer

The installer and generator now default to 60 seconds per each of 17 optional
procedural files. `--noise-seconds`, `--seconds`, and `--skip-noise` remain
available; 180 seconds is still an accepted explicit override.

Procedural generation is isolated as an optional fail-soft step. Its outcome is
tracked as exactly `generated`, `skipped by user`, or `failed`. A generation
failure leaves successful environment/dependency setup intact, explains that
the bundled curated Core Sound Pack remains usable, prints the platform-correct
retry command, and still completes installation. Required dependency failures
remain fatal. The synthesis implementation was not redesigned.

### B — Utility request and metadata validation

All three write routes use one JSON-object body helper. Malformed JSON and valid
non-object JSON return HTTP 400 before route code calls object methods.

Exact limits:

- song code: existing 256 KiB UTF-8 limit;
- song metadata: 32 KiB after compact, sorted, canonical UTF-8 JSON encoding;
- song metadata depth: at most four JSON container levels;
- metadata must be an object containing JSON-compatible, finite values.

`createdAt` and `updatedAt` are server-managed. Create and update prepare and
validate both files before touching the final song directory.

Song-write consistency guarantee: both complete files are written and `fsync`ed
in a same-filesystem staging directory. An existing complete song directory is
moved to a uniquely named backup, the complete staged directory is moved into
place, and an injected replacement failure rolls the previous directory back.
Known temporary directories are cleaned after success and handled failure.
This is a staged pair replacement with rollback, not a claim of a truly atomic
two-file transaction. A process or machine crash in the narrow interval between
directory renames can retain the full prior pair under a hidden backup name and
may require recovery; it should not expose a deliberately half-written pair.

### C — location semantics

Strict API validation rejects booleans, non-finite coordinates, and values
outside latitude/longitude bounds. Partial updates now use the current saved
location as the explicit fallback, so omitted label, coordinates, timezone, and
temperature-unit fields are preserved. Load-time repair still falls back safely.
The weather cache is cleared only when the resulting location actually changes.

### D — path containment and quarantine

Small Python and JavaScript helpers reject empty, absolute, Windows-absolute,
separator-bearing basename values, dot segments, mixed slash traversal, and
resolved candidates outside their declared root. These guards are applied
before finalizer/renamer reads or writes, release-builder hashing or packaging,
and release-audit inspection. Valid detached-evidence selection remains driven
by canonical catalog metadata.

The public `sounds/` mount checks the first normalized path component with
`casefold()` before static filesystem resolution. Exact `inbox`, `Inbox`,
`INBOX`, and `iNbOx` variants, plus encoded/traversal aliases, take the custom
403 denial path; unrelated names such as `inbox-mixes` remain available.

### E — sleep timer

The wall-clock `endAt` remains authoritative. With an active audio context, the
timer cancels stale automation, holds the current base master level until the
fade boundary, and schedules one `linearRampToValueAtTime(0, deadline)`. A timer
shorter than the fade begins immediately. The 500 ms interval now updates only
status/reconciliation, not audible gain.

Cancellation, replacement, completion, silence, and manual master changes share
the same automation cleanup/rescheduling path. Visible `visibilitychange`,
`pageshow`, the ordinary tick, and a foreground deadline timeout reconcile the
wall clock. Completion pauses ambient and Radio playback and restores the base
gain for the next resume. This improves foreground and return behavior without
claiming lock-screen, mobile-background, or overnight survival.

### F — release hygiene and CI

`.gitattributes` now fixes BAT files to CRLF and shell/command/Python/JavaScript
sources to LF. Existing launchers already matched the intended checkout bytes;
the release smoke now proves both source and ZIP member endings, plus executable
modes. This is deterministic packaging policy, not a claim that LF batch files
were previously proven broken.

The release audit prints to stdout by default. `--report PATH` is explicit and
creates parent directories; `--root PATH` supports extracted-package checks.
Two-run regression coverage compares all relevant results while allowing the
expected timestamp to differ and proves no root `release-audit.json` appears.

GitHub Actions now runs the deterministic suite on Python 3.10 and 3.12 with
Node 22. Runtime dependencies use `requirements.txt` plus the existing
known-good `constraints.txt`. A manual browser job installs Playwright/Chromium
as QA-only tooling and tests both profiles; it is not a runtime dependency.

### G — documentation

The architecture and `/api/sounds` descriptions now distinguish bundled
`sounds/library/`, optional install-generated root WAVs, personal Radio, and
the non-public inbox. Installer, audit, CI, browser, and 60-second generation
behavior are documented. The alpha.13 development changelog was updated without
changing build identity.

## Deferred findings and limitations

- No authentication/account, Host-header/DNS-rebinding redesign, service
  worker, database, framework, build system, settings cache, weather concurrency
  redesign, synthesis streaming rewrite, or `/api/sounds` removal was added.
- FastAPI already uses lifespan in this starting tree; no lifecycle migration
  was needed in this pass.
- CI is committed but cannot produce hosted evidence until the branch is pushed
  or the workflow is dispatched.
- The clean dependency install was exercised locally on Python 3.14/macOS arm64;
  the declared 3.10/3.12 matrix still needs its first hosted run.
- Visual review found the Nocturne Pi video-disabled hero can appear as a plain
  black panel because the global clean-video CSS hides the painted fallback and
  the disabled video never receives the reveal class. Fixing that presentation
  would change visual behavior and was deferred from this frozen hardening pass.
- Real Windows launcher/path behavior, Raspberry Pi 3 memory/performance,
  screen-reader use, phone lock/background behavior, listening comfort, and an
  overnight session remain field-test pending.

Recommended owner stamping command after review (not executed):

```bash
.venv/bin/python scripts/stamp_build.py \
  --version 0.1.0-alpha.13 \
  --revision <final-release-revision>
```
