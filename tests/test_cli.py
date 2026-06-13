from pathlib import Path
from types import SimpleNamespace

import pytest

from yt_sound import cli
from yt_sound.audio_splitter import SplitResult
from yt_sound.settings import Settings


def test_download_audio_configures_yt_dlp(monkeypatch, tmp_path: Path) -> None:
    received = {}

    class FakeYoutubeDL:
        def __init__(self, options):
            received["options"] = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def download(self, urls):
            received["urls"] = urls

    monkeypatch.setitem(
        __import__("sys").modules,
        "yt_dlp",
        SimpleNamespace(YoutubeDL=FakeYoutubeDL),
    )

    cli.download_audio(
        "https://example.test/video",
        "mp3",
        tmp_path,
        False,
        Settings(mp3_bitrate_kbps=256),
    )

    assert received["urls"] == ["https://example.test/video"]
    assert received["options"]["format"] == "bestaudio/best"
    assert received["options"]["noplaylist"] is True
    assert received["options"]["outtmpl"] == str(
        tmp_path / "%(title)s [%(id)s].%(ext)s"
    )
    assert received["options"]["postprocessors"][0]["preferredcodec"] == "mp3"
    assert received["options"]["postprocessors"][0]["preferredquality"] == "256"
    assert len(received["options"]["postprocessor_hooks"]) == 1


def test_download_audio_uses_custom_filename(monkeypatch, tmp_path: Path) -> None:
    received = {}

    class FakeYoutubeDL:
        def __init__(self, options):
            received["options"] = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def download(self, urls):
            pass

    monkeypatch.setitem(
        __import__("sys").modules,
        "yt_dlp",
        SimpleNamespace(YoutubeDL=FakeYoutubeDL),
    )

    cli.download_audio(
        "https://example.test/video",
        "mp3",
        tmp_path,
        False,
        filename="my 100% audio",
    )

    assert received["options"]["outtmpl"] == str(
        tmp_path / "my 100%% audio.%(ext)s"
    )


def test_download_audio_rejects_custom_filename_for_playlist(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="cannot be used with --playlist"):
        cli.download_audio(
            "https://example.test/playlist",
            "mp3",
            tmp_path,
            True,
            filename="playlist",
        )


@pytest.mark.parametrize("value", ["", ".", "..", "folder/name", "folder\\name"])
def test_filename_stem_rejects_invalid_names(value: str) -> None:
    with pytest.raises(cli.argparse.ArgumentTypeError):
        cli.filename_stem(value)


def test_download_audio_does_not_set_mp3_quality_for_other_formats(
    monkeypatch,
    tmp_path: Path,
) -> None:
    received = {}

    class FakeYoutubeDL:
        def __init__(self, options):
            received["options"] = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def download(self, urls):
            pass

    monkeypatch.setitem(
        __import__("sys").modules,
        "yt_dlp",
        SimpleNamespace(YoutubeDL=FakeYoutubeDL),
    )

    cli.download_audio(
        "https://example.test/video",
        "m4a",
        tmp_path,
        False,
        Settings(mp3_bitrate_kbps=256),
    )

    assert "preferredquality" not in received["options"]["postprocessors"][0]


def test_download_audio_processes_finished_move_files_hook(monkeypatch, tmp_path: Path) -> None:
    received = {}
    audio_file = tmp_path / "episode.mp3"

    class FakeYoutubeDL:
        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def download(self, urls):
            hook = self.options["postprocessor_hooks"][0]
            hook(
                {
                    "status": "finished",
                    "postprocessor": "MoveFiles",
                    "info_dict": {
                        "filepath": str(audio_file),
                        "title": "Original episode title",
                    },
                }
            )

    def fake_split_audio(file_path, part_duration):
        received["file_path"] = file_path
        received["part_duration"] = part_duration
        return SplitResult(file_path, 60.0, (), ())

    monkeypatch.setitem(
        __import__("sys").modules,
        "yt_dlp",
        SimpleNamespace(YoutubeDL=FakeYoutubeDL),
    )
    monkeypatch.setattr(cli, "split_audio", fake_split_audio)

    cli.download_audio(
        "https://example.test/video",
        "mp3",
        tmp_path,
        False,
        Settings(fragment_length_seconds=45),
    )

    assert received["file_path"] == audio_file
    assert received["part_duration"] == 45
    report = next(tmp_path.glob("download-report-*.txt")).read_text(encoding="utf-8")
    assert "Видео #1" in report
    assert "Оригинальное название: Original episode title" in report
    assert "Файл: episode.mp3" in report


def test_download_audio_can_skip_splitting(monkeypatch, tmp_path: Path) -> None:
    received = {"split_called": False}
    audio_file = tmp_path / "episode.mp3"

    class FakeYoutubeDL:
        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def download(self, urls):
            hook = self.options["postprocessor_hooks"][0]
            hook(
                {
                    "status": "finished",
                    "postprocessor": "MoveFiles",
                    "info_dict": {
                        "filepath": str(audio_file),
                        "title": "Original episode title",
                    },
                }
            )

    def fake_split_audio(file_path, part_duration):
        received["split_called"] = True
        return SplitResult(file_path, 60.0, (), ())

    monkeypatch.setitem(
        __import__("sys").modules,
        "yt_dlp",
        SimpleNamespace(YoutubeDL=FakeYoutubeDL),
    )
    monkeypatch.setattr(cli, "split_audio", fake_split_audio)

    cli.download_audio(
        "https://example.test/video",
        "mp3",
        tmp_path,
        False,
        Settings(split_audio=False),
    )

    assert received["split_called"] is False
    report = next(tmp_path.glob("download-report-*.txt")).read_text(encoding="utf-8")
    assert "Видео #1" in report
    assert "Оригинальное название: Original episode title" in report
    assert "Файл: episode.mp3" in report
    assert "Нарезка: отключена в настройках" in report
