// Claudio Radio - Web Player JavaScript

class ClaudioPlayer {
    constructor() {
        this.audio = document.getElementById('audioPlayer');
        this.isPlaying = false;
        this.currentPlaylist = [];
        this.currentIndex = 0;
        
        this.initElements();
        this.initEventListeners();
        this.startClock();
        this.loadStatus();
    }
    
    initElements() {
        // Clock
        this.clockEl = document.getElementById('clock');
        this.dateEl = document.getElementById('date');
        
        // ON AIR
        this.onAirEl = document.getElementById('onAir');
        
        // Track info
        this.trackTitleEl = document.getElementById('trackTitle');
        this.trackArtistEl = document.getElementById('trackArtist');
        
        // Progress
        this.progressFillEl = document.getElementById('progressFill');
        this.currentTimeEl = document.getElementById('currentTime');
        this.totalTimeEl = document.getElementById('totalTime');
        
        // Controls
        this.playBtn = document.getElementById('playBtn');
        this.prevBtn = document.getElementById('prevBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.playIcon = document.getElementById('playIcon');
        this.pauseIcon = document.getElementById('pauseIcon');
        
        // DJ Message
        this.djMessageEl = document.getElementById('djMessage');
        
        // Chat
        this.chatInput = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.chatHistory = document.getElementById('chatHistory');
        
        // Playlist
        this.playlistContent = document.getElementById('playlistContent');
        this.playlistCount = document.getElementById('playlistCount');
    }
    
    initEventListeners() {
        // Play/Pause
        this.playBtn.addEventListener('click', () => this.togglePlay());
        
        // Previous/Next
        this.prevBtn.addEventListener('click', () => this.previous());
        this.nextBtn.addEventListener('click', () => this.next());
        
        // Chat
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Audio events
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('ended', () => this.next());
    }
    
    startClock() {
        const updateClock = () => {
            const now = new Date();
            
            // Pixel clock format: HH:MM:SS
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            this.clockEl.textContent = `${hours}:${minutes}:${seconds}`;
            
            // Date
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            this.dateEl.textContent = now.toLocaleDateString('en-US', options);
        };
        
        updateClock();
        setInterval(updateClock, 1000);
    }
    
    togglePlay() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    play() {
        this.isPlaying = true;
        this.onAirEl.classList.add('active');
        this.playIcon.style.display = 'none';
        this.pauseIcon.style.display = 'block';
        
        if (this.audio.src) {
            this.audio.play().catch(e => console.log('Audio play failed:', e));
        }
    }
    
    pause() {
        this.isPlaying = false;
        this.onAirEl.classList.remove('active');
        this.playIcon.style.display = 'block';
        this.pauseIcon.style.display = 'none';
        this.audio.pause();
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addChatMessage(message, 'user');
        this.chatInput.value = '';
        
        // Show loading
        this.djMessageEl.textContent = 'Thinking...';
        
        try {
            // Call API to create playlist
            const response = await fetch('/api/playlist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: message })
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.djMessageEl.textContent = 'Sorry, something went wrong.';
                return;
            }
            
            // Update DJ message
            this.djMessageEl.textContent = data.dj_message;
            
            // Update playlist
            this.updatePlaylist(data.playlist);
            
            // Add DJ response to chat
            this.addChatMessage(data.dj_message, 'dj');
            
            // Play first song
            if (data.playlist.songs.length > 0) {
                this.playSong(0);
            }
            
        } catch (error) {
            console.error('Error:', error);
            this.djMessageEl.textContent = 'Sorry, I\'m having trouble connecting.';
        }
    }
    
    addChatMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `chat-message ${sender}`;
        div.textContent = text;
        this.chatHistory.appendChild(div);
        this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
    }
    
    updatePlaylist(playlist) {
        this.currentPlaylist = playlist.songs;
        this.playlistCount.textContent = `${playlist.songs.length} songs`;
        
        if (playlist.songs.length === 0) {
            this.playlistContent.innerHTML = '<div class="empty-playlist">No songs found.</div>';
            return;
        }
        
        this.playlistContent.innerHTML = playlist.songs.map((song, index) => `
            <div class="playlist-item ${index === 0 ? 'active' : ''}" data-index="${index}">
                <span class="playlist-number">${index + 1}</span>
                <div class="playlist-info">
                    <div class="playlist-title">${song.title}</div>
                    <div class="playlist-artist">${song.artist}</div>
                </div>
                <span class="playlist-duration">${song.duration_formatted}</span>
            </div>
        `).join('');
        
        // Add click handlers
        this.playlistContent.querySelectorAll('.playlist-item').forEach(item => {
            item.addEventListener('click', () => {
                const index = parseInt(item.dataset.index);
                this.playSong(index);
            });
        });
    }
    
    playSong(index) {
        if (index < 0 || index >= this.currentPlaylist.length) return;
        
        this.currentIndex = index;
        const song = this.currentPlaylist[index];
        
        // Update UI
        this.trackTitleEl.textContent = song.title;
        this.trackArtistEl.textContent = song.artist;
        this.totalTimeEl.textContent = song.duration_formatted;
        
        // Update playlist active state
        this.playlistContent.querySelectorAll('.playlist-item').forEach((item, i) => {
            item.classList.toggle('active', i === index);
        });
        
        // Note: Actual audio playback would require song URLs from Netease API
        // For now, we just update the UI
        this.play();
    }
    
    next() {
        if (this.currentPlaylist.length === 0) return;
        
        const nextIndex = (this.currentIndex + 1) % this.currentPlaylist.length;
        this.playSong(nextIndex);
    }
    
    previous() {
        if (this.currentPlaylist.length === 0) return;
        
        const prevIndex = (this.currentIndex - 1 + this.currentPlaylist.length) % this.currentPlaylist.length;
        this.playSong(prevIndex);
    }
    
    updateProgress() {
        if (!this.audio.duration) return;
        
        const progress = (this.audio.currentTime / this.audio.duration) * 100;
        this.progressFillEl.style.width = `${progress}%`;
        
        const current = this.formatTime(this.audio.currentTime);
        const total = this.formatTime(this.audio.duration);
        
        this.currentTimeEl.textContent = current;
        this.totalTimeEl.textContent = total;
    }
    
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.playing && data.song) {
                this.trackTitleEl.textContent = data.song.title;
                this.trackArtistEl.textContent = data.song.artist;
            }
        } catch (error) {
            console.log('Could not load status');
        }
    }
}

// Initialize player when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.player = new ClaudioPlayer();
});
