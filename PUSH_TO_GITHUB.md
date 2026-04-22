# Push to GitHub

## Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `claudio-music-agent` (or your preferred name)
3. Make it **Private** (recommended for API keys)
4. Don't initialize with README (we already have one)
5. Click **Create repository**

## Step 2: Add Remote and Push

Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/claudio-music-agent.git

# Push to GitHub
git branch -M main
git push -u origin main
```

Or use SSH (if you have SSH keys set up):

```bash
git remote add origin git@github.com:YOUR_USERNAME/claudio-music-agent.git
git branch -M main
git push -u origin main
```

## Step 3: Add GitHub Secrets

After pushing, add your secrets:

1. Go to: `https://github.com/YOUR_USERNAME/claudio-music-agent/settings/secrets/actions`
2. Click **New repository secret**
3. Add these secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `ELEVENLABS_API_KEY` (optional)
   - `ADMIN_USER_ID` (optional)

See [GITHUB_SECRETS.md](GITHUB_SECRETS.md) for detailed instructions.

## Step 4: Deploy on Office Mac

On your office Mac:

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/claudio-music-agent.git
cd claudio-music-agent

# Create .env file
cp .env.example .env
# Edit .env with your API keys

# Install and start
pip install -r requirements.txt
npx NeteaseCloudMusicApi &
./cli.py
```

Or use auto-start:

```bash
cd deploy
./install-macos.sh
launchctl start com.claudio.bot
```

## Done! 🎵

Your Claudio AI DJ is now on GitHub and ready to use!
