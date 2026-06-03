from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("yt-sound.json")
DEFAULT_FRAGMENT_LENGTH_SECONDS = 30 * 60
DEFAULT_MP3_BITRATE_KBPS = 192


@dataclass(frozen=True)
class Settings:
    fragment_length_seconds: int = DEFAULT_FRAGMENT_LENGTH_SECONDS
    mp3_bitrate_kbps: int = DEFAULT_MP3_BITRATE_KBPS


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
        fragment_length_seconds=_read_positive_int(
            raw,
            "fragment_length_seconds",
            DEFAULT_FRAGMENT_LENGTH_SECONDS,
            path,
        ),
        mp3_bitrate_kbps=_read_positive_int(
            raw,
            "mp3_bitrate_kbps",
            DEFAULT_MP3_BITRATE_KBPS,
            path,
        ),
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
