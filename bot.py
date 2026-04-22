#!/usr/bin/env python3
"""
Claudio Telegram Bot - 主入口
"""

import os
import logging
import asyncio
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from claudio_agent import ClaudioTelegramBot

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# 初始化 Claudio
claudio = ClaudioTelegramBot(os.getenv("TELEGRAM_BOT_TOKEN", "test"))


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start 命令"""
    response = claudio.handle_message("/start", str(update.effective_user.id))
    await update.message.reply_text(response["content"])


async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/now 命令"""
    response = claudio.handle_message("/now", str(update.effective_user.id))
    await update.message.reply_text(response["content"])


async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/next 命令"""
    response = claudio.handle_message("/next", str(update.effective_user.id))
    await update.message.reply_text(response["content"])


async def prev_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/prev 命令"""
    response = claudio.handle_message("/prev", str(update.effective_user.id))
    await update.message.reply_text(response["content"])


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status 命令"""
    response = claudio.handle_message("/status", str(update.effective_user.id))
    await update.message.reply_text(response["content"])


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理普通消息"""
    user_message = update.message.text
    user_id = str(update.effective_user.id)
    
    # 显示"正在输入"
    await update.message.chat.send_action(action="typing")
    
    # 处理消息
    response = claudio.handle_message(user_message, user_id)
    
    # 发送回复
    await update.message.reply_text(response["content"])


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """错误处理"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "抱歉，出错了。请稍后再试，或者换个说法。"
        )


def main():
    """主函数"""
    # 获取 Token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "test":
        logger.error("请设置 TELEGRAM_BOT_TOKEN 环境变量")
        print("错误：请设置 TELEGRAM_BOT_TOKEN 环境变量")
        print("示例：export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        return
    
    # 创建应用
    application = Application.builder().token(token).build()
    
    # 添加处理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("now", now_command))
    application.add_handler(CommandHandler("next", next_command))
    application.add_handler(CommandHandler("skip", next_command))  # 别名
    application.add_handler(CommandHandler("prev", prev_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # 普通消息处理器
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # 错误处理器
    application.add_error_handler(error_handler)
    
    # 启动 Bot
    logger.info("Claudio Bot 启动中...")
    print("🎵 Claudio AI DJ 已启动！")
    print("按 Ctrl+C 停止")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
