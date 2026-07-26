#!/usr/bin/env python3
"""ytmeta web — Flask API server for YouTube metadata."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, jsonify, request, send_from_directory
from ytmeta.fetcher import fetch_metadata

app = Flask(__name__, static_folder="static")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


@app.route("/api/metadata", methods=["GET"])
def api_metadata():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "Missing 'url' query parameter"}), 400

    try:
        info = fetch_metadata(url)
    except Exception as e:
        return jsonify({"error": str(e).strip() or repr(e)}), 400

    # Build a clean, frontend-friendly payload
    payload = {
        "id": info.get("id"),
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "channel_url": info.get("channel_url") or info.get("uploader_url"),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
        "category": info.get("category"),
        "thumbnail": info.get("thumbnail"),
        "webpage_url": info.get("webpage_url"),
        "description": info.get("description"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "dislike_count": info.get("dislike_count"),
        "comment_count": info.get("comment_count"),
        "is_live": info.get("is_live"),
        "was_live": info.get("was_live"),
        "is_private": info.get("is_private"),
        "was_unlisted": info.get("was_unlisted"),
        "is_episode": info.get("is_episode"),
        "age_limit": info.get("age_limit"),
        "resolution": info.get("resolution"),
        "fps": info.get("fps"),
        "format": info.get("format"),
        "vcodec": info.get("vcodec"),
        "acodec": info.get("acodec"),
        "tbr": info.get("tbr"),
        "vbr": info.get("vbr"),
        "abr": info.get("abr"),
        "filesize": info.get("filesize") or info.get("filesize_approx"),
        "tags": info.get("tags"),
        "chapters": info.get("chapters"),
        "subtitles": list(info.get("subtitles", {}).keys()) if info.get("subtitles") else [],
        "auto_captions_count": (
            len(info.get("automatic_captions", {}))
            - len(info.get("subtitles", {}))
            if info.get("automatic_captions")
            else 0
        ),
        "formats": [
            {
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "resolution": f.get("resolution"),
                "fps": f.get("fps"),
                "vcodec": f.get("vcodec"),
                "acodec": f.get("acodec"),
                "filesize": f.get("filesize") or f.get("filesize_approx"),
                "tbr": f.get("tbr"),
            }
            for f in (info.get("formats") or [])
        ],
    }
    return jsonify(payload)


if __name__ == "__main__":
    print("  ytmeta web running at http://localhost:5050")
    app.run(host="0.0.0.0", port=5050, debug=False)
