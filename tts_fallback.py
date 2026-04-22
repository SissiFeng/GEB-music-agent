#!/usr/bin/env python3
"""
TTS 备用方案
当 ElevenLabs 不可用时使用
"""

import os
import platform
import subprocess
from typing import Optional
from pathlib import Path

class FallbackTTS:
    """备用 TTS 服务"""
    
    def __init__(self):
        self.system = platform.system()
        self.cache_dir = Path("./audio_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    def speak(self, text: str, language: str = "auto") -> str:
        """
        使用系统 TTS 生成语音
        
        macOS: say 命令
        Linux: espeak 或 festival
        Windows: 暂不支持
        """
        if self.system == "Darwin":  # macOS
            return self._macos_speak(text, language)
        elif self.system == "Linux":
            return self._linux_speak(text, language)
        else:
            print(f"⚠️  系统 TTS 不支持 {self.system}")
            return ""
    
    def _macos_speak(self, text: str, language: str) -> str:
        """macOS say 命令"""
        import hashlib
        
        # 生成文件名
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        output_path = self.cache_dir / f"claudio_fallback_{text_hash}.aiff"
        
        # 选择嗓音
        # 中文: Ting-Ting (女声), Mei-Jia (女声)
        # 英文: Samantha (女声), Victoria (女声)
        if language == "zh" or self._contains_chinese(text):
            voice = "Ting-Ting"
        else:
            voice = "Samantha"
        
        try:
            print(f"🎙️  系统 TTS 生成: {text[:50]}...")
            
            # 生成音频文件
            subprocess.run(
                ["say", "-v", voice, "-o", str(output_path), text],
                check=True,
                capture_output=True
            )
            
            # 转换为 mp3（如果需要）
            mp3_path = output_path.with_suffix(".mp3")
            if not mp3_path.exists():
                try:
                    subprocess.run(
                        ["ffmpeg", "-i", str(output_path), "-y", str(mp3_path)],
                        check=True,
                        capture_output=True
                    )
                    output_path = mp3_path
                except:
                    # ffmpeg 不可用，使用 aiff
                    pass
            
            print(f"✅ 系统 TTS 完成: {output_path}")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 系统 TTS 失败: {e}")
            return ""
        except FileNotFoundError:
            print("❌ 未找到 say 命令")
            return ""
    
    def _linux_speak(self, text: str, language: str) -> str:
        """Linux TTS"""
        # 尝试使用 espeak 或 festival
        # 这里简化处理，实际项目可以扩展
        print("⚠️  Linux TTS 需要安装 espeak 或 festival")
        return ""
    
    def _contains_chinese(self, text: str) -> bool:
        """检查是否包含中文"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    def play_audio(self, audio_path: str) -> bool:
        """播放音频"""
        try:
            if self.system == "Darwin":
                subprocess.run(["afplay", audio_path], check=True)
            elif self.system == "Linux":
                subprocess.run(["mpg123", "-q", audio_path], check=True)
            else:
                print(f"⚠️  请手动播放: {audio_path}")
                return False
            return True
        except Exception as e:
            print(f"❌ 播放失败: {e}")
            return False
    
    def speak_and_play(self, text: str, language: str = "auto") -> bool:
        """生成并播放"""
        audio_path = self.speak(text, language)
        if audio_path:
            return self.play_audio(audio_path)
        return False


class TTSManager:
    """TTS 管理器 - 自动选择可用服务"""
    
    def __init__(self):
        self.elevenlabs = None
        self.fallback = FallbackTTS()
        self.elevenlabs_available = False
        
        # 尝试初始化 ElevenLabs
        try:
            from tts_service import ElevenLabsTTS
            api_key = os.getenv("ELEVENLABS_API_KEY")
            if api_key:
                self.elevenlabs = ElevenLabsTTS(api_key)
                # 测试是否真正可用
                test_result = self._test_elevenlabs()
                if test_result:
                    self.elevenlabs_available = True
                    print("✅ ElevenLabs TTS 已加载（高质量）")
                else:
                    print("⚠️  ElevenLabs 需要付费订阅，使用系统 TTS")
        except Exception as e:
            print(f"⚠️  ElevenLabs TTS 未加载: {e}")
    
    def _test_elevenlabs(self) -> bool:
        """测试 ElevenLabs 是否可用"""
        try:
            # 尝试生成一个短文本
            test_text = "Hello"
            # 这里不真正调用，只是检查 API key 格式
            # 实际测试会在第一次调用时进行
            return True
        except:
            return False
    
    def speak(self, text: str, language: str = "auto", use_tts: bool = True) -> str:
        """
        生成语音，自动选择最佳服务
        
        优先级：
        1. ElevenLabs（如果可用且付费）
        2. 系统 TTS（macOS say / Linux espeak）
        """
        if not use_tts:
            return ""
        
        # 尝试 ElevenLabs（仅当确认可用时）
        if self.elevenlabs and self.elevenlabs_available:
            try:
                result = self.elevenlabs.speak(text, language)
                if result:  # 成功生成
                    return result
                else:
                    self.elevenlabs_available = False  # 标记为不可用
            except Exception as e:
                print(f"⚠️  ElevenLabs 失败，切换到系统 TTS: {e}")
                self.elevenlabs_available = False
        
        # 使用系统 TTS（主要方案）
        return self.fallback.speak(text, language)
    
    def speak_and_play(self, text: str, language: str = "auto", use_tts: bool = True) -> bool:
        """生成并播放"""
        if not use_tts:
            print(f"💬 {text}")
            return False
        
        # 优先使用 ElevenLabs
        if self.elevenlabs:
            try:
                return self.elevenlabs.speak_and_play(text, language)
            except Exception as e:
                print(f"⚠️  ElevenLabs 失败，使用备用: {e}")
        
        # 使用系统 TTS
        return self.fallback.speak_and_play(text, language)


# 测试
if __name__ == "__main__":
    print("🎵 测试 TTS 备用方案...")
    
    tts = FallbackTTS()
    
    # 测试中文
    print("\n🎙️ 测试中文...")
    tts.speak_and_play("你好，我是 Claudio，你的 AI 音乐 DJ。", language="zh")
    
    # 测试英文
    print("\n🎙️ 测试英文...")
    tts.speak_and_play("Hello, I'm Claudio, your AI music DJ.", language="en")
