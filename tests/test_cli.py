from pathlib import Path
from types import SimpleNamespace

from yt_sound import cli
from yt_sound.audio_splitter import SplitResult


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

    cli.download_audio("https://example.test/video", "mp3", tmp_path, False)

    assert received["urls"] == ["https://example.test/video"]
    assert received["options"]["format"] == "bestaudio/best"
    assert received["options"]["noplaylist"] is True
    assert received["options"]["postprocessors"][0]["preferredcodec"] == "mp3"
    assert len(received["options"]["postprocessor_hooks"]) == 1


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

    def fake_split_audio(file_path):
        received["file_path"] = file_path
        return SplitResult(file_path, 60.0, (), ())

    monkeypatch.setitem(
        __import__("sys").modules,
        "yt_dlp",
        SimpleNamespace(YoutubeDL=FakeYoutubeDL),
    )
    monkeypatch.setattr(cli, "split_audio", fake_split_audio)

    cli.download_audio("https://example.test/video", "mp3", tmp_path, False)

    assert received["file_path"] == audio_file
    report = next(tmp_path.glob("download-report-*.txt")).read_text(encoding="utf-8")
    assert "Видео #1" in report
    assert "Файл: episode.mp3" in report
