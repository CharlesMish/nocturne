#!/usr/bin/env python3
"""Small cross-platform path guards for Nocturne maintenance scripts."""
from __future__ import annotations

from pathlib import Path, PureWindowsPath


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError(f"{label} must be a non-empty path string")
    return value


def require_basename(value: object, label: str = "filename") -> str:
    raw = _text(value, label)
    if raw in {".", ".."} or "/" in raw or "\\" in raw:
        raise ValueError(f"{label} must be a basename without path separators: {raw!r}")
    if Path(raw).is_absolute() or PureWindowsPath(raw).is_absolute():
        raise ValueError(f"{label} must not be absolute: {raw!r}")
    return raw


def ensure_within(root: Path, candidate: Path, label: str = "path") -> Path:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes {resolved_root}: {candidate}") from exc
    return resolved_candidate


def resolve_relative(root: Path, value: object, label: str = "path") -> Path:
    raw = _text(value, label)
    if "\\" in raw:
        raise ValueError(f"{label} must use forward slashes: {raw!r}")
    if Path(raw).is_absolute() or PureWindowsPath(raw).is_absolute():
        raise ValueError(f"{label} must be relative: {raw!r}")
    if any(part in {"", ".", ".."} for part in raw.split("/")):
        raise ValueError(f"{label} contains an unsafe path segment: {raw!r}")
    return ensure_within(root, root / raw, label)


def resolve_catalog_path(repository: Path, value: object, declared_root: Path, label: str) -> Path:
    candidate = resolve_relative(repository, value, label)
    return ensure_within(declared_root, candidate, label)
