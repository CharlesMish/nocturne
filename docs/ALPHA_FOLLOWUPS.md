# Alpha follow-up notes

This is a short maintenance queue, not release evidence. “Fixed” items are
covered by repository checks; “field” items still require the named real device
or interaction and must not be presented as verified.

| ID | Priority | Status | Flag and evidence | Quick follow-up |
|---|---|---|---|---|
| UI-01 | medium | fixed | Muted helper copy and compact actions fell below the otherwise calm visual hierarchy. Browser smoke now measures representative text floors. | Recheck these floors whenever the full-profile type scale changes. |
| QA-01 | medium | fixed | Browser smoke required a separately discovered system browser and missed the 340 px breakpoint plus enabled Utility/Dashboard states. | Keep Playwright Chromium QA-only; run both profiles before release captures. |
| CSS-01 | low | open | The large inline base stylesheet and later polish layer create specificity debt, although current brace, compile, and browser checks pass. | Consolidate only during a separately scoped CSS maintenance project; avoid a release-pass refactor. |
| DASH-01 | low | field | Dashboard is correctly lazy-loaded and unloaded, but its canvas cost has not been measured on a Raspberry Pi. | Profile the enabled Dashboard on the intended Pi/browser and record thermals, frame stability, and unload behavior. |
| PLAT-01 | high | field | Windows/macOS launchers, Raspberry Pi, screen reader, lock-screen/app-switch, listening comfort, and overnight behavior remain unverified on real targets. | Record exact device, OS, browser, launch context, and result in the existing device/hardware reports. |

Utility remains disabled and route-hidden by default. Its enabled browser smoke
uses local fixtures and does not exercise the explicit outbound Strudel link.
