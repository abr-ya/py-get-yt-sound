from pathlib import Path
from types import SimpleNamespace

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
    assert received["options"]["postprocessors"][0]["preferredcodec"] == "mp3"
    assert received["options"]["postprocessors"][0]["preferredquality"] == "256"
    assert len(received["options"]["postprocessor_hooks"]) == 1


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
                    "info_dict": {"filepath": str(audio_file)},
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
                    "info_dict": {"filepath": str(audio_file)},
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
    assert "Файл: episode.mp3" in report
    assert "Нарезка: отключена в настройках" in report
