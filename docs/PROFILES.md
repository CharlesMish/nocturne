# Nocturne and Nocturne Pi

Nocturne uses one source tree and two presentation profiles.

## Nocturne

The full atmospheric profile. It enables the rain video, gentle ambient motion,
parallax, normal asset preloading, and curated appearance controls. Settings can
coordinate the surrounding color mood, typography, and lighting density without
changing the rain media or the saved sound mix. These browser-local preferences
apply across Onsen, Sky, and Radio. It is intended for Raspberry Pi 4 or newer,
ordinary computers, and cases where the Pi only serves the app while a phone,
tablet, or laptop renders it.

## Nocturne Pi

The lower-resource profile. It uses a still rain image, disables continuous
decorative motion and parallax, removes expensive backdrop blur, and avoids
requesting the full rain video. It also keeps the compact mixer and omits the
full profile's appearance controls. It is designed for Raspberry Pi 3-class,
low-memory systems, older browsers, and local-display or kiosk use.

That is a design target, not a claim that every Pi 3 configuration has been
tested. Hardware reports are welcome.

## Deployment mode is separate

Either edition can be used in either way:

- **Server only:** the host runs Nocturne; another device displays it.
- **Local display:** the host runs Nocturne and a browser on an attached screen.

Local display is normally the more demanding case. These are diagnostic and
deployment descriptions, not separate products.

## Launching a profile from source

The source tree defaults to `nocturne`, recorded in `nocturne_profile.json`.
Override it without editing files:

```bash
python run_nocturne.py --profile nocturne
python run_nocturne.py --profile nocturne-pi
```

The active definition is exposed locally at `/api/profile` and included in
`/api/version`.
