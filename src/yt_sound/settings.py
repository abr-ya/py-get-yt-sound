from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("yt-sound.json")
DEFAULT_FRAGMENT_LENGTH_MINUTES = 30
DEFAULT_FRAGMENT_LENGTH_SECONDS = DEFAULT_FRAGMENT_LENGTH_MINUTES * 60
DEFAULT_MP3_BITRATE_KBPS = 192


@dataclass(frozen=True)
class Settings:
    fragment_length_seconds: int = DEFAULT_FRAGMENT_LENGTH_SECONDS
    mp3_bitrate_kbps: int = DEFAULT_MP3_BITRATE_KBPS
    split_audio: bool = True


def load_settings(path: Path = DEFAULT_CONFIG_PATH) -> Settings:
    if not path.exists():
        return Settings()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid settings file {path}: {exc.msg}") from exc

    if not isinstance(raw, dict):
        raise RuntimeError(f"invalid settings file {path}: expected JSON object")

    return Settings(
        fragment_length_seconds=_read_fragment_length_seconds(
            raw,
            path,
        ),
        mp3_bitrate_kbps=_read_positive_int(
            raw,
            "mp3_bitrate_kbps",
            DEFAULT_MP3_BITRATE_KBPS,
            path,
        ),
        split_audio=_read_bool(
            raw,
            "split_audio",
            True,
            path,
        ),
    )


def _read_fragment_length_seconds(data: dict[str, Any], path: Path) -> int:
    if "fragment_length_minutes" in data:
        minutes = _read_positive_int(
            data,
            "fragment_length_minutes",
            DEFAULT_FRAGMENT_LENGTH_MINUTES,
            path,
        )
        return minutes * 60

    return _read_positive_int(
        data,
        "fragment_length_seconds",
        DEFAULT_FRAGMENT_LENGTH_SECONDS,
        path,
    )


def _read_positive_int(
    data: dict[str, Any],
    key: str,
    default: int,
    path: Path,
) -> int:
    value = data.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise RuntimeError(f"invalid settings file {path}: {key} must be a positive integer")
    return value


def _read_bool(
    data: dict[str, Any],
    key: str,
    default: bool,
    path: Path,
) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise RuntimeError(f"invalid settings file {path}: {key} must be a boolean")
    return value
