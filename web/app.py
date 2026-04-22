#!/usr/bin/env python3
"""
Claudio Web Player - Retro Radio UI
Flask backend for the web interface
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claudio_agent import MusicCurator, Mood
from tts_fallback import TTSManager

app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)
CORS(app)

# Initialize services
curator = MusicCurator(use_netease=True)
tts = TTSManager()

@app.route('/')
def index():
    """Main player page"""
    return render_template('player.html')

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
    app.run(debug=True, port=5000)
