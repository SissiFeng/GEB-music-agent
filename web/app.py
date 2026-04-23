#!/usr/bin/env python3
"""
Claudio Web Player - Retro Radio UI
Flask backend for the web interface
"""

from flask import Flask, render_template, jsonify, request, send_from_directory, abort
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import json
import logging
import os
import sys
import threading
import requests

# Add parent directory to path
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(str(PROJECT_ROOT))

from claudio_agent import MusicCurator, Mood
from tts_fallback import TTSManager
from kimi_client import KimiClient
from youtube_resolver import resolve_via_youtube
from netease_seeds import fetch_playlist_seeds
from weather import get_weather

logger = logging.getLogger(__name__)

app = Flask(__name__,
    template_folder='templates',
    static_folder='static'
)
CORS(app)

# Initialize services
curator = MusicCurator(use_netease=True)
tts = TTSManager()

NETEASE_BASE = os.getenv("NETEASE_API_URL", "http://localhost:3000")
SCHEDULE_PATH = Path(__file__).parent / "schedule.json"
AUDIO_CACHE = PROJECT_ROOT / "audio_cache"

# Playlist cache: one generated list per (slot_id, YYYY-MM-DD).
# Kimi runs at most once per slot per day.
PLAYLIST_CACHE_PATH = Path(__file__).parent / "playlist_cache.json"
# History of actually-played tracks so Kimi can avoid repeats.
HISTORY_PATH = Path(__file__).parent / "played_history.json"
HISTORY_LIMIT = 120  # keep last ~120 tracks
_cache_lock = threading.Lock()
_history_lock = threading.Lock()

# Kimi client reused across requests for the /resolve endpoint.
playlist_kimi = KimiClient()


