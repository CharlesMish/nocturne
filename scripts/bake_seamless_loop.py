#!/usr/bin/env python3
"""Bake a recording into a cyclic crossfaded loop, with an audit sidecar.

This is an *offline preparation tool*, not an automatic quality verdict. It joins
an overlap between the source tail and head, records the exact transform, and
marks every output ``audition_required``. A rendered file remains a candidate
until a human listens on the intended devices.

Requires ffmpeg/ffprobe and NumPy (already a Nocturne runtime dependency).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_LIBRARY = (ROOT / "sounds" / "library").resolve()
SUPPORTED = {".wav", ".flac", ".ogg", ".opus", ".webm", ".m4a", ".aac", ".mp3"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def probe(path: Path) -> dict[str, Any]:
    completed = run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,channels,sample_rate,duration:format=duration,bit_rate,size",
            "-of", "json", str(path),
        ],
        capture=True,
    )
    data = json.loads(completed.stdout)
    streams = data.get("streams") or []
    if not streams:
        raise ValueError(f"No audio stream found in {path}")
    stream = streams[0]
    stream["channels"] = int(stream["channels"])
    stream["sample_rate"] = int(stream["sample_rate"])
    return data


def ffmpeg_version() -> str:
    completed = run(["ffmpeg", "-version"], capture=True)
    return completed.stdout.splitlines()[0].strip()


def within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory)
        return True
    except ValueError:
        return False


def boundary_metrics(samples: np.ndarray) -> dict[str, float]:
    # Compare the wrap jump with ordinary adjacent-sample movement. This is a
    # screening metric only: it cannot detect a musically obvious transition.
    if samples.shape[0] < 3:
        return {"boundary_jump_rms": 0.0, "typical_step_rms": 0.0, "jump_ratio": 0.0}
    jump = samples[0] - samples[-1]
    adjacent = np.diff(samples, axis=0)
    typical = float(np.sqrt(np.mean(np.square(adjacent, dtype=np.float64))))
    boundary = float(np.sqrt(np.mean(np.square(jump, dtype=np.float64))))
    return {
        "boundary_jump_rms": boundary,
        "typical_step_rms": typical,
        "jump_ratio": boundary / typical if typical > 0 else 0.0,
    }


def encode_command(raw_path: Path, output: Path, sample_rate: int, channels: int) -> list[str]:
    base = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "f32le", "-ar", str(sample_rate), "-ac", str(channels), "-i", str(raw_path),
        "-map_metadata", "-1",
    ]
    suffix = output.suffix.lower()
    if suffix == ".wav":
        return base + ["-c:a", "pcm_s16le", str(output)]
    if suffix == ".flac":
        return base + ["-c:a", "flac", "-compression_level", "8", str(output)]
    if suffix in {".opus", ".ogg", ".webm"}:
        return base + ["-c:a", "libopus", "-b:a", "160k", "-vbr", "on", str(output)]
    if suffix == ".m4a":
        return base + ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)]
    if suffix == ".aac":
        return base + ["-c:a", "aac", "-b:a", "192k", "-f", "adts", str(output)]
    if suffix == ".mp3":
        return base + ["-c:a", "libmp3lame", "-q:a", "2", str(output)]
    raise ValueError(f"Unsupported output extension: {suffix}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="source recording")
    parser.add_argument("output", type=Path, help="baked output (.wav/.flac/.ogg/.opus/.webm/.m4a/.aac/.mp3)")
    parser.add_argument("--crossfade-seconds", type=float, default=6.0, help="cyclic head/tail overlap (default: 6)")
    parser.add_argument("--curve", choices=("equal-power", "linear"), default="equal-power")
    parser.add_argument("--max-decoded-mb", type=float, default=512.0, help="refuse larger decoded PCM buffers")
    parser.add_argument("--allow-public-path", action="store_true", help="allow writing directly under sounds/library (normally refused)")
    parser.add_argument("--sidecar", type=Path, help="JSON sidecar path (default: OUTPUT.loop.json)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.input.expanduser().resolve()
    output = args.output.expanduser().resolve()
    sidecar = (args.sidecar.expanduser().resolve() if args.sidecar else Path(str(output) + ".loop.json"))

    for executable in ("ffmpeg", "ffprobe"):
        if not shutil.which(executable):
            raise SystemExit(f"Missing required executable: {executable}")
    if not source.is_file():
        raise SystemExit(f"Input does not exist: {source}")
    if output.suffix.lower() not in SUPPORTED:
        raise SystemExit(f"Unsupported output extension {output.suffix}; choose one of {sorted(SUPPORTED)}")
    if source == output:
        raise SystemExit("Refusing to overwrite the source recording")
    if sidecar in {source, output}:
        raise SystemExit("Sidecar path must be different from the source and output audio paths")
    if within(output, PUBLIC_LIBRARY) and not args.allow_public_path:
        raise SystemExit("Refusing to publish directly into sounds/library; bake into sounds/inbox and audition first (or pass --allow-public-path explicitly)")
    if args.crossfade_seconds <= 0:
        raise SystemExit("--crossfade-seconds must be positive")

    metadata = probe(source)
    stream = metadata["streams"][0]
    sample_rate = int(stream["sample_rate"])
    channels = int(stream["channels"])
    duration = float(stream.get("duration") or metadata.get("format", {}).get("duration") or 0)
    if duration <= args.crossfade_seconds * 2:
        raise SystemExit("Crossfade must be shorter than half the decoded recording")
    estimated_bytes = duration * sample_rate * channels * 4
    if estimated_bytes > args.max_decoded_mb * 1024 * 1024:
        raise SystemExit(
            f"Decoded PCM would be about {estimated_bytes / 1024 / 1024:.1f} MiB; "
            f"raise --max-decoded-mb deliberately or pre-trim the source"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nocturne-loop-") as temp:
        tempdir = Path(temp)
        decoded = tempdir / "decoded.f32"
        baked_raw = tempdir / "baked.f32"
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
            "-map", "0:a:0", "-f", "f32le", "-acodec", "pcm_f32le", "-ar", str(sample_rate),
            "-ac", str(channels), str(decoded),
        ])
        decoded_limit = args.max_decoded_mb * 1024 * 1024
        if decoded.stat().st_size > decoded_limit:
            raise SystemExit(
                f"Decoded PCM is {decoded.stat().st_size / 1024 / 1024:.1f} MiB; "
                f"raise --max-decoded-mb deliberately or pre-trim the source"
            )
        samples = np.fromfile(decoded, dtype="<f4")
        if samples.size % channels:
            raise RuntimeError("Decoded sample count is not divisible by channel count")
        samples = samples.reshape((-1, channels))
        overlap = int(round(args.crossfade_seconds * sample_rate))
        if samples.shape[0] <= overlap * 2:
            raise SystemExit("Decoded recording is too short for this crossfade")

        # Rotate the source so the overlap lives at the loop boundary:
        # x[L … N-L] then crossfade x[N-L … N] into x[0 … L]. When the
        # result wraps, head[L-1] naturally continues into head[L].
        position = np.linspace(0.0, 1.0, overlap, dtype=np.float64)[:, None]
        if args.curve == "equal-power":
            fade_out = np.cos(position * math.pi / 2.0)
            fade_in = np.sin(position * math.pi / 2.0)
        else:
            fade_out = 1.0 - position
            fade_in = position
        bridge = samples[-overlap:].astype(np.float64) * fade_out + samples[:overlap].astype(np.float64) * fade_in
        middle = samples[overlap:-overlap].astype(np.float64)
        baked = np.concatenate((middle, bridge), axis=0)

        peak_before = float(np.max(np.abs(baked))) if baked.size else 0.0
        safety_gain = min(1.0, 0.999 / peak_before) if peak_before else 1.0
        baked *= safety_gain
        baked = baked.astype("<f4")
        baked.tofile(baked_raw)
        source_metrics = boundary_metrics(samples)
        pcm_metrics = boundary_metrics(baked)
        run(encode_command(baked_raw, output, sample_rate, channels))

    # Re-decode the actual deliverable for a codec-aware numerical screen.
    with tempfile.TemporaryDirectory(prefix="nocturne-loop-check-") as temp:
        decoded_output = Path(temp) / "output.f32"
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(output),
            "-map", "0:a:0", "-f", "f32le", "-acodec", "pcm_f32le", "-ar", str(sample_rate),
            "-ac", str(channels), str(decoded_output),
        ])
        encoded = np.fromfile(decoded_output, dtype="<f4").reshape((-1, channels))
        encoded_metrics = boundary_metrics(encoded)

    output_probe = probe(output)
    record = {
        "schema": "nocturne.loop-bake.v1",
        "status": "audition_required",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "path": str(source.relative_to(ROOT)) if within(source, ROOT) else str(source),
            "sha256": sha256(source),
            "size_bytes": source.stat().st_size,
            "probe": metadata,
        },
        "output": {
            "path": str(output.relative_to(ROOT)) if within(output, ROOT) else str(output),
            "sha256": sha256(output),
            "size_bytes": output.stat().st_size,
            "probe": output_probe,
        },
        "transform": {
            "method": "offline cyclic head-tail crossfade",
            "curve": args.curve,
            "crossfade_seconds": args.crossfade_seconds,
            "overlap_samples_per_channel": int(round(args.crossfade_seconds * sample_rate)),
            "sample_rate_hz": sample_rate,
            "channels": channels,
            "safety_gain": safety_gain,
            "ffmpeg": ffmpeg_version(),
        },
        "numerical_screen": {
            "source_boundary": source_metrics,
            "baked_pcm_boundary": pcm_metrics,
            "encoded_output_boundary": encoded_metrics,
            "interpretation": "A lower wrap-jump ratio is encouraging but does not prove an inaudible or comfortable loop.",
        },
        "claim_boundary": "Nocturne has rendered a traceable repair candidate. Human audition on target devices is still required before catalog promotion.",
    }
    sidecar.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"Command failed: {' '.join(exc.cmd)}", file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        raise SystemExit(exc.returncode or 1)
