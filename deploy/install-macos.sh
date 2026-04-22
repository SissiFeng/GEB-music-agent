#!/bin/bash
# Claudio AI DJ macOS 自动部署脚本

set -e

echo "🎵 Claudio AI DJ macOS 部署脚本"
echo "================================="

# 配置
INSTALL_DIR="$HOME/.claudio"
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="com.claudio.bot.plist"

# 检查依赖
echo "📦 检查依赖..."
if ! command -v node &> /dev/null; then
    echo "❌ 未安装 Node.js，请先安装: brew install node"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ 未安装 Python3，请先安装: brew install python3"
    exit 1
fi

# 创建安装目录
echo "📁 创建安装目录..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"

# 复制文件
echo "📂 复制文件..."
cp -r "$(dirname "$0")/.."/* "$INSTALL_DIR/"

# 创建虚拟环境
echo "🐍 创建 Python 虚拟环境..."
cd "$INSTALL_DIR"
python3 -m venv venv
venv/bin/pip install -q -r requirements.txt

# 检查环境变量
echo "🔑 检查环境变量..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo "⚠️  警告: 未找到 .env 文件"
    echo "   请创建 $INSTALL_DIR/.env 并设置:"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - ELEVENLABS_API_KEY"
    echo ""
    echo "   参考: $INSTALL_DIR/.env.example"
    exit 1
fi

# 安装 LaunchAgent
echo "⚙️  安装 LaunchAgent..."
mkdir -p "$LAUNCH_AGENT_DIR"

# 替换环境变量
export TELEGRAM_BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN "$INSTALL_DIR/.env" | cut -d'=' -f2)
export ELEVENLABS_API_KEY=$(grep ELEVENLABS_API_KEY "$INSTALL_DIR/.env" | cut -d'=' -f2)

envsubst < "$INSTALL_DIR/deploy/$PLIST_FILE" > "$LAUNCH_AGENT_DIR/$PLIST_FILE"

# 加载服务
launchctl load "$LAUNCH_AGENT_DIR/$PLIST_FILE"

echo ""
echo "✅ 部署完成！"
echo ""
echo "管理命令:"
echo "  launchctl start com.claudio.bot    # 启动"
echo "  launchctl stop com.claudio.bot     # 停止"
echo "  launchctl unload ~/Library/LaunchAgents/com.claudio.bot.plist  # 卸载"
echo ""
echo "查看日志:"
echo "  tail -f $INSTALL_DIR/logs/claudio.log"
echo ""
echo "CLI 交互:"
echo "  cd $INSTALL_DIR && ./cli.py"
echo ""
