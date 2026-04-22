"""Current-weather lookup via wttr.in — zero config, no API key, auto-geolocates.

Returns None gracefully on any failure so callers can skip the weather line
in their prompt without error handling.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_CACHE: dict = {"weather": None, "weather_at": 0.0}
_WEATHER_TTL_SEC = 1800  # 30 min — plenty fresh for mood-setting
_WTTR_ENDPOINT = "https://wttr.in/?format=j1"


def get_weather() -> Optional[dict]:
    """Return {city, region, country, description, main, temp_c, humidity, wind_kmh} or None."""
    now = time.time()
    cached = _CACHE.get("weather")
    if cached and (now - _CACHE["weather_at"]) < _WEATHER_TTL_SEC:
        return cached

    try:
        r = requests.get(_WTTR_ENDPOINT, timeout=8, headers={"User-Agent": "curl/claudio"})
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        logger.debug("wttr.in fetch failed: %s", exc)
        return None

    try:
        loc  = (data.get("nearest_area") or [{}])[0]
        cur  = (data.get("current_condition") or [{}])[0]
        desc = (cur.get("weatherDesc") or [{}])[0].get("value", "")
        weather = {
            "city":        _wttr_value(loc.get("areaName")),
            "region":      _wttr_value(loc.get("region")),
            "country":     _wttr_value(loc.get("country")),
            "description": desc.strip(),
            "main":        desc.strip().split(",")[0],
            "temp_c":      _to_float(cur.get("temp_C")),
            "humidity":    _to_float(cur.get("humidity")),
            "wind_kmh":    _to_float(cur.get("windspeedKmph")),
        }
    except Exception as exc:  # noqa: BLE001
        logger.debug("wttr.in parse failed: %s", exc)
        return None

    _CACHE["weather"] = weather
    _CACHE["weather_at"] = now
    return weather


def _wttr_value(field) -> Optional[str]:
    """wttr.in nests single-value strings as [{'value': 'X'}]."""
    if isinstance(field, list) and field:
        return field[0].get("value")
    return None


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def weather_line(w: Optional[dict]) -> str:
    """Compact one-liner for prompts; empty string if no data."""
    if not w:
        return ""
    parts = []
    if w.get("city"):
        parts.append(w["city"])
    if w.get("description"):
        parts.append(w["description"])
    if w.get("temp_c") is not None:
        parts.append(f"{round(w['temp_c'])}°C")
    return ", ".join(parts)
