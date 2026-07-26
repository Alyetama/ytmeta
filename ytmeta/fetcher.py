import yt_dlp


def fetch_metadata(url: str) -> dict:
    """Fetch video metadata using yt-dlp without downloading.

    Raises yt_dlp.utils.DownloadError on failure.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "logger": _NullLogger(),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info


class _NullLogger:
    """Suppress yt-dlp's internal logging to avoid stderr duplication."""

    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass
