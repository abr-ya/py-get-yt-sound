# py-get-yt-sound

Небольшой CLI-инструмент поверх `yt-dlp` для скачивания звуковой дорожки.
Для преобразования аудио требуется установленный `ffmpeg`.

## Установка

Все команды выполняются в виртуальном окружении:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Использование

Скачать звук в MP3 в каталог `downloads`:

```bash
.venv/bin/yt-sound "https://www.youtube.com/watch?v=VIDEO_ID"
```

Выбрать формат и каталог:

```bash
.venv/bin/yt-sound --audio-format m4a --output-dir audio "URL"
```

По умолчанию скачивается только один ролик. Для плейлиста добавьте `--playlist`.
