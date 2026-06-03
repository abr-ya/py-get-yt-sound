from __future__ import annotations

from datetime import datetime
from pathlib import Path

from yt_sound.audio_splitter import SplitResult, format_timestamp


class DownloadReport:
    def __init__(self, output_dir: Path, fragment_length_seconds: int) -> None:
        self.fragment_length_seconds = fragment_length_seconds
        self.created_at = datetime.now().astimezone()
        filename = self.created_at.strftime("download-report-%Y%m%d-%H%M%S-%f.txt")
        self.path = output_dir / filename
        self._write(f"Дата и время отчета: {self.created_at.isoformat(timespec='seconds')}\n\n")

    def add(self, index: int, result: SplitResult) -> None:
        lines = [
            f"Видео #{index}",
            f"Файл: {result.source.name}",
            f"Длительность: {format_timestamp(result.duration)}",
        ]
        if result.split_points:
            lines.append("Точки разреза:")
            for point in result.split_points:
                method = "пауза" if point.found_in_silence else "точная отметка"
                lines.append(f"- {format_timestamp(point.seconds)} ({method})")
            lines.append("Части:")
            lines.extend(f"- {part.name}" for part in result.parts)
        else:
            lines.append(
                "Точки разреза: нет, файл не длиннее "
                f"{format_timestamp(self.fragment_length_seconds)}"
            )
        self._write("\n".join(lines) + "\n\n")

    def _write(self, text: str) -> None:
        with self.path.open("a", encoding="utf-8") as report_file:
            report_file.write(text)
