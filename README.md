# 🎵 Claudio - AI Music Curator & DJ

Your personalized AI music radio station. Claudio curates playlists based on your mood, time of day, and natural language requests, with a warm DJ personality.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 🤖 **AI DJ Personality** - Claudio speaks, has personality, and guides your listening experience
- ⏰ **Time-Aware** - Automatically adjusts music style based on time of day
- 💬 **Natural Language** - "Play something for coding", "Relaxing music", "Energizing playlist"
- 🎙️ **Voice Announcements** - System TTS (free) or ElevenLabs (premium)
- 📻 **Retro Radio UI** - Beautiful CLI interface inspired by vintage radios
- 🎵 **Netease Cloud Music** - Access to vast Chinese music library

## 🚀 Quick Start

### Prerequisites

- macOS / Linux / Windows
- Python 3.8+
- Node.js (for Netease Cloud Music API)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/claudio-music-agent.git
cd claudio-music-agent

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your API keys (see [Environment Variables](#environment-variables))

3. **For macOS auto-start**, install the LaunchAgent:
```bash
cd deploy
./install-macos.sh
```

## 🎮 Usage

### CLI Mode (Recommended)

```bash
# Terminal 1: Start Netease Cloud Music API
npx NeteaseCloudMusicApi

# Terminal 2: Start Claudio CLI
./cli.py
```

**Example interaction:**
```
╔══════════════════════════════════════════════════════════╗
║      C L A U D I O   R A D I O                           ║
║     Your AI Music Curator & DJ                           ║
╚══════════════════════════════════════════════════════════╝

🎵 Claudio > Play something for coding

🎙️  Good afternoon! Let me find some focus music for you...

📻 Claudio's Focus Time
Music to help you enter flow state

1. Weightless - Marconi Union (8:00)
2. Tycho - A Walk - Tycho (5:00)
3. Bonobo - Kiara - Bonobo (4:00)
...
```

### Telegram Bot Mode

```bash
# Start the bot
python bot.py
```

Commands:
- `/start` - Start using Claudio
- `/now` - Current playing
- `/next` - Skip to next
- `/prev` - Previous song
- `/status` - Playback status

## 🔧 Environment Variables

Create a `.env` file with the following:

```env
# Required: Telegram Bot Token (get from @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional: ElevenLabs API Key (for premium voice)
# Note: Free tier doesn't support API TTS, need Starter plan ($5/month)
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Optional: Netease Cloud Music API URL
NETEASE_API_URL=http://localhost:3000

# Optional: Admin user ID for Telegram
ADMIN_USER_ID=your_telegram_user_id
```

### GitHub Secrets (for CI/CD)

If deploying via GitHub Actions, add these secrets:

1. Go to **Settings > Secrets and variables > Actions**
2. Add the following secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `ELEVENLABS_API_KEY` (optional)
   - `ADMIN_USER_ID` (optional)

## 🎙️ Voice Options

### Option 1: System TTS (Free, Default)

Uses macOS `say` command or Linux `espeak`:
- **Chinese**: Ting-Ting (female, gentle)
- **English**: Samantha (female, clear)
- No cost, no network required

### Option 2: ElevenLabs (Premium)

High-quality AI voices:
- Subscribe at [elevenlabs.io](https://elevenlabs.io) (Starter plan $5/month)
- Add API key to `.env`
- Automatically detected and used

### Toggle TTS

In CLI mode:
```
🎵 Claudio > tts off    # Disable voice
🎵 Claudio > tts on     # Enable voice
```

## 📁 Project Structure

```
claudio-music-agent/
├── cli.py                 # CLI interface
├── bot.py                 # Telegram bot
├── claudio_agent.py       # Core music curation logic
├── netease_api.py         # Netease Cloud Music API wrapper
├── tts_service.py         # ElevenLabs TTS
├── tts_fallback.py        # System TTS fallback
├── config.yaml            # Configuration
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── deploy/
│   ├── install-macos.sh   # macOS auto-start installer
│   ├── com.claudio.bot.plist  # LaunchAgent config
│   └── claudio.service    # systemd service (Linux)
└── README.md
```

## 🛠️ CLI Commands

| Command | Description |
|---------|-------------|
| `now`, `n` | Show current playing |
| `next`, `skip`, `s` | Next song |
| `prev`, `p` | Previous song |
| `pause`, `stop` | Pause playback |
| `play`, `resume` | Resume playback |
| `tts on/off` | Toggle voice announcements |
| `mood <mood>` | Play by mood (focus/relax/sleep/energize/workout) |
| `help`, `h`, `?` | Show help |
| `quit`, `q` | Exit |

## 🎯 Natural Language Examples

- "Play something for coding"
- "Relaxing music for work"
- "Energizing playlist for workout"
- "Sleep music, 30 minutes"
- "Chinese songs for running"
- "Jazz for evening relaxation"

## 🚀 Deployment

### macOS (LaunchAgent)

Auto-start on boot:
```bash
cd deploy
./install-macos.sh
```

Manage:
```bash
launchctl start com.claudio.bot     # Start
launchctl stop com.claudio.bot      # Stop
launchctl unload ~/Library/LaunchAgents/com.claudio.bot.plist  # Uninstall
```

### Linux (systemd)
```bash
cd deploy
sudo ./install.sh

sudo systemctl start claudio    # Start
sudo systemctl stop claudio     # Stop
sudo journalctl -u claudio -f   # View logs
```

## 📝 Configuration

Edit `config.yaml`:

```yaml
ai:
  provider: "anthropic"  # or "moonshot" for Kimi
  model: "claude-3-5-sonnet-20241022"

music_sources:
  netease:
    enabled: true
    api_base: "http://localhost:3000"

tts:
  provider: "system"  # "system" or "elevenlabs"
  elevenlabs_voice: "21m00Tcm4TlvDq8ikWAM"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- [Binaryify/NeteaseCloudMusicApi](https://github.com/Binaryify/NeteaseCloudMusicApi) - Netease Cloud Music API
- [ElevenLabs](https://elevenlabs.io) - Premium TTS service
- Inspired by the original [Claudio](https://www.xiaohongshu.com/) project

---

**Enjoy your AI DJ!** 🎵
