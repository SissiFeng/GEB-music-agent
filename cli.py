#!/usr/bin/env python3
"""
Claudio CLI - 命令行交互界面
类似截图中的复古电台风格
"""

import os
import sys
import time
import random
from datetime import datetime
from typing import Optional

from claudio_agent import MusicCurator, Mood
try:
    from tts_fallback import TTSManager
except ImportError:
    TTSManager = None

class ClaudioCLI:
    """Claudio 命令行界面"""
    
    # 复古电台风格的 ASCII 艺术
    LOGO = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     🎵  ╔══════════════════════════════════════╗  🎵     ║
    ║        ║      C L A U D I O   R A D I O       ║         ║
    ║        ║                                      ║         ║
    ║        ║     Your AI Music Curator & DJ       ║         ║
    ║        ╚══════════════════════════════════════╝         ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    
    # 颜色代码
    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "italic": "\033[3m",
        "underline": "\033[4m",
        "blink": "\033[5m",
        "reverse": "\033[7m",
        "hidden": "\033[8m",
        
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        
        "bg_black": "\033[40m",
        "bg_red": "\033[41m",
        "bg_green": "\033[42m",
        "bg_yellow": "\033[43m",
        "bg_blue": "\033[44m",
        "bg_magenta": "\033[45m",
        "bg_cyan": "\033[46m",
        "bg_white": "\033[47m",
    }
    
    def __init__(self):
        self.curator = MusicCurator(use_netease=True)
        self.tts = None
        self.current_song_index = 0
        self.is_playing = False
        self.use_tts = True  # TTS 开关
        
        # 初始化 TTS
        if TTSManager:
            try:
                self.tts = TTSManager()
                print(self.colorize("✅ TTS 服务已启动", "green"))
            except Exception as e:
                print(self.colorize(f"⚠️ TTS 未启动: {e}", "yellow"))
        else:
            print(self.colorize("⚠️ TTS 模块未加载", "yellow"))
    
    def colorize(self, text: str, color: str = "white", style: str = "") -> str:
        """添加颜色"""
        if not sys.stdout.isatty():  # 如果不是终端，不添加颜色
            return text
        
        codes = []
        if style:
            codes.append(self.COLORS.get(style, ""))
        codes.append(self.COLORS.get(color, ""))
        
        return f"{''.join(codes)}{text}{self.COLORS['reset']}"
    
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """打印头部"""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%Y-%m-%d %A")
        
        print(self.LOGO)
        print(self.colorize(f"    📻 {date_str}  {time_str}", "cyan"))
        print(self.colorize("    " + "═" * 56, "dim"))
        print()
    
    def print_now_playing(self):
        """打印当前播放"""
        song = self.curator.get_current_song()
        if not song:
            print(self.colorize("    ⏸️  暂无播放", "dim"))
            return
        
        # 计算进度
        duration_min = song.duration_ms // 60000
        duration_sec = (song.duration_ms // 1000) % 60
        
        # 模拟进度条
        progress = 35  # 模拟 35% 进度
        bar_width = 30
        filled = int(bar_width * progress / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        print()
        print(self.colorize("    ┌─ NOW PLAYING ─────────────────────────────────────┐", "magenta"))
        print(self.colorize(f"    │                                                   │", "magenta"))
        print(self.colorize(f"    │  🎵  {song.title[:40]:<40} │", "white", "bold"))
        print(self.colorize(f"    │     {song.artist[:44]:<44} │", "dim"))
        print(self.colorize(f"    │                                                   │", "magenta"))
        print(self.colorize(f"    │  {bar}  {progress}% │", "cyan"))
        print(self.colorize(f"    │     {duration_min}:{duration_sec:02d}                                          │", "dim"))
        print(self.colorize(f"    └───────────────────────────────────────────────────┘", "magenta"))
        print()
    
    def speak(self, text: str, language: str = "auto"):
        """语音播报"""
        if self.tts and self.use_tts:
            print(self.colorize(f"    🎙️  {text[:60]}...", "green"))
            self.tts.speak_and_play(text, language)
        else:
            print(self.colorize(f"    💬 {text}", "green"))
    
    def dj_intro(self):
        """DJ 开场"""
        hour = datetime.now().hour
        
        intros = [
            "你好，我是 Claudio，你的 AI 音乐 DJ。",
            "欢迎来到 Claudio Radio，让我为你推荐音乐。",
            "我是 Claudio，很高兴为你服务。",
        ]
        
        if 5 <= hour < 12:
            intros.append("早上好，让音乐陪你开始新的一天。")
        elif 12 <= hour < 18:
            intros.append("下午好，希望这些音乐能让你放松。")
        else:
            intros.append("晚上好，让音乐陪你度过这段时光。")
        
        intro = random.choice(intros)
        self.speak(intro, language="zh")
    
    def handle_command(self, command: str) -> bool:
        """处理命令"""
        cmd = command.strip().lower()
        
        if cmd in ["quit", "exit", "q"]:
            print(self.colorize("\n    👋 感谢使用 Claudio Radio，再见！", "yellow"))
            return False
        
        elif cmd in ["help", "h", "?"]:
            self.print_help()
        
        elif cmd in ["now", "n"]:
            self.print_now_playing()
        
        elif cmd in ["next", "skip", "s"]:
            song = self.curator.next_song()
            if song:
                intro = self.curator.generate_song_intro(song)
                self.speak(intro, "zh")
                self.print_now_playing()
            else:
                print(self.colorize("    ⚠️  没有下一首了", "yellow"))
        
        elif cmd in ["prev", "p", "back"]:
            song = self.curator.previous_song()
            if song:
                intro = self.curator.generate_song_intro(song)
                self.speak(intro, "zh")
                self.print_now_playing()
        
        elif cmd in ["pause", "stop"]:
            self.is_playing = False
            print(self.colorize("    ⏸️  已暂停", "yellow"))
        
        elif cmd == "tts on":
            self.use_tts = True
            print(self.colorize("    🎙️  TTS 已开启", "green"))
        
        elif cmd == "tts off":
            self.use_tts = False
            print(self.colorize("    🔇 TTS 已关闭", "yellow"))
        
        elif cmd in ["play", "resume"]:
            self.is_playing = True
            print(self.colorize("    ▶️  继续播放", "green"))
        
        elif cmd.startswith("mood "):
            mood_str = cmd[5:].strip()
            self.play_by_mood(mood_str)
        
        elif cmd:
            # 自然语言请求
            self.handle_natural_language(command)
        
        return True
    
    def play_by_mood(self, mood_str: str):
        """根据情绪播放"""
        mood_map = {
            "focus": Mood.FOCUS,
            "work": Mood.FOCUS,
            "学习": Mood.FOCUS,
            "工作": Mood.FOCUS,
            "relax": Mood.RELAX,
            "放松": Mood.RELAX,
            "休息": Mood.RELAX,
            "sleep": Mood.SLEEP,
            "睡觉": Mood.SLEEP,
            "助眠": Mood.SLEEP,
            "energize": Mood.ENERGIZE,
            "提神": Mood.ENERGIZE,
            "workout": Mood.WORKOUT,
            "运动": Mood.WORKOUT,
            "健身": Mood.WORKOUT,
        }
        
        mood = mood_map.get(mood_str.lower())
        if mood:
            request = f"给我一些{mood_str}的音乐"
            self.handle_natural_language(request)
        else:
            print(self.colorize(f"    ⚠️  未知情绪: {mood_str}", "yellow"))
            print(self.colorize("    可用: focus, relax, sleep, energize, workout", "dim"))
    
    def handle_natural_language(self, text: str):
        """处理自然语言"""
        print(self.colorize(f"\n    🔍 理解请求: {text}", "cyan"))
        
        # 生成播放列表
        playlist = self.curator.create_playlist(text)
        
        # DJ 开场白
        context = {"user_request": text}
        dj_text = self.curator.generate_dj_intro(context)
        self.speak(dj_text, "zh")
        
        # 显示播放列表
        print()
        print(self.colorize(f"    📻 {playlist.name}", "white", "bold"))
        print(self.colorize(f"    {playlist.description}", "dim"))
        print()
        
        # 显示歌曲列表
        for i, song in enumerate(playlist.songs[:5], 1):
            duration_min = song.duration_ms // 60000
            duration_sec = (song.duration_ms // 1000) % 60
            print(self.colorize(f"    {i}. 《{song.title}》- {song.artist} ({duration_min}:{duration_sec:02d})", "white"))
        
        if len(playlist.songs) > 5:
            print(self.colorize(f"    ... 还有 {len(playlist.songs) - 5} 首", "dim"))
        
        # 播报第一首歌
        if playlist.songs:
            first_song = playlist.songs[0]
            intro = self.curator.generate_song_intro(first_song)
            time.sleep(1)
            self.speak(intro, "zh")
            self.is_playing = True
        
        print()
    
    def print_help(self):
        """打印帮助"""
        help_text = """
    ┌─ COMMANDS ──────────────────────────────────────────┐
    │                                                      │
    │  now, n          - 显示当前播放                     │
    │  next, skip, s   - 下一首                           │
    │  prev, p         - 上一首                           │
    │  pause, stop     - 暂停                             │
    │  play, resume    - 继续播放                         │
    │  tts on/off      - 开启/关闭语音                    │
    │  mood <情绪>     - 按情绪播放 (focus/relax/sleep)   │
    │  help, h, ?      - 显示帮助                         │
    │  quit, exit, q   - 退出                             │
    │                                                      │
    │  或直接输入: "我想听点适合写代码的歌"               │
    │                                                      │
    └──────────────────────────────────────────────────────┘
        """
        print(self.colorize(help_text, "cyan"))
    
    def run(self):
        """运行 CLI"""
        self.clear_screen()
        self.print_header()
        
        # DJ 开场
        self.dj_intro()
        
        # 显示帮助
        self.print_help()
        
        # 主循环
        while True:
            try:
                # 显示提示符
                prompt = self.colorize("    🎵 ", "magenta") + self.colorize("Claudio", "white", "bold") + self.colorize(" > ", "magenta")
                command = input(prompt).strip()
                
                if not command:
                    continue
                
                if not self.handle_command(command):
                    break
                
            except KeyboardInterrupt:
                print()
                print(self.colorize("\n    👋 感谢使用 Claudio Radio，再见！", "yellow"))
                break
            except Exception as e:
                print(self.colorize(f"\n    ❌ 错误: {e}", "red"))


def main():
    """主入口"""
    cli = ClaudioCLI()
    cli.run()


if __name__ == "__main__":
    main()
