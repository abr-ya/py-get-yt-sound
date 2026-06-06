from pathlib import Path

import pytest

from yt_sound.settings import Settings, load_settings


def test_load_settings_uses_defaults_when_file_is_missing(tmp_path: Path) -> None:
    assert load_settings(tmp_path / "missing.json") == Settings()


def test_load_settings_reads_values(tmp_path: Path) -> None:
    config_path = tmp_path / "yt-sound.json"
    config_path.write_text(
        '{"fragment_length_minutes": 45, "mp3_bitrate_kbps": 256}',
        encoding="utf-8",
    )

    assert load_settings(config_path) == Settings(
        fragment_length_seconds=2700,
        mp3_bitrate_kbps=256,
    )


def test_load_settings_reads_split_audio_flag(tmp_path: Path) -> None:
    config_path = tmp_path / "yt-sound.json"
    config_path.write_text(
        '{"split_audio": false}',
        encoding="utf-8",
    )

    assert load_settings(config_path) == Settings(split_audio=False)


def test_load_settings_keeps_legacy_seconds_value(tmp_path: Path) -> None:
    config_path = tmp_path / "yt-sound.json"
    config_path.write_text(
        '{"fragment_length_seconds": 45, "mp3_bitrate_kbps": 256}',
        encoding="utf-8",
    )

    assert load_settings(config_path) == Settings(
        fragment_length_seconds=45,
        mp3_bitrate_kbps=256,
    )


def test_load_settings_rejects_invalid_values(tmp_path: Path) -> None:
    config_path = tmp_path / "yt-sound.json"
    config_path.write_text('{"fragment_length_minutes": 0}', encoding="utf-8")

    with pytest.raises(RuntimeError, match="fragment_length_minutes"):
        load_settings(config_path)


def test_load_settings_rejects_invalid_split_audio_flag(tmp_path: Path) -> None:
    config_path = tmp_path / "yt-sound.json"
    config_path.write_text('{"split_audio": "no"}', encoding="utf-8")

    with pytest.raises(RuntimeError, match="split_audio"):
        load_settings(config_path)
