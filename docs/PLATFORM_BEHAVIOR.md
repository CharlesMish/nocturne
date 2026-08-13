# Browser and device behavior

**Field evidence status: pending.** The integration code is feature-detected and
caveated, but no phone/browser combination is treated as proven until recorded
in `docs/DEVICE_TEST_MATRIX.md`.

Nocturne is a local web application. The same code can receive different browser
capabilities depending on how it is opened.

## Context matrix

| Launch path | Core mixer | Media / install APIs | Practical note |
|---|---|---|---|
| `http://127.0.0.1:8000` or `http://localhost:8000` | Expected | Localhost is generally treated as potentially trustworthy | Best first test on the server device |
| `http://DEVICE-IP:8000` or `http://pi.local:8000` | Expected | Some secure-context-only APIs may be withheld | Honest baseline for simple trusted-LAN playback |
| Trusted `https://...` | Expected | Best chance of exposing secure-context APIs | Certificate must be trusted by the listening device |
| Installed icon / standalone display | Browser-dependent | Manifest identity may improve presentation | Does not guarantee background survival |

Nocturne shows its current feature detections in **Settings → Device
integration**.

## Trusted-network boundary

Nocturne has no login or per-user permissions. Anyone who can reach the server
can change settings and, when Utility is enabled, create, edit, or delete local
sketches. Bind it to a LAN address only on a network you trust.

## What this alpha does

- Supplies a web-app manifest and local 192/512/maskable icons.
- Registers Media Session play, pause, stop, previous, and next handlers only
  when the browser exposes them.
- Updates title/artwork metadata for the ambient mix or current Radio track.
- Records whether audio appeared active before the page became hidden.
- On return, shows a visible resume message when playback appears interrupted or
  the audio context is suspended.
- Accepts optional TLS certificate and private-key paths in `run_nocturne.py`.

## What it deliberately does not claim

- No service worker or offline application cache is shipped yet.
- No Wake Lock request is made.
- Visibility handling cannot stop a phone OS from suspending or terminating the
  browser process.
- Media Session support does not prove lock-screen controls will appear or that
  audio will continue overnight.
- Nocturne is not a dependable browser alarm and should not be the only alarm.

## Optional HTTPS

```bash
./.venv/bin/python run_nocturne.py --host 0.0.0.0 \
  --ssl-certfile /path/to/trusted-cert.pem \
  --ssl-keyfile /path/to/private-key.pem
```

The certificate must be trusted on every client device. Nocturne does not
silently create or install a local certificate authority because that is a
security-sensitive, platform-specific operation.

## Required field matrix

At minimum, compare:

- one desktop localhost session;
- one phone over plain LAN HTTP;
- one phone over trusted HTTPS when available;
- screen lock, 2-minute return, 10-minute app switch, and a longer bedside run;
- ambient mix and Radio separately.

Record actual results in `docs/DEVICE_TEST_MATRIX.md` and include the relevant
row with feedback. Do not convert API availability into a reliability claim.

## Reference material

- MDN, Secure contexts: `https://developer.mozilla.org/docs/Web/Security/Secure_Contexts`
- MDN, Media Session API: `https://developer.mozilla.org/docs/Web/API/Media_Session_API`
- MDN, Page Visibility API: `https://developer.mozilla.org/docs/Web/API/Page_Visibility_API`
- MDN, Web app manifests: `https://developer.mozilla.org/docs/Web/Progressive_web_apps/Manifest`
