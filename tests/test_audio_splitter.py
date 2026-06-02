from pathlib import Path

from yt_sound import audio_splitter


def test_choose_split_point_uses_silence_from_first_window(monkeypatch) -> None:
    calls = []

    def fake_detect_silences(file_path, start, end):
        calls.append((start, end))
        return [(1799.0, 1801.0)]

    monkeypatch.setattr(audio_splitter, "detect_silences", fake_detect_silences)

    point = audio_splitter.choose_split_point(Path("episode.mp3"), 1800.0, 4000.0)

    assert point == audio_splitter.SplitPoint(1800.0, True)
    assert calls == [(1620.0, 1980.0)]


def test_choose_split_point_expands_search_window(monkeypatch) -> None:
    calls = []

    def fake_detect_silences(file_path, start, end):
        calls.append((start, end))
        return [] if len(calls) == 1 else [(2039.0, 2041.0)]

    monkeypatch.setattr(audio_splitter, "detect_silences", fake_detect_silences)

    point = audio_splitter.choose_split_point(Path("episode.mp3"), 1800.0, 4000.0)

    assert point == audio_splitter.SplitPoint(2040.0, True)
    assert calls == [(1620.0, 1980.0), (1500.0, 2100.0)]


def test_choose_split_point_falls_back_to_exact_mark(monkeypatch) -> None:
    monkeypatch.setattr(audio_splitter, "detect_silences", lambda *args: [])

    point = audio_splitter.choose_split_point(Path("episode.mp3"), 1800.0, 4000.0)

    assert point == audio_splitter.SplitPoint(1800.0, False)


def test_find_split_points_keeps_parts_around_thirty_minutes(monkeypatch) -> None:
    monkeypatch.setattr(
        audio_splitter,
        "choose_split_point",
        lambda file_path, target, duration: audio_splitter.SplitPoint(target - 10, True),
    )

    points = audio_splitter.find_split_points(Path("episode.mp3"), 3700.0)

    assert points == (
        audio_splitter.SplitPoint(1790.0, True),
        audio_splitter.SplitPoint(3580.0, True),
    )


def test_parse_silences_adds_window_offset() -> None:
    output = """
[silencedetect @ 0x1] silence_start: 1.25
[silencedetect @ 0x1] silence_end: 3.75 | silence_duration: 2.5
"""

    silences = audio_splitter._parse_silences(output, offset=100.0, window_duration=10.0)

    assert silences == [(101.25, 103.75)]
