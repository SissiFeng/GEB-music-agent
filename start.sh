#!/bin/bash
# Claudio AI DJ 启动脚本

echo "🎵 启动 Claudio AI 音乐电台..."

# 检查环境变量
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ 错误: 请设置 TELEGRAM_BOT_TOKEN 环境变量"
    echo "   export TELEGRAM_BOT_TOKEN='你的BotToken'"
    exit 1
fi

# 检查 Python 依赖
echo "📦 检查依赖..."
pip install -q -r requirements.txt

# 启动网易云音乐 API（如果可用）
if command -v npx &> /dev/null; then
    echo "🎵 启动网易云音乐 API..."
    npx NeteaseCloudMusicApi &
    NETEASE_PID=$!
    echo "   网易云音乐 API PID: $NETEASE_PID"
    sleep 3
fi

# 启动 Bot
echo "🤖 启动 Telegram Bot..."
python bot.py

# 清理
if [ ! -z "$NETEASE_PID" ]; then
    echo "🛑 停止网易云音乐 API..."
    kill $NETEASE_PID 2>/dev/null
fi

echo "👋 Claudio 已停止"
