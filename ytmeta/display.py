import textwrap
from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

console = Console()


def _fmt_number(n) -> str:
    if n is None:
        return "N/A"
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _fmt_duration(seconds) -> str:
    if seconds is None:
        return "N/A"
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def _fmt_date(date_str) -> str:
    if date_str is None:
        return "N/A"
    try:
        dt = datetime.strptime(str(date_str), "%Y%m%d")
        return dt.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return str(date_str)


def _truncate(text, width=80):
    if text is None:
        return ""
    return textwrap.fill(text, width=width, max_lines=20, placeholder="...")


def display_metadata(info: dict):
    """Render metadata with Rich."""
    title = info.get("title", "Unknown")
    channel = info.get("channel", info.get("uploader", "Unknown"))

    # ── Header ───────────────────────────────────────────────────────────
    header = Text()
    header.append("  ytmeta  ", style="bold white on blue")
    header.append("  ", style="default")
    header.append(title, style="bold white")
    console.print(header)
    console.print()

    # ── Overview Panel ───────────────────────────────────────────────────
    overview = Table.grid(padding=(0, 2))
    overview.add_column(style="bold cyan", width=14)
    overview.add_column()

    overview.add_row("Channel", channel)
    overview.add_row("Upload Date", _fmt_date(info.get("upload_date")))
    overview.add_row("Duration", _fmt_duration(info.get("duration")))
    overview.add_row("Category", info.get("category", "N/A"))
    overview.add_row("Video ID", info.get("id", "N/A"))

    console.print(Panel(overview, title="[bold]Overview[/bold]", border_style="blue"))

    # ── Statistics Panel ─────────────────────────────────────────────────
    stats = Table.grid(padding=(0, 2))
    stats.add_column(style="bold green", width=14)
    stats.add_column()

    view_count = info.get("view_count")
    like_count = info.get("like_count")
    comment_count = info.get("comment_count")
    dislike_count = info.get("dislike_count")

    stats.add_row("Views", _fmt_number(view_count))
    stats.add_row("Likes", _fmt_number(like_count))
    if dislike_count is not None:
        stats.add_row("Dislikes", _fmt_number(dislike_count))
    stats.add_row("Comments", _fmt_number(comment_count))

    console.print(Panel(stats, title="[bold]Statistics[/bold]", border_style="green"))

    # ── Technical Details Panel ──────────────────────────────────────────
    tech = Table.grid(padding=(0, 2))
    tech.add_column(style="bold yellow", width=14)
    tech.add_column()

    duration_s = info.get("duration")
    view_count_val = int(view_count) if view_count else 0
    if duration_s and view_count_val:
        watch_hours = (view_count_val * duration_s) / 3600
        tech.add_row("Est. Watch Hours", f"{watch_hours:,.0f}")

    tech.add_row("Resolution", info.get("resolution", "N/A"))
    tech.add_row("FPS", str(info.get("fps", "N/A")))

    # Format selection info
    fmt = info.get("format", "N/A")
    if fmt and len(fmt) > 40:
        fmt = fmt[:37] + "..."
    tech.add_row("Format", fmt)

    vcodec = info.get("vcodec", "N/A")
    acodec = info.get("acodec", "N/A")
    tech.add_row("Video Codec", vcodec if vcodec and vcodec != "none" else "N/A")
    tech.add_row("Audio Codec", acodec if acodec and acodec != "none" else "N/A")

    tbr = info.get("tbr")
    if tbr:
        tech.add_row("Total Bitrate", f"{tbr:.0f} kbps")
    vbr = info.get("vbr")
    if vbr:
        tech.add_row("Video Bitrate", f"{vbr:.0f} kbps")
    abr = info.get("abr")
    if abr:
        tech.add_row("Audio Bitrate", f"{abr:.0f} kbps")

    filesize = info.get("filesize") or info.get("filesize_approx")
    if filesize:
        size_mb = filesize / (1024 * 1024)
        tech.add_row("File Size", f"{size_mb:.1f} MB")

    tech.add_row("Has Subtitles", "Yes" if info.get("subtitles") else "No")
    tech.add_row("Has Chapters", "Yes" if info.get("chapters") else "No")

    # Live status
    is_live = info.get("is_live")
    was_live = info.get("was_live")
    if is_live:
        tech.add_row("Status", "[bold red]LIVE NOW[/bold red]")
    elif was_live:
        tech.add_row("Status", "[yellow]Was Live[/yellow]")

    console.print(
        Panel(tech, title="[bold]Technical Details[/bold]", border_style="yellow")
    )

    # ── Availability Panel ───────────────────────────────────────────────
    avail = Table.grid(padding=(0, 2))
    avail.add_column(style="bold magenta", width=14)
    avail.add_column()

    age = info.get("age_limit")
    if age is not None:
        avail.add_row("Age Restriction", f"{age}+")

    avail.add_row("Is Private", "Yes" if info.get("is_private") else "No")
    avail.add_row("Is Unlisted", "Yes" if info.get("was_unlisted") else "No")
    avail.add_row("Is Live", "Yes" if info.get("is_live") else "No")
    avail.add_row("Is Episode", "Yes" if info.get("is_episode") else "No")

    console.print(
        Panel(avail, title="[bold]Availability[/bold]", border_style="magenta")
    )

    # ── Subtitles Panel ──────────────────────────────────────────────────
    subtitles = info.get("subtitles", {})
    auto_captions = info.get("automatic_captions", {})

    if subtitles or auto_captions:
        sub_table = Table(title="Subtitles & Captions", border_style="cyan")
        sub_table.add_column("Language", style="cyan")
        sub_table.add_column("Type", style="white")
        sub_table.add_column("Formats")

        if subtitles:
            for lang, formats in sorted(subtitles.items()):
                fmt_list = ", ".join(f.get("ext", "?") for f in formats)
                sub_table.add_row(lang, "Manual", fmt_list)

        if auto_captions:
            non_manual = {k: v for k, v in auto_captions.items() if k not in subtitles}
            shown = 0
            for lang, formats in sorted(non_manual.items()):
                if shown >= 10:
                    break
                fmt_list = ", ".join(f.get("ext", "?") for f in formats)
                sub_table.add_row(lang, "Auto", fmt_list)
                shown += 1
            remaining = len(non_manual) - shown
            if remaining > 0:
                sub_table.add_row(
                    f"[dim]+{remaining} more[/dim]", "[dim]Auto[/dim]", "[dim]...[/dim]"
                )

        console.print(
            Panel(sub_table, title="[bold]Subtitles & Captions[/bold]", border_style="cyan")
        )

    # ── Chapters Panel ───────────────────────────────────────────────────
    chapters = info.get("chapters")
    if chapters:
        ch_tree = Tree("[bold]Chapters[/bold]", guide_style="bright_blue")
        for ch in chapters:
            start = ch.get("start_time", 0)
            end = ch.get("end_time", 0)
            ch_title = ch.get("title", "Untitled")
            duration_str = _fmt_duration(end - start)
            ch_tree.add(
                f"[cyan]{_fmt_duration(start)}[/cyan]  {ch_title}  [dim]({duration_str})[/dim]"
            )

        console.print(
            Panel(ch_tree, title="[bold]Chapters[/bold]", border_style="bright_blue")
        )

    # ── Tags Panel ───────────────────────────────────────────────────────
    tags = info.get("tags")
    if tags:
        tag_text = Text()
        for i, tag in enumerate(tags):
            style = ["bold red", "bold green", "bold blue", "bold yellow", "bold magenta"][
                i % 5
            ]
            tag_text.append(f"#{tag} ", style=style)

        console.print(Panel(tag_text, title="[bold]Tags[/bold]", border_style="red"))

    # ── Description Panel ────────────────────────────────────────────────
    description = info.get("description")
    if description:
        truncated = _truncate(description, width=console.width - 4)
        console.print(
            Panel(
                truncated,
                title="[bold]Description[/bold]",
                border_style="white",
                padding=(1, 2),
            )
        )

    # ── URLs Panel ───────────────────────────────────────────────────────
    url_table = Table.grid(padding=(0, 2))
    url_table.add_column(style="bold blue", width=14)
    url_table.add_column()

    video_url = info.get("webpage_url") or info.get("url")
    channel_url = info.get("channel_url") or info.get("uploader_url")

    if video_url:
        url_table.add_row("Video URL", video_url)
    if channel_url:
        url_table.add_row("Channel URL", channel_url)
    if info.get("playlist_url"):
        url_table.add_row("Playlist URL", info.get("playlist_url"))
    if info.get("thumbnail"):
        url_table.add_row("Thumbnail", info["thumbnail"])

    console.print(
        Panel(url_table, title="[bold]URLs[/bold]", border_style="blue")
    )

    # ── Available Formats ────────────────────────────────────────────────
    formats = info.get("formats")
    if formats and len(formats) > 1:
        fmt_table = Table(title="Available Formats", border_style="bright_black")
        fmt_table.add_column("Format ID", style="dim")
        fmt_table.add_column("Ext")
        fmt_table.add_column("Resolution", style="cyan")
        fmt_table.add_column("FPS", justify="right")
        fmt_table.add_column("VCodec")
        fmt_table.add_column("ACodec")
        fmt_table.add_column("Size", justify="right")
        fmt_table.add_column("Bitrate", justify="right")

        for f in formats:
            fs = f.get("filesize") or f.get("filesize_approx")
            size_str = f"{fs / (1024*1024):.1f} MB" if fs else "N/A"
            tbr_str = f"{f.get('tbr', 0):.0f} kbps" if f.get("tbr") else "N/A"
            res = f.get("resolution", "audio only" if f.get("vcodec") == "none" else "N/A")
            vcodec = f.get("vcodec", "none")
            if vcodec == "none":
                vcodec = "-"
            acodec = f.get("acodec", "none")
            if acodec == "none":
                acodec = "-"

            fmt_table.add_row(
                str(f.get("format_id", "?")),
                f.get("ext", "?"),
                res,
                str(f.get("fps", "")),
                vcodec[:12] if vcodec else "-",
                acodec[:12] if acodec else "-",
                size_str,
                tbr_str,
            )

        console.print(
            Panel(fmt_table, title="[bold]Available Formats[/bold]", border_style="bright_black")
        )

    # ── Footer ───────────────────────────────────────────────────────────
    console.print()
    console.print(
        f"  [dim]Fetched at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by ytmeta[/dim]"
    )
