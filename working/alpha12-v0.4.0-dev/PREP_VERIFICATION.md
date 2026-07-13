# Nocturne alpha.12-dev preparation verification

Build: `v0.1.0-alpha.12-dev · 2026-07-12 · codex-profile-split-v0.4.0-dev`

Purpose: verify the Codex-ready profile/evidence scaffold before handoff. This
is not a public release certification or target-hardware result.

## Source snapshot

Observed PASS:

- generated sound/build fallback synchronization;
- source audio contract;
- source release audit with 0 errors and 0 warnings;
- FastAPI runtime smoke;
- shared-profile smoke for `nocturne` and `nocturne-pi`;
- Chromium smoke for Nocturne;
- Chromium smoke for Nocturne Pi, including no `/rain.mp4` request;
- Python compilation;
- Node syntax for release audit and inline application JavaScript;
- local support-report generation without upload.

## Preliminary dual release exercise

`scripts/make_dual_release.py` produced both products and one evidence archive
from the same source identity.

Preliminary artifacts used only for package-path verification:

| Artifact | Size | SHA-256 |
|---|---:|---|
| `nocturne-v0.4.0-dev.zip` | 11,484,643 bytes | `2a21c9ad2c92b8a01cbf422abb6adc9ae76a154f86e73d0828f86e3f9473f0b9` |
| `nocturne-pi-v0.4.0-dev.zip` | 8,568,604 bytes | `b9ec5e44d4e241afac2289619d79ecb29e385b9b2d081ba8c2dd9bba1088cd2f` |
| `nocturne-evidence-v0.4.0-dev.zip` | 21,445,764 bytes | `570a7eac152ff8ba8d96177433113446c563c93fab44302c1329879b91e24008` |

Both product ZIPs were freshly extracted. Each extracted package passed:

- generated fallback synchronization;
- source audio contract;
- release audit;
- runtime smoke;
- profile smoke;
- profile-appropriate Chromium smoke.

The Pi package omitted `static/rain.mp4`; its browser smoke still passed and did
not request that path.

## Not executed or established

- clean dependency installation from an empty machine;
- regeneration and installed-mode audit of all 17 procedural WAVs in this new
  snapshot;
- Raspberry Pi 3, 4, or 5 performance;
- server-only versus local-display measurements;
- physical phone lock/background behavior;
- screen-reader quality;
- battery, heat, or long-run memory behavior;
- human listening, loop comfort, or overnight use;
- Git history/branch operations on the owner's actual repository.

Codex must rerun checks after edits and must not carry these results forward as
proof of changed artifacts.
