# 🎵 Claudio 快速启动指南

## 环境要求

- macOS / Linux / Windows
- Python 3.8+
- Node.js (用于网易云音乐 API)

## 1. 安装依赖

```bash
cd claudio-music-agent
pip install -r requirements.txt
```

## 2. 配置环境变量

```bash
# 复制模板
cp .env.example .env

# 编辑 .env，填入你的 Telegram Bot Token
# TELEGRAM_BOT_TOKEN=从 @BotFather 获取
```

## 3. 启动方式

### 方式一：CLI 交互（推荐）

**步骤 1：启动网易云音乐 API**
```bash
# 新终端窗口
npx NeteaseCloudMusicApi
```

**步骤 2：启动 CLI**
```bash
# 另一个终端窗口
cd claudio-music-agent
./cli.py
```

**使用示例：**
```
🎵 Claudio > 我想听点适合写代码的歌

🎙️  下午好，我是 Claudio...

📻 Claudio 的专注时光
1. 《夜曲》- 周杰伦
2. 《Weightless》- Marconi Union
...
```

### 方式二：Telegram Bot

```bash
# 1. 启动网易云音乐 API
npx NeteaseCloudMusicApi

# 2. 启动 Bot
python bot.py
```

## 4. TTS 配置

### 方案 A：系统 TTS（免费，macOS 推荐）

无需配置，自动使用 macOS `say` 命令。

支持嗓音：
- 中文：Ting-Ting（女声）
- 英文：Samantha（女声）

### 方案 B：ElevenLabs（高质量，需付费订阅）

**⚠️ 重要：** ElevenLabs 免费版（10k credits/月）**不能**使用标准 API 生成语音，需要升级到付费计划（$5/月起）。

**付费版优势：**
- 高质量 AI 嗓音
- 多语言支持
- 自定义嗓音克隆

**配置方法：**
1. 注册 https://elevenlabs.io
2. 订阅付费计划（Starter $5/月）
3. 获取 API Key
4. 添加到 `.env`：
```
ELEVENLABS_API_KEY=你的_api_key
```

### 方案 C：关闭 TTS

在 CLI 中输入：
```
🎵 Claudio > tts off
```

## 5. 自动启动（macOS）

```bash
cd deploy
./install-macos.sh
```

启动命令：
```bash
launchctl start com.claudio.bot
```

## 6. 常见问题

### Q: 网易云音乐 API 启动失败？
```bash
# 安装 npx（如果未安装）
npm install -g npx

# 或使用 npx 直接运行
npx NeteaseCloudMusicApi
```

### Q: TTS 不工作？
- 检查系统：macOS 使用 `say`，Linux 需要 `espeak`
- 或关闭 TTS：`tts off`
- 或使用 ElevenLabs（需付费）

### Q: 如何获取 Telegram Bot Token？
1. 打开 Telegram，搜索 @BotFather
2. 发送 `/newbot`
3. 按提示创建 Bot
4. 复制 Token 到 `.env`

## 7. CLI 命令

| 命令 | 说明 |
|------|------|
| `now`, `n` | 当前播放 |
| `next`, `s` | 下一首 |
| `prev`, `p` | 上一首 |
| `tts on/off` | 开关语音 |
| `mood focus` | 专注模式 |
| `mood relax` | 放松模式 |
| `quit`, `q` | 退出 |

## 8. 自然语言示例

- "我想听点适合写代码的歌"
- "给我一些放松的音乐"
- "提神醒脑的歌单"
- "助眠音乐，30分钟"
- "适合运动的中文歌"

---

**现在就开始享受你的 AI DJ 吧！** 🎵
