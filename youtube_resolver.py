"""YouTube audio resolver via yt-dlp.

Returns direct audio stream URLs (m4a preferred for Safari compat). URLs are
signed and expire in ~6h, so consumers should treat them as short-lived.
"""
from __future__ import annotations

import logging
from typing import Optional

try:
    import yt_dlp
except ImportError:  # pragma: no cover
    yt_dlp = None  # type: ignore

logger = logging.getLogger(__name__)

_YDL_OPTS = {
    # Prefer m4a/AAC — plays in <audio> on every browser.
    "format": "bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "extract_flat": False,
    "noplaylist": True,
    "socket_timeout": 20,
}

# Reject tracks outside this range — too short is likely a snippet/preview, too
# long is usually a full-album upload, hour-long mix, or "extended version".
MIN_DURATION_S = 60      # 1 minute
MAX_DURATION_S = 15 * 60 # 15 minutes


def resolve_via_youtube(title: str, artist: str = "") -> Optional[dict]:
    """Return {url, youtube_id, title, artist, duration_ms, source: 'youtube'} or None.

    Scans the top-N YouTube search results and picks the first one within the
    MIN/MAX duration window — this keeps album uploads and 30-second teasers
    from sneaking into the queue.
    """
    if yt_dlp is None:
        logger.warning("yt-dlp not installed")
        return None

    # Top 5 results; most tracks have "Topic" channel or official audio in top 3.
    query = f"ytsearch5:{title} {artist}".strip()
    try:
        with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
            info = ydl.extract_info(query, download=False)
    except Exception as exc:  # noqa: BLE001 - any yt-dlp error degrades gracefully
        logger.warning("yt-dlp failed for %r: %s", query, exc)
        return None

    if not info:
        return None

    entries = info.get("entries") if "entries" in info else [info]
    entries = [e for e in (entries or []) if e]
    if not entries:
        return None

    # Pick first entry with a playable URL in acceptable duration range.
    chosen = None
    for entry in entries:
        dur = entry.get("duration") or 0
        if dur < MIN_DURATION_S or dur > MAX_DURATION_S:
            continue
        if not entry.get("url"):
            continue
        chosen = entry
        break

    if chosen is None:
        # All candidates out of range or urlless — last-ditch, take first that has a url
        for entry in entries:
            if entry.get("url"):
                chosen = entry
                break

    if chosen is None:
        return None

    info = chosen
    url = info.get("url")
    if not url:
        return None

    duration_s = info.get("duration") or 0

    # Pick the highest-quality thumbnail available.
    thumb = info.get("thumbnail")
    thumbs = info.get("thumbnails") or []
    if thumbs:
        thumb = max(thumbs, key=lambda t: (t.get("width") or 0) * (t.get("height") or 0)).get("url") or thumb

    return {
        "url": url,
        "youtube_id": info.get("id"),
        "title": title,
        "artist": artist,
        "netease_title": info.get("title"),  # actual track name from YouTube
        "netease_artist": info.get("uploader", ""),
        "duration_ms": int(duration_s * 1000),
        "thumbnail": thumb,
        "source": "youtube",
    }