def load_schedule():
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_cache() -> dict:
    if not PLAYLIST_CACHE_PATH.exists():
        return {}
    try:
        with open(PLAYLIST_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    with open(PLAYLIST_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _cache_key(slot_id: str) -> str:
    return f"{slot_id}|{datetime.now().strftime('%Y-%m-%d')}"


def _get_cached_tracks(slot_id: str) -> list | None:
    cache = _load_cache()
    entry = cache.get(_cache_key(slot_id))
    if not entry:
        return None
    return entry.get("tracks") or None


def _set_cached_tracks(slot_id: str, tracks: list) -> None:
    with _cache_lock:
        cache = _load_cache()
        cache[_cache_key(slot_id)] = {
            "tracks": tracks,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }
        # Prune entries older than 7 days to keep file small.
        cutoff = datetime.now().timestamp() - 7 * 86400
        cache = {
            k: v for k, v in cache.items()
            if datetime.fromisoformat(v.get("generated_at", datetime.now().isoformat())).timestamp() >= cutoff
        }
        _save_cache(cache)


def _load_history() -> list:
    if not HISTORY_PATH.exists():
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _append_history(tracks: list) -> None:
    """Append tracks to played history, keep newest HISTORY_LIMIT."""
    if not tracks:
        return
    with _history_lock:
        history = _load_history()
        ts = datetime.now().isoformat(timespec="seconds")
        for t in tracks:
            history.append({
                "title": t.get("title"),
                "artist": t.get("artist"),
                "played_at": ts,
            })
        history = history[-HISTORY_LIMIT:]
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)


def _recent_plays_for_prompt(days: int = 7, limit: int = 40) -> list:
    """Return recent plays within N days as {title, artist} list (deduped)."""
    history = _load_history()
    cutoff = datetime.now().timestamp() - days * 86400
    seen = set()
    out = []
    # Walk newest-first so dedup keeps most recent occurrence
    for h in reversed(history):
        try:
            ts = datetime.fromisoformat(h.get("played_at", "")).timestamp()
        except Exception:
            continue
        if ts < cutoff:
            continue
        title = (h.get("title") or "").strip()
        artist = (h.get("artist") or "").strip()
        key = (title.lower(), artist.lower())
        if not title or key in seen:
            continue
        seen.add(key)
        out.append({"title": title, "artist": artist})
        if len(out) >= limit:
            break
    return out


def resolve_song(title: str, artist: str):
    """Search netease and return the first candidate with a real playable URL.

    Netease often returns a fresh re-upload ID as the top search result but only
    older IDs hold public MP3 URLs, so we scan the top results and pick the first
    one whose /song/url actually returns a url (not just freeTrialInfo).
    """
    keywords = f"{title} {artist}".strip()
    try:
        r = requests.get(
            f"{NETEASE_BASE}/search",
            params={"keywords": keywords, "limit": 10},
            timeout=5,
        )
        candidates = r.json().get("result", {}).get("songs", []) or []
    except Exception:
        return None

    want_artist = (artist or "").strip().lower()

    def artist_matches(candidate) -> bool:
        if not want_artist:
            return True
        names = [a.get("name", "").lower() for a in candidate.get("artists", [])]
        for n in names:
            if not n:
                continue
            if n in want_artist or want_artist in n:
                return True
        return False

    for song in candidates:
        song_id = song.get("id")
        if not song_id:
            continue
        # Skip obvious false-positive matches that share title but not artist.
        if not artist_matches(song):
            continue
        try:
            ur = requests.get(
                f"{NETEASE_BASE}/song/url",
                params={"id": song_id},
                timeout=5,
            )
            data = ur.json().get("data", []) or []
        except Exception:
            continue

        if not data or not data[0].get("url"):
            continue
        # Skip VIP-only previews that only return freeTrialInfo
        if data[0].get("freeTrialInfo"):
            continue

        return {
            "title": title,
            "artist": artist,
            "netease_title": song.get("name"),
            "netease_artist": ", ".join(a.get("name", "") for a in song.get("artists", [])),
            "id": song_id,
            "url": data[0]["url"],
            "duration_ms": song.get("duration", 0),
            "fee": data[0].get("fee", 0),
        }

    return None


@app.route('/')
def index():
    """Schedule view (new Phase 2 home)."""
    return render_template('schedule.html')


@app.route('/player')
def legacy_player():
    """Original single-player view (kept as backup)."""
    return render_template('player.html')


@app.route('/api/schedule')
def api_schedule():
    """Return the user's daily schedule."""
    return jsonify(load_schedule())


@app.route('/api/schedule/<slot_id>/resolve', methods=['POST'])
def api_resolve_slot(slot_id):
    """Resolve a slot to playable tracks using the mood/seeds/weather pipeline.

    Flow:
      cache hit -> return cached (unless ?refresh=1)
      else:
        1. Fetch trending netease playlist tracks for slot.seed_categories
        2. Fetch current weather (if OPENWEATHER_API_KEY set)
        3. Load recent play history (last 7 days)
        4. Ask Kimi with mood + seeds + weather + history
        5. yt-dlp parallel resolve each suggestion
        6. Append successful tracks to history, cache result
    """
    force_regen = request.args.get("refresh") in {"1", "true", "yes"}

    schedule = load_schedule()
    slot = next((s for s in schedule.get("slots", []) if s.get("id") == slot_id), None)
    if slot is None:
        return jsonify({"error": "slot not found"}), 404

    mood = slot.get("mood") or slot.get("vibe")  # accept legacy field name
    if not mood:
        # Legacy fixed-song list path
        songs = slot.get("songs", [])
        if not songs:
            return jsonify({"error": "slot has no mood and no songs"}), 400
        with ThreadPoolExecutor(max_workers=min(8, max(1, len(songs)))) as ex:
            resolved = list(ex.map(
                lambda s: resolve_song(s.get("title", ""), s.get("artist", "")),
                songs,
            ))
        tracks = [r for r in resolved if r]
        missing = [songs[i] for i, r in enumerate(resolved) if r is None]
        return jsonify({"slot": slot, "tracks": tracks, "missing": missing, "source": "netease"})

    # mood-mode path
    if not force_regen:
        cached = _get_cached_tracks(slot_id)
        if cached:
            return jsonify({
                "slot": slot,
                "tracks": cached,
                "missing": [],
                "source": "cache",
            })

    if not playlist_kimi.enabled:
        return jsonify({"error": "Kimi disabled — set MOONSHOT_API_KEY"}), 503

    seeds = []
    seed_categories = slot.get("seed_categories") or []
    if seed_categories:
        try:
            seeds = fetch_playlist_seeds(seed_categories, max_tracks=12)
        except Exception as exc:
            logger.warning("netease seed fetch failed: %s", exc)
            seeds = []

    weather = None
    try:
        weather = get_weather()
    except Exception as exc:
        logger.warning("weather fetch failed: %s", exc)

    recent = _recent_plays_for_prompt(days=7, limit=40)

    suggestions = playlist_kimi.generate_playlist(
        mood=mood,
        length=int(slot.get("length", 10)),
        seed_tracks=seeds,
        recent_plays=recent,
        weather=weather,
        exploration=slot.get("exploration", "medium"),
    )
    if not suggestions:
        return jsonify({
            "slot": slot,
            "tracks": [],
            "missing": [],
            "error": "Kimi did not return a valid playlist",
        }), 502

    with ThreadPoolExecutor(max_workers=min(6, max(1, len(suggestions)))) as ex:
        resolved = list(ex.map(
            lambda s: resolve_via_youtube(s["title"], s.get("artist", "")),
            suggestions,
        ))
    tracks = [r for r in resolved if r]
    missing = [suggestions[i] for i, r in enumerate(resolved) if r is None]

    if tracks:
        _set_cached_tracks(slot_id, tracks)
        _append_history(tracks)

    return jsonify({
        "slot": slot,
        "tracks": tracks,
        "missing": missing,
        "source": "generated",
        "kimi_suggested": len(suggestions),
        "context": {
            "seeds_used": len(seeds),
            "recent_avoided": len(recent),
            "weather": weather,
        },
    })


@app.route('/api/weather')
def api_weather():
    """Return current weather from wttr.in, or {} if unavailable."""
    try:
        w = get_weather()
    except Exception:
        w = None
    return jsonify(w or {})


@app.route('/api/extract', methods=['POST'])
def api_extract():
    """Extract songs from freeform pasted text, resolve via YouTube, return tracks."""
    if not playlist_kimi.enabled:
        return jsonify({"error": "Kimi disabled — set MOONSHOT_API_KEY"}), 503

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "no text provided"}), 400
    if len(text) > 8000:
        return jsonify({"error": "text too long (max 8000 chars)"}), 413

    songs = playlist_kimi.extract_songs_from_text(text)
    if not songs:
        return jsonify({"songs": [], "tracks": [], "missing": [], "error": "nothing identifiable extracted"}), 200

    with ThreadPoolExecutor(max_workers=min(6, max(1, len(songs)))) as ex:
        resolved = list(ex.map(
            lambda s: resolve_via_youtube(s.get("title", ""), s.get("artist", "")),
            songs,
        ))
    tracks = [r for r in resolved if r]
    missing = [songs[i] for i, r in enumerate(resolved) if r is None]

    if tracks:
        _append_history(tracks)

    return jsonify({
        "songs": songs,
        "tracks": tracks,
        "missing": missing,
        "source": "pasted",
    })


