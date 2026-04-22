# GitHub Secrets Setup Guide

This guide explains how to securely store API keys and sensitive information using GitHub Secrets.

## Why Use GitHub Secrets?

- 🔒 **Security**: Secrets are encrypted and never exposed in code
- 🔄 **CI/CD**: Automatically available in GitHub Actions
- 👥 **Collaboration**: Team members can use the same secrets without sharing

## Required Secrets

### 1. TELEGRAM_BOT_TOKEN (Required)

Your Telegram Bot token from @BotFather.

**How to get:**
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Copy the token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. ELEVENLABS_API_KEY (Optional)

For premium voice quality. Free tier has API limitations.

**How to get:**
1. Go to [elevenlabs.io](https://elevenlabs.io)
2. Sign up and subscribe to Starter plan ($5/month) for API access
3. Go to Settings > API Keys
4. Create new key and copy it

### 3. ADMIN_USER_ID (Optional)

Your Telegram user ID for admin commands.

**How to get:**
1. Open Telegram and search for [@userinfobot](https://t.me/userinfobot)
2. Send any message
3. Copy your ID (format: `123456789`)

## Setting Up Secrets

### Method 1: GitHub Web Interface

1. Go to your repository on GitHub
2. Click **Settings** tab
3. In left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret:
   - Name: `TELEGRAM_BOT_TOKEN`
   - Value: your actual token
6. Click **Add secret**
7. Repeat for other secrets

### Method 2: GitHub CLI

```bash
# Install gh CLI if not already: https://cli.github.com/

# Authenticate
github auth login

# Add secrets
gh secret set TELEGRAM_BOT_TOKEN --body "your_bot_token_here"
gh secret set ELEVENLABS_API_KEY --body "your_elevenlabs_key_here"
gh secret set ADMIN_USER_ID --body "your_user_id_here"

# Verify
gh secret list
```

## Using Secrets in Code

Secrets are automatically available as environment variables in GitHub Actions:

```yaml
# .github/workflows/deploy.yml
- name: Create environment file
  run: |
    cat > .env << EOF
    TELEGRAM_BOT_TOKEN=${{ secrets.TELEGRAM_BOT_TOKEN }}
    ELEVENLABS_API_KEY=${{ secrets.ELEVENLABS_API_KEY }}
    ADMIN_USER_ID=${{ secrets.ADMIN_USER_ID }}
    EOF
```

In Python code:
```python
import os

# GitHub Actions automatically injects secrets as env vars
token = os.getenv('TELEGRAM_BOT_TOKEN')
```

## Local Development

For local development, use `.env` file (already in `.gitignore`):

```bash
cp .env.example .env
# Edit .env with your actual keys
```

**Never commit `.env` to Git!**

## Security Best Practices

1. ✅ **DO** use GitHub Secrets for all API keys
2. ✅ **DO** rotate secrets regularly
3. ❌ **DON'T** hardcode secrets in code
4. ❌ **DON'T** commit `.env` files
5. ❌ **DON'T** share secrets in issues/PRs

## Troubleshooting

### Secret not working?
- Check the secret name matches exactly (case-sensitive)
- Verify the workflow has access: `secrets.TELEGRAM_BOT_TOKEN`
- Check repository settings: Settings > Actions > General > Workflow permissions

### Need to update a secret?
1. Go to Settings > Secrets and variables > Actions
2. Find the secret
3. Click **Update**
4. Enter new value

## Questions?

Open an issue if you need help with secrets setup!
