from __future__ import annotations

import argparse
from pathlib import Path

from yt_sound.audio_splitter import split_audio
from yt_sound.report import DownloadReport
from yt_sound.settings import DEFAULT_CONFIG_PATH, Settings, load_settings


AUDIO_FORMATS = ("mp3", "m4a", "opus", "wav", "flac")


def filename_stem(value: str) -> str:
    if not value or value in {".", ".."} or "/" in value or "\\" in value:
        raise argparse.ArgumentTypeError(
            "filename must be a file name without a directory path"
        )
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt-sound",
        description="Download audio from a video URL using yt-dlp.",
    )
    parser.add_argument("url", help="Video or playlist URL")
    parser.add_argument(
        "-f",
        "--audio-format",
        choices=AUDIO_FORMATS,
        default="mp3",
        help="Output audio format (default: mp3)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("downloads"),
        help="Directory for downloaded files (default: downloads)",
    )
    parser.add_argument(
        "-n",
        "--filename",
        type=filename_stem,
        help="Output file name without extension (default: video title and ID)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Settings file path (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--playlist",
        action="store_true",
        help="Allow downloading an entire playlist",
    )
    return parser


def download_audio(
    url: str,
    audio_format: str,
    output_dir: Path,
    allow_playlist: bool,
    settings: Settings | None = None,
    filename: str | None = None,
) -> None:
    if filename and allow_playlist:
        raise RuntimeError("--filename cannot be used with --playlist")

    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError(
            "yt-dlp is not installed. Run: .venv/bin/pip install -e ."
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    settings = settings or Settings()
    audio_postprocessor = {
        "key": "FFmpegExtractAudio",
        "preferredcodec": audio_format,
    }
    if audio_format == "mp3":
        audio_postprocessor["preferredquality"] = str(settings.mp3_bitrate_kbps)

    output_name = (
        f"{filename.replace('%', '%%')}.%(ext)s"
        if filename
        else "%(title)s [%(id)s].%(ext)s"
    )
    options = {
        "format": "bestaudio/best",
        "noplaylist": not allow_playlist,
        "outtmpl": str(output_dir / output_name),
        "postprocessors": [audio_postprocessor],
    }
    report = DownloadReport(output_dir, settings.fragment_length_seconds)
    processed_files: set[Path] = set()
    video_index = 0

    def process_downloaded_audio(status: dict) -> None:
        nonlocal video_index
        if status.get("status") != "finished" or status.get("postprocessor") != "MoveFiles":
            return
        info = status["info_dict"]
        file_path = Path(info["filepath"])
        original_title = info.get("title")
        if file_path in processed_files:
            return
        processed_files.add(file_path)
        video_index += 1
        if settings.split_audio:
            report.add(
                video_index,
                split_audio(file_path, settings.fragment_length_seconds),
                original_title,
            )
        else:
            report.add_without_split(video_index, file_path, original_title)

    options["postprocessor_hooks"] = [process_downloaded_audio]

    with yt_dlp.YoutubeDL(options) as downloader:
        downloader.download([url])


def main() -> int:
    args = build_parser().parse_args()
    try:
        settings = load_settings(args.config)
        download_audio(
            url=args.url,
            audio_format=args.audio_format,
            output_dir=args.output_dir,
            allow_playlist=args.playlist,
            settings=settings,
            filename=args.filename,
        )
    except RuntimeError as exc:
        print(f"error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