@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """Serve TTS-generated audio files from the shared cache dir."""
    target = AUDIO_CACHE / filename
    if not target.exists():
        abort(404)
    return send_from_directory(str(AUDIO_CACHE), filename)


@app.route('/sw.js')
def service_worker():
    """Serve the service worker from root so its scope covers the whole site."""
    response = send_from_directory(app.static_folder, 'sw.js', mimetype='application/javascript')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route('/api/status')
def get_status():
    """Get current playback status"""
    song = curator.get_current_song()
    playlist = curator.current_playlist
    
    if song:
        return jsonify({
            'playing': True,
            'song': {
                'title': song.title,
                'artist': song.artist,
                'album': song.album,
                'duration_ms': song.duration_ms,
                'cover_url': ''  # TODO: Add cover
            },
            'playlist': playlist.name if playlist else None,
            'progress': 35  # TODO: Real progress
        })
    
    return jsonify({'playing': False})

@app.route('/api/playlist', methods=['POST'])
def create_playlist():
    """Create a new playlist from natural language"""
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Create playlist
    playlist = curator.create_playlist(query)
    
    # Generate DJ intro
    context = {'user_request': query}
    dj_message = curator.generate_dj_intro(context)
    
    # Convert songs to dict
    songs_data = []
    for song in playlist.songs:
        songs_data.append({
            'title': song.title,
            'artist': song.artist,
            'album': song.album,
            'duration_ms': song.duration_ms,
            'duration_formatted': format_duration(song.duration_ms)
        })
    
    return jsonify({
        'playlist': {
            'name': playlist.name,
            'description': playlist.description,
            'songs': songs_data,
            'total_duration': format_duration(playlist.total_duration_ms)
        },
        'dj_message': dj_message
    })

@app.route('/api/speak', methods=['POST'])
def speak():
    """Generate TTS audio"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Generate audio
    audio_path = tts.speak(text, language='auto')
    
    if audio_path:
        return jsonify({
            'success': True,
            'audio_url': f'/audio/{os.path.basename(audio_path)}'
        })
    
    return jsonify({'error': 'TTS generation failed'}), 500

@app.route('/api/control/<action>', methods=['POST'])
def control(action):
    """Playback controls"""
    if action == 'next':
        song = curator.next_song()
        if song:
            intro = curator.generate_song_intro(song)
            return jsonify({
                'success': True,
                'song': {
                    'title': song.title,
                    'artist': song.artist,
                    'duration_formatted': format_duration(song.duration_ms)
                },
                'intro': intro
            })
    
    elif action == 'prev':
        song = curator.previous_song()
        if song:
            intro = curator.generate_song_intro(song)
            return jsonify({
                'success': True,
                'song': {
                    'title': song.title,
                    'artist': song.artist,
                    'duration_formatted': format_duration(song.duration_ms)
                },
                'intro': intro
            })
    
    return jsonify({'error': 'Action failed'}), 400

def format_duration(ms):
    """Format milliseconds to MM:SS"""
    minutes = ms // 60000
    seconds = (ms // 1000) % 60
    return f"{minutes}:{seconds:02d}"

if __name__ == '__main__':
    app.run(debug=True, port=5555, host='0.0.0.0')
