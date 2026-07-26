#!/usr/bin/env python3
"""ytmeta - Extensive YouTube video metadata viewer."""

import argparse
import json
import sys

from rich.console import Console
from rich.table import Table

from ytmeta.display import console, display_metadata, _fmt_duration
from ytmeta.fetcher import fetch_metadata

DESCRIPTION = """\
ytmeta — Display extensive metadata for any YouTube video.

Provide a YouTube URL and get a rich, detailed breakdown of the video's
metadata including statistics, technical details, subtitles, chapters, tags, and more.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ytmeta",
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="YouTube video URL (supports youtu.be, youtube.com/watch, shorts, etc.)",
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="json_output",
        help="Output raw metadata as JSON instead of rich display",
    )
    parser.add_argument(
        "--no-formats",
        action="store_true",
        dest="hide_formats",
        help="Hide the available formats table",
    )
    parser.add_argument(
        "--no-subtitles",
        action="store_true",
        dest="hide_subtitles",
        help="Hide subtitles/captions panel",
    )
    parser.add_argument(
        "--no-description",
        action="store_true",
        dest="hide_description",
        help="Hide the description panel",
    )
    parser.add_argument(
        "--chapters-only",
        action="store_true",
        dest="chapters_only",
        help="Show only chapter information",
    )
    parser.add_argument(
        "--tags-only",
        action="store_true",
        dest="tags_only",
        help="Show only tags",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        dest="stats_only",
        help="Show only statistics (views, likes, comments)",
    )
    return parser


def _filter_info(info: dict, args) -> dict:
    """Return a copy of info filtered by CLI flags."""
    info = dict(info)
    if args.hide_formats:
        info.pop("formats", None)
    if args.hide_subtitles:
        info.pop("subtitles", None)
        info.pop("automatic_captions", None)
    if args.hide_description:
        info.pop("description", None)
    return info


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.url:
        parser.print_help()
        sys.exit(1)

    url = args.url.strip()

    try:
        if not args.json_output:
            console.print(f"  [dim]Fetching metadata for {url}...[/dim]\n")
        info = fetch_metadata(url)
    except Exception as e:
        msg = str(e).strip() or repr(e)
        if args.json_output:
            print(json.dumps({"error": msg}, indent=2))
        else:
            console.print(f"\n  [bold red]Error:[/bold red] {msg}\n")
        sys.exit(1)

    if args.json_output:
        clean = dict(info)
        clean.pop("formats", None)
        print(json.dumps(clean, indent=2, default=str))
        return

    # Mode-specific views that bypass full display
    if args.chapters_only:
        chapters = info.get("chapters")
        if not chapters:
            console.print("  [yellow]No chapters found for this video.[/yellow]")
            return
        from rich.tree import Tree

        tree = Tree(f"[bold]{info.get('title', 'Untitled')}[/bold]", guide_style="bright_blue")
        for ch in chapters:
            start = ch.get("start_time", 0)
            end = ch.get("end_time", 0)
            ch_title = ch.get("title", "Untitled")
            tree.add(f"[cyan]{_fmt_duration(start)}[/cyan]  {ch_title}  [dim]({_fmt_duration(end-start)})[/dim]")
        console.print(tree)
        return

    if args.tags_only:
        tags = info.get("tags")
        if not tags:
            console.print("  [yellow]No tags found for this video.[/yellow]")
            return
        table = Table(title=f"Tags — {info.get('title', '')}", border_style="red")
        table.add_column("#", style="dim")
        table.add_column("Tag", style="bold")
        for i, tag in enumerate(tags, 1):
            table.add_row(str(i), tag)
        console.print(table)
        return

    if args.stats_only:
        table = Table(title=f"Stats — {info.get('title', '')}", border_style="green")
        table.add_column("Metric", style="bold green")
        table.add_column("Value", style="white", justify="right")
        if info.get("view_count"):
            table.add_row("Views", f"{info['view_count']:,}")
        if info.get("like_count"):
            table.add_row("Likes", f"{info['like_count']:,}")
        if info.get("dislike_count"):
            table.add_row("Dislikes", f"{info['dislike_count']:,}")
        if info.get("comment_count"):
            table.add_row("Comments", f"{info['comment_count']:,}")
        console.print(table)
        return

    display_info = _filter_info(info, args)
    display_metadata(display_info)


if __name__ == "__main__":
    main()
