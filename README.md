# py-get-yt-sound

A small CLI tool built on top of `yt-dlp` for downloading audio tracks.
Audio conversion requires `ffmpeg` to be installed.

## Installation

Run all commands in a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Usage

Download audio as MP3 into the `downloads` directory:

```bash
.venv/bin/yt-sound "https://www.youtube.com/watch?v=VIDEO_ID"
```

Choose an audio format and output directory:

```bash
.venv/bin/yt-sound --audio-format m4a --output-dir audio "URL"
```

By default, only one video is downloaded. Add `--playlist` to download a playlist.

Settings are read from `yt-sound.json` in the current directory by default:

```json
{
  "fragment_length_seconds": 1800,
  "mp3_bitrate_kbps": 192
}
```

Use `--config path/to/settings.json` to choose another settings file.
`mp3_bitrate_kbps` is passed to `yt-dlp`/`ffmpeg` as the MP3 audio bitrate.
It is applied only when `--audio-format mp3` is used.

If an audio file is longer than `fragment_length_seconds`, parts named `*.part-001.*`,
`*.part-002.*`, and so on are automatically created next to the original file.
The tool searches for the nearest silence within 3 minutes of the split point,
then within 5 minutes. If no suitable silence is found, it uses the exact
fragment boundary.

After each run, a `download-report-*.txt` text report is created in the download
directory with the names of the processed files and their split points.
