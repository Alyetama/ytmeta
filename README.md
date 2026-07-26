# ytmeta

CLI tool and web app to display extensive YouTube video metadata with rich terminal output and a dark-themed web UI.

## CLI

```bash
pip install -e .
ytmeta <youtube-url>
```

### Options

| Flag | Description |
|------|-------------|
| `-j, --json` | Output raw JSON |
| `--stats-only` | Views, likes, comments only |
| `--tags-only` | Tags only |
| `--chapters-only` | Chapters only |
| `--no-subtitles` | Hide subtitles panel |
| `--no-formats` | Hide formats table |
| `--no-description` | Hide description |

## Web

```bash
pip install -e .
python web/server.py
```

Open http://localhost:5050 in your browser.

## Dependencies

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [rich](https://github.com/Textualize/rich)
- [flask](https://flask.palletsprojects.com/)
