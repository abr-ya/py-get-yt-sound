from pathlib import Path
from types import SimpleNamespace

from yt_sound import cli


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

