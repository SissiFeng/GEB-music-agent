#!/bin/bash
# Claudio AI DJ 自动部署脚本

set -e

echo "🎵 Claudio AI DJ 自动部署脚本"
echo "==============================="

# 配置
INSTALL_DIR="/opt/claudio"
USER="claudio"
SERVICE_FILE="claudio.service"

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行此脚本"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
if ! command -v node &> /dev/null; then
    echo "❌ 未安装 Node.js，请先安装"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ 未安装 Python3，请先安装"
    exit 1
fi

# 创建用户
echo "👤 创建用户..."
if ! id "$USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$USER"
fi

# 创建安装目录
echo "📁 创建安装目录..."
mkdir -p "$INSTALL_DIR"

# 复制文件
echo "📂 复制文件..."
cp -r ../* "$INSTALL_DIR/"
chown -R "$USER:$USER" "$INSTALL_DIR"

# 创建虚拟环境
echo "🐍 创建 Python 虚拟环境..."
cd "$INSTALL_DIR"
sudo -u "$USER" python3 -m venv venv
sudo -u "$USER" venv/bin/pip install -q -r requirements.txt

# 检查环境变量
echo "🔑 检查环境变量..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo "⚠️  警告: 未找到 .env 文件"
    echo "   请创建 $INSTALL_DIR/.env 并设置 TELEGRAM_BOT_TOKEN"
    echo "   参考: $INSTALL_DIR/.env.example"
fi

# 安装 systemd 服务
echo "⚙️  安装 systemd 服务..."
cp "$SERVICE_FILE" /etc/systemd/system/
systemctl daemon-reload
systemctl enable claudio

echo ""
echo "✅ 部署完成！"
echo ""
echo "启动命令:"
echo "  sudo systemctl start claudio    # 启动服务"
echo "  sudo systemctl stop claudio     # 停止服务"
echo "  sudo systemctl status claudio   # 查看状态"
echo "  sudo journalctl -u claudio -f   # 查看日志"
echo ""
echo "CLI 交互:"
echo "  cd $INSTALL_DIR && ./cli.py"
echo ""
