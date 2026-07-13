# Nocturne field-test card

Use this after automated checks pass. Record observations rather than turning a
single good night into a broad reliability claim.

## A. Quick listening screen

For each of the eight Tonight sounds:

- Listen through headphones and a phone/tablet speaker for at least 3 minutes.
- Mark audible loop boundaries, clicks, sudden events, harsh frequency bands,
  obvious level mismatch, or mounting fatigue.
- Repeat any suspect boundary several times with the sound alone.

Then run one 15-minute mixed scene on the intended bedside speaker. Exercise
master volume, silence/resume, and one timer fade.

## B. Interaction and accessibility

- Keyboard through top modes, Settings, scene controls, mixer controls, and the
  sound picker. Confirm focus remains visible and returns after the picker.
- With one available screen reader, confirm names and states are understandable;
  note any verbosity, missing state, or focus loss.
- At a narrow phone width, check that the scene shelf and mixer do not overflow.

## C. Background / lock cycle

Record the exact URL type: localhost, plain LAN HTTP, trusted HTTPS, or installed
icon.

1. Start a mix and note active levels.
2. Lock the screen for 2 minutes; test any OS play/pause controls.
3. Unlock and return. Record whether audio continued, paused, restarted, or
   required the visible resume action.
4. Repeat after switching to another app for 10 minutes.
5. Repeat with Radio.

Do not infer one browser/device result applies to another. Enter each exact
combination in `docs/DEVICE_TEST_MATRIX.md`.

## D. Longer bedside cycle

Only after A–C are acceptable:

- Keep a normal backup alarm.
- Run Nocturne for the intended sleep interval.
- In the morning, record whether the process/tab survived, whether audio was
  still playing at the expected level, battery/heat behavior, and any wake-up
  or network interruption.

## E. Candidate promotion

A quarantined/seam-baked sound can enter the public catalog only after:

- repeated boundary listening on headphones;
- phone/tablet and bedside-speaker checks;
- a mixed-context check;
- no unexplained transient or source mismatch;
- catalog/provenance update plus source and installed audits.

“Numerical boundary improved” is not a promotion criterion by itself.
