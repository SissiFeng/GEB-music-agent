"""Moonshot (Kimi) wrapper for DJ personality text generation.

Uses the OpenAI SDK against Moonshot's compatible endpoint. If the API key is
missing or the call fails for any reason, callers receive None and are expected
to fall back to their existing template logic.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

logger = logging.getLogger(__name__)

_MOONSHOT_BASE_URL = "https://api.moonshot.ai/v1"
_DEFAULT_MODEL = "moonshot-v1-8k"
_DEFAULT_TIMEOUT = 10.0


class KimiClient:
    """Minimal chat wrapper with graceful degradation."""

    def __init__(self, model: str = _DEFAULT_MODEL, timeout: float = _DEFAULT_TIMEOUT):
        self.model = model
        self.timeout = timeout
        self._client = None

        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            return
        if OpenAI is None:
            logger.warning("openai package not installed; Kimi disabled")
            return

        self._client = OpenAI(api_key=api_key, base_url=_MOONSHOT_BASE_URL)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def chat(
        self,
        system: str,
        user: str,
        max_tokens: int = 200,
        temperature: float = 0.8,
    ) -> Optional[str]:
        if self._client is None:
            return None
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout,
            )
            text = resp.choices[0].message.content
            return text.strip() if text else None
        except Exception as exc:  # noqa: BLE001 - any error should degrade
            logger.warning("Kimi call failed, falling back: %s", exc)
            return None

    def generate_playlist(
        self,
        mood: str,
        length: int = 10,
        seed_tracks: Optional[List[dict]] = None,
        recent_plays: Optional[List[dict]] = None,
        weather: Optional[dict] = None,
        exploration: str = "medium",
        context: Optional[str] = None,
    ) -> List[dict]:
        """Return [{title, artist}, ...] shaped by mood + optional seeds/weather/history.

        The prompt explicitly demands freshness — 2-3 unfamiliar picks per call, no
        duplicates with recent_plays, cross-era/cross-language mixing when the mood
        allows. Seed tracks coming from trending Netease playlists give Kimi a
        "what's in the air today" lens so results drift daily.
        """
        if self._client is None:
            return []

        now = datetime.now()
        ctx = context or f"{now.strftime('%A')} {now.strftime('%H:%M')}"

        exploration_directive = {
            "low":    "Stay close to well-known songs. Avoid obscure B-sides.",
            "medium": "Balance 60% well-known songs with 40% thoughtful discoveries.",
            "high":   "Lean into discovery — at least half the list should be less-heard tracks. Cross languages and eras freely if the mood allows.",
        }.get(exploration, "Balance 60% well-known songs with 40% thoughtful discoveries.")

        system = (
            "You are Claudio, a music curator with wide, eclectic taste running a personal radio station. "
            "Your listener is tired of predictable playlists — surprise them.\n\n"
            "Hard rules:\n"
            "  1. Output ONLY a JSON array. No prose, no markdown, no code fences.\n"
            "  2. Every song must be a real track that exists on YouTube. Don't invent.\n"
            "  3. Do not repeat songs the listener says they just heard.\n"
            "  4. At least 2-3 picks must be genuine discoveries — songs they likely haven't heard.\n"
            "  5. Mix artists unless the mood begs for a deep-dive on one.\n"
            "  6. Mix eras (1960s–today) when the mood allows — don't cluster one decade.\n"
            'Entry shape: {"title": "...", "artist": "..."}'
        )

        blocks: List[str] = []
        blocks.append(f"MOOD: {mood}")
        blocks.append(f"LENGTH: exactly {length} songs")
        blocks.append(f"CONTEXT: {ctx}")
        blocks.append(f"EXPLORATION: {exploration_directive}")

        if weather:
            wline = []
            if weather.get("city"):        wline.append(weather["city"])
            if weather.get("description"): wline.append(weather["description"])
            if weather.get("temp_c") is not None:
                wline.append(f"{round(weather['temp_c'])}°C")
            if wline:
                blocks.append(
                    "WEATHER: " + ", ".join(wline) +
                    " — let this colour the mood (rainy → slower/inward, sunny → brighter, cold → warmer tones)."
                )

        if seed_tracks:
            seed_lines = []
            for s in seed_tracks[:12]:
                title = s.get("title", "")
                artist = s.get("artist", "")
                cat = s.get("category", "")
                seed_lines.append(f"  - {title} — {artist}" + (f"  [{cat}]" if cat else ""))
            blocks.append(
                "TRENDING RIGHT NOW (sampled from Netease playlists — use as inspiration, "
                "pick from these OR suggest similar-vibe tracks):\n" + "\n".join(seed_lines)
            )

        if recent_plays:
            recent_lines = []
            for r in recent_plays[:30]:
                recent_lines.append(f"  - {r.get('title','')} — {r.get('artist','')}")
            blocks.append(
                "RECENTLY PLAYED (do not repeat any of these):\n" + "\n".join(recent_lines)
            )

        blocks.append("\nOutput the JSON array now.")

        raw = self.chat(
            system=system,
            user="\n\n".join(blocks),
            max_tokens=3500,
            temperature=0.95,
        )
        if not raw:
            return []

        parsed = _parse_playlist_json(raw)
        if not parsed:
            logger.warning("Kimi returned unparseable playlist; first 200 chars: %s", raw[:200])
        return parsed[:length]


def _parse_playlist_json(raw: str) -> List[dict]:
    """Best-effort JSON array extraction tolerating code fences, stray prose, and truncation."""
    text = raw.strip()

    # Strip markdown fences if Kimi added them anyway.
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # First try: the clean case — a full [...] block.
    match = re.search(r"\[.*\]", text, flags=re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return _normalize(data)
        except json.JSONDecodeError:
            pass

    # Fallback: truncated / malformed — extract each {…} object independently.
    # This rescues most output when max_tokens cut off mid-array.
    objs: List[dict] = []
    for m in re.finditer(r"\{[^{}]*\}", text, flags=re.DOTALL):
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                objs.append(obj)
        except json.JSONDecodeError:
            continue
    return _normalize(objs) if objs else []


def _normalize(items: List[dict]) -> List[dict]:
    out: List[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        artist = str(item.get("artist") or "").strip()
        if title:
            out.append({"title": title, "artist": artist})
    return out
