# Offline seam baking

`scripts/bake_seamless_loop.py` turns a recording into a traceable cyclic
crossfade candidate. It is a preparation tool, not an automatic curation gate.

## Example

```bash
python scripts/bake_seamless_loop.py \
  /path/to/source-recording.mp3 \
  sounds/inbox/seam-baked/my-loop-candidate.m4a \
  --crossfade-seconds 6 \
  --curve equal-power
```

The companion evidence archive contains the worked rain source, output, and
sidecar under `current/detached/sounds/inbox/`. They are intentionally absent
from the slim tester ZIP; copy them into matching local paths only when auditing
or re-rendering that example.

The tool:

1. probes and decodes the first audio stream with FFmpeg;
2. keeps the uninterrupted middle of the source;
3. crossfades the source tail into its head at the new loop boundary;
4. applies only a safety gain when the rendered peak would exceed 0.999;
5. encodes the requested format;
6. re-decodes the actual output for a codec-aware boundary screen; and
7. writes `OUTPUT.loop.json` with hashes, file sizes, probe data, transform
   parameters, FFmpeg identity, and claim boundaries.

## Safety boundaries

- Output under `sounds/library/` is refused unless
  `--allow-public-path` is supplied explicitly.
- The default decoded-memory ceiling is 512 MiB; pre-trim very long inputs or
  raise the limit deliberately.
- The sidecar status is always `audition_required`.
- A lower boundary-jump ratio detects only one numerical symptom. It cannot
  determine whether changing ambience, rhythm, stereo image, or an encoded
  transient makes the loop obvious.
- Preserve the original source and its license/provenance record.

## Promotion sequence

Keep the render under `sounds/inbox/`, which Nocturne refuses to serve. Then:

1. listen across the boundary repeatedly on headphones;
2. test phone/tablet and intended bedside speakers;
3. test alone and inside a normal mix;
4. update `sounds/sound_library.json` only after approval;
5. run synchronization, source audit, runtime smoke, and installed audit; and
6. retain the transform sidecar beside the provenance evidence.

The alpha.10 evidence bundle includes one repaired rain candidate as a worked
example. It remains quarantined pending the human listening cycle.
