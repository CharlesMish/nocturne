#!/usr/bin/env python3
"""Deterministic installer regressions without creating a real virtualenv."""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import install  # noqa: E402
from scripts import generate_noise  # noqa: E402


def expect(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def run_fixture(argv: list[str], *, fail_generator: bool = False, fail_dependency: bool = False):
    calls: list[list[str]] = []
    output = io.StringIO()
    with tempfile.TemporaryDirectory(prefix="nocturne-installer-smoke-") as temp:
        root = Path(temp)
        venv = root / ".venv"
        venv.mkdir()
        python = venv / "bin" / "python"

        def fake_run(cmd, *, env=None):
            rendered = [str(part) for part in cmd]
            calls.append(rendered)
            if fail_dependency and "pip" in rendered:
                raise subprocess.CalledProcessError(17, rendered)
            if fail_generator and any(part.endswith("generate_noise.py") for part in rendered):
                raise subprocess.CalledProcessError(23, rendered)

        with (
            patch.object(install, "ROOT", root),
            patch.object(install, "VENV", venv),
            patch.object(install, "CONSTRAINTS", root / "constraints.txt"),
            patch.object(install, "ensure_venv", return_value=python),
            patch.object(install, "run", side_effect=fake_run),
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(output),
        ):
            try:
                result = install.main(argv)
                error = None
            except BaseException as exc:  # argparse and required subprocess failures are evidence here.
                result = None
                error = exc
    return result, error, calls, output.getvalue()


def generation_seconds(calls: list[list[str]]) -> str | None:
    for call in calls:
        if any(part.endswith("generate_noise.py") for part in call):
            return call[call.index("--seconds") + 1]
    return None


def main() -> int:
    checks: list[str] = []
    expect(install.DEFAULT_NOISE_SECONDS == 60, "installer default duration is 60 seconds", checks)
    expect(generate_noise.DEFAULT_SECONDS == 60, "generator default duration is 60 seconds", checks)
    expect(generate_noise.parse_args([]).seconds == 60, "generator parser resolves the default duration to 60 seconds", checks)
    expect(generate_noise.parse_args(["--seconds", "180"]).seconds == 180, "generator accepts an explicit 180-second override", checks)
    for invalid in ("0", "-1", "not-a-number"):
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                generate_noise.parse_args(["--seconds", invalid])
            except SystemExit as exc:
                generator_error = exc
            else:
                generator_error = None
        expect(
            isinstance(generator_error, SystemExit) and generator_error.code == 2,
            f"invalid generator duration is rejected: {invalid}",
            checks,
        )

    result, error, calls, output = run_fixture(["--skip-deps", "--no-fetch-media"])
    expect(error is None and result == 0 and generation_seconds(calls) == "60", "ordinary install resolves procedural generation to 60 seconds", checks)
    expect("Procedural beds: generated (60 seconds per file)." in output, "generated outcome is reported truthfully", checks)

    result, error, calls, output = run_fixture(["--skip-deps", "--noise-seconds", "180", "--no-fetch-media"])
    expect(error is None and result == 0 and generation_seconds(calls) == "180", "explicit 180-second installer override remains accepted", checks)

    for invalid in ("0", "-1", "not-a-number"):
        _, error, _, output = run_fixture(["--skip-deps", "--noise-seconds", invalid, "--no-fetch-media"])
        expect(isinstance(error, SystemExit) and error.code == 2, f"invalid installer duration is rejected: {invalid}", checks)

    result, error, calls, output = run_fixture(["--skip-deps", "--skip-noise", "--no-fetch-media"])
    expect(error is None and result == 0 and generation_seconds(calls) is None, "--skip-noise completes without invoking the generator", checks)
    expect("Procedural beds: skipped by user" in output and "Procedural beds: generated" not in output, "skip outcome never claims generation", checks)

    result, error, calls, output = run_fixture(
        ["--skip-deps", "--noise-seconds", "60", "--no-fetch-media"],
        fail_generator=True,
    )
    expect(error is None and result == 0, "simulated optional generator failure still completes installation", checks)
    expect("bundled curated Core Sound Pack" in output, "generator failure explains the bundled fallback", checks)
    expect(".venv/bin/python scripts/generate_noise.py --seconds 60" in output, "generator failure prints the exact retry command", checks)
    expect("Procedural beds: generation failed" in output and "Procedural beds: generated" not in output, "failed generation is reported without a false success", checks)

    result, error, calls, output = run_fixture(["--skip-noise", "--no-fetch-media"], fail_dependency=True)
    expect(isinstance(error, subprocess.CalledProcessError) and error.returncode == 17, "simulated required dependency failure still fails installation", checks)
    expect(generation_seconds(calls) is None and "Nocturne is installed" not in output, "required dependency failure does not reach a false install success", checks)

    report = {"schema": "nocturne.installer-smoke.v1", "overall": "PASS", "checks": checks}
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"schema": "nocturne.installer-smoke.v1", "overall": "FAIL", "error": str(exc)}, indent=2))
        raise
