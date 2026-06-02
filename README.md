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

If an audio file is longer than 30 minutes, parts named `*.part-001.*`,
`*.part-002.*`, and so on are automatically created next to the original file.
The tool searches for the nearest silence within 3 minutes of the split point,
then within 5 minutes. If no suitable silence is found, it uses the exact
30-minute mark.

After each run, a `download-report-*.txt` text report is created in the download
directory with the names of the processed files and their split points.
