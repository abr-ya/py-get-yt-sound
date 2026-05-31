from __future__ import annotations

import argparse
from pathlib import Path


AUDIO_FORMATS = ("mp3", "m4a", "opus", "wav", "flac")


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
) -> None:
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError(
            "yt-dlp is not installed. Run: .venv/bin/pip install -e ."
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    options = {
        "format": "bestaudio/best",
        "noplaylist": not allow_playlist,
        "outtmpl": str(output_dir / "%(title)s [%(id)s].%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
            }
        ],
    }

    with yt_dlp.YoutubeDL(options) as downloader:
        downloader.download([url])


def main() -> int:
    args = build_parser().parse_args()
    try:
        download_audio(
            url=args.url,
            audio_format=args.audio_format,
            output_dir=args.output_dir,
            allow_playlist=args.playlist,
        )
    except RuntimeError as exc:
        print(f"error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

