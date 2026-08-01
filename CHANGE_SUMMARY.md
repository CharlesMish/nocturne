# Nocturne Alpha.13 Hardening Change Summary

## Fixed

- Lowered optional procedural generation to 60 seconds by default, retained
  explicit longer runs, and made only generator failure nonfatal and truthful.
- Rejected malformed/non-object Utility requests, bounded metadata to 32 KiB
  and four container levels, and staged complete song pairs with rollback.
- Rejected non-finite coordinates and preserved omitted location fields.
- Contained CSV/catalog/release paths and denied every tested inbox casing and
  encoded/traversal alias through the custom quarantine guard.
- Scheduled timer fading with one Web Audio ramp while keeping wall-clock
  expiry and safe cancel/return/master-volume reconciliation.
- Restored the intended static rain hero in Nocturne Pi without requesting the
  disabled MP4 or adding motion.
- Made release audit non-mutating by default, codified launcher endings, added
  focused smokes and Python 3.10/3.12 CI, and corrected release documentation.

## Tested

- Source, installed, and freshly extracted source audio/release contracts.
- 85 runtime, 13 profile, 21 installer, 24 path, and 27 release-builder checks.
- Both browser profiles in the working tree and extracted RC, with no page or
  console errors, deterministic sleep-timer timing coverage, and an explicit Pi
  static-background assertion.
- Real 17-file default generation on Apple Silicon: 4.10 seconds, 80.08 MiB
  output, about 341.45 MiB maximum RSS.
- Clean constrained dependency installation on macOS arm64/Python 3.14.
- Product/evidence ZIP CRC, SHA-256, manifest, permissions, and line endings.

## Still field-test pending

- Windows installer/launchers and case-insensitive filesystem behavior.
- Raspberry Pi 3 installation, local-display performance, and memory margin.
- Real screen-reader use, phone lock/background return, listening comfort,
  loop audition, and overnight behavior.
- The first hosted Python 3.10/3.12 CI matrix run after an authorized push.

## Deferred

- Authentication/accounts and broad Host-header/DNS-rebinding changes.
- Service worker/offline mode, database, framework/build migration, and
  frontend modularization.
- Streaming procedural synthesis and other algorithm redesign.
- Settings/weather concurrency redesign, `/api/sounds` removal, and final
  `0.1.0-alpha.13` stamping.
