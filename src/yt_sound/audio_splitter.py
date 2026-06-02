from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


PART_DURATION = 30 * 60
SEARCH_WINDOWS = (3 * 60, 5 * 60)
SILENCE_DURATION = 0.7
SILENCE_NOISE = "-35dB"

_SILENCE_RE = re.compile(r"silence_(start|end):\s*(-?\d+(?:\.\d+)?)")


@dataclass(frozen=True)
class SplitPoint:
    seconds: float
    found_in_silence: bool


@dataclass(frozen=True)
class SplitResult:
    source: Path
    duration: float
    split_points: tuple[SplitPoint, ...]
    parts: tuple[Path, ...]


def get_duration(file_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def detect_silences(file_path: Path, start: float, end: float) -> list[tuple[float, float]]:
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-ss",
            str(start),
            "-t",
            str(end - start),
            "-i",
            str(file_path),
            "-af",
            f"silencedetect=noise={SILENCE_NOISE}:d={SILENCE_DURATION}",
            "-f",
            "null",
            "-",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return _parse_silences(result.stderr, offset=start, window_duration=end - start)


def _parse_silences(
    output: str,
    *,
    offset: float,
    window_duration: float,
) -> list[tuple[float, float]]:
    intervals = []
    silence_start = None
    for match in _SILENCE_RE.finditer(output):
        event, value = match.groups()
        seconds = float(value)
        if event == "start":
            silence_start = seconds
        elif silence_start is not None:
            intervals.append((offset + silence_start, offset + seconds))
            silence_start = None
    if silence_start is not None:
        intervals.append((offset + silence_start, offset + window_duration))
    return intervals


def choose_split_point(
    file_path: Path,
    target: float,
    duration: float,
) -> SplitPoint:
    for window in SEARCH_WINDOWS:
        start = max(0.0, target - window)
        end = min(duration, target + window)
        silences = detect_silences(file_path, start, end)
        if silences:
            closest = min(
                silences,
                key=lambda interval: abs((interval[0] + interval[1]) / 2 - target),
            )
            return SplitPoint(seconds=(closest[0] + closest[1]) / 2, found_in_silence=True)
    return SplitPoint(seconds=target, found_in_silence=False)


def find_split_points(file_path: Path, duration: float) -> tuple[SplitPoint, ...]:
    points = []
    previous = 0.0
    while duration - previous > PART_DURATION:
        point = choose_split_point(file_path, previous + PART_DURATION, duration)
        points.append(point)
        previous = point.seconds
    return tuple(points)


def split_audio(file_path: Path) -> SplitResult:
    duration = get_duration(file_path)
    split_points = find_split_points(file_path, duration)
    if not split_points:
        return SplitResult(file_path, duration, (), ())

    parts = []
    boundaries = [0.0, *(point.seconds for point in split_points), duration]
    for index, (start, end) in enumerate(zip(boundaries, boundaries[1:]), start=1):
        part_path = file_path.with_name(f"{file_path.stem}.part-{index:03d}{file_path.suffix}")
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                str(start),
                "-t",
                str(end - start),
                "-i",
                str(file_path),
                "-c",
                "copy",
                str(part_path),
            ],
            check=True,
        )
        parts.append(part_path)
    return SplitResult(file_path, duration, split_points, tuple(parts))


def format_timestamp(seconds: float) -> str:
    total_seconds = round(seconds)
    hours, remainder = divmod(total_seconds, 60 * 60)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
