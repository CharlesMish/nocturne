# Radio Drift + Space

Nocturne Radio includes two lightweight effects aimed at the classic “slowed down + reverb” mood without turning the deck into a DAW.

## Controls

- **drift** — maps `0–100%` to `1.00×–0.75×` playback speed.
- **space** — a subtle synthetic room/plate reverb mixed into the radio path.

Both controls are neutral by default and persist in browser `localStorage`:

```text
nocturne:onsen:radio:drift
nocturne:onsen:radio:reverb
```

## Why drift uses playbackRate

The implementation uses `HTMLMediaElement.playbackRate`, which is the lowest-risk browser feature for slowed playback. To get the recognizable slowed-remix sound, Nocturne also sets `preservesPitch`, `mozPreservesPitch`, and `webkitPreservesPitch` to `false` when available. Some browsers may ignore these flags, but the request is explicit and harmless.

## Why space uses a generated impulse

The reverb uses a `ConvolverNode` with a short deterministic impulse generated in JavaScript. This avoids shipping a separate impulse-response WAV and avoids one more network request. At `0%`, the wet gain is silent and the dry path is effectively unchanged.

## Audio graph

```text
audio element → warmth lowpass → dry gain ───────────────┐
                              → convolver → space gain ─┤
                                                         ↓
                                                  radio gain → analyser → master
```

The analyser stays after the effect mix so the VU meter reflects the post-effect signal. The global master and sleep timer still fade the full result.

## Suggested starting presets

- Dreamy but still readable: `warmth 25%`, `drift 30%`, `space 25%`
- Very late-night: `warmth 45%`, `drift 55%`, `space 35%`
- Original deck: `warmth 0%`, `drift 0%`, `space 0%`
