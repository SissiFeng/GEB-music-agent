"""Scrape Netease Cloud Music trending playlists as Kimi seed material.

Netease public endpoints (no login required):
    /top/playlist?cat=<category>&limit=N&order=hot
    /playlist/detail?id=<id>

Gives us "what's in the air right now" inspiration to feed Kimi so recommendations
drift across days even when the user's mood description is stable.
"""
from __future__ import annotations

import logging
import os
import random
from typing import Iterable, List

import requests

logger = logging.getLogger(__name__)

NETEASE_BASE = os.getenv("NETEASE_API_URL", "http://localhost:3000")


def fetch_playlist_seeds(
    categories: Iterable[str],
    max_tracks: int = 15,
    per_category: int = 2,
    tracks_per_playlist: int = 5,
) -> List[dict]:
    """Pull trending-playlist tracks across the given Netease categories.

    Returns a shuffled, deduplicated list of {title, artist, from_playlist, category}.
    Any failure degrades silently — callers expect a possibly-empty list.
    """
    candidates: List[dict] = []

    for cat in categories:
        try:
            r = requests.get(
                f"{NETEASE_BASE}/top/playlist",
                params={"cat": cat, "limit": per_category, "order": "hot"},
                timeout=5,
            )
            playlists = r.json().get("playlists", []) or []
        except Exception as exc:
            logger.debug("netease top/playlist failed for %s: %s", cat, exc)
            continue

        for pl in playlists[:per_category]:
            pl_id = pl.get("id")
            pl_name = pl.get("name", "")
            if not pl_id:
                continue
            try:
                d = requests.get(
                    f"{NETEASE_BASE}/playlist/detail",
                    params={"id": pl_id},
                    timeout=5,
                )
                tracks = d.json().get("playlist", {}).get("tracks", []) or []
            except Exception as exc:
                logger.debug("netease playlist/detail failed id=%s: %s", pl_id, exc)
                continue

            if not tracks:
                continue
            sample = random.sample(tracks, min(tracks_per_playlist, len(tracks)))
            for t in sample:
                name = t.get("name", "").strip()
                if not name:
                    continue
                artists = ", ".join(a.get("name", "") for a in t.get("ar", []) if a.get("name"))
                candidates.append({
                    "title": name,
                    "artist": artists,
                    "from_playlist": pl_name,
                    "category": cat,
                })

    # Dedup by (title lower, artist lower); shuffle so ordering is fresh per call
    random.shuffle(candidates)
    seen = set()
    result: List[dict] = []
    for c in candidates:
        key = (c["title"].lower(), c["artist"].lower())
        if key in seen:
            continue
        seen.add(key)
        result.append(c)
        if len(result) >= max_tracks:
            break
    return result
