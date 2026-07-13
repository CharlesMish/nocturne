# Nocturne v0.1.0-alpha.12 release evidence

Tag: `v0.1.0-alpha.12`

Product commit: `a650b8d4fc14e643f7a665c060e6c49254c6ceb1`

Build identity: `v0.1.0-alpha.12 · 2026-07-12 · v0.1.0-alpha.12`

This is the first public dual-profile field-test alpha. It contains Nocturne
and Nocturne Pi products built from the same tagged source. The Pi product
omits the rain video and resolves the still/reduced-motion profile.

## Evidence established

- Required source verification suite passed on macOS.
- Source and packaged Chromium smokes passed for both profiles.
- All three initial archives passed checksum and ZIP CRC checks.
- Both product manifests matched every extracted file's size and SHA-256.
- Both ZIPs preserved executable macOS/Linux installer modes.
- A fresh ordinary Nocturne extraction completed an accelerated macOS install
  smoke and served the expected build/profile endpoints.
- Repeated builds after this evidence snapshot are required to match before
  the GitHub prerelease is published.

## Still pending

- Windows installation and playback;
- Raspberry Pi 3, 4, or 5 hardware performance;
- real screen-reader use;
- phone lock-screen/background behavior;
- listening comfort, loop audition, battery/heat, and overnight behavior.

The macOS install smoke used one-second generated beds to exercise all 17
generator paths without representing a listening or full-duration media test.
