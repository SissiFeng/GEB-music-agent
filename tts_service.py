#!/usr/bin/env python3
"""
TTS 服务 - ElevenLabs 集成
支持中英文，温柔嗓音
"""

import os
import requests
from typing import Optional
from pathlib import Path

class ElevenLabsTTS:
    """ElevenLabs TTS 服务"""
    
    # 温柔的嗓音推荐 - 使用免费/默认嗓音
    VOICES = {
        # 免费默认嗓音（支持多语言）
        "default": "21m00Tcm4TlvDq8ikWAM",  # Bella - 免费，柔和、亲切
        "gentle": "AZnzlk1XvdvUeBnXmlld",   # Elli - 免费，温柔
        
        # 备选
        "calm": "MF3mGyEYCl7XYWbV9V6O",     # 平静
        "soft": "TxGEqnHWrfWFTfGW9XjX",     # 柔和
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 ELEVENLABS_API_KEY 环境变量")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        # 默认使用免费嗓音
        self.default_voice = self.VOICES["default"]
        
        # 创建音频缓存目录
        self.cache_dir = Path("./audio_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    def speak(self, text: str, voice_id: Optional[str] = None, 
              language: str = "auto", save_path: Optional[str] = None) -> str:
        """
        将文本转换为语音
        
        Args:
            text: 要转换的文本
            voice_id: 嗓音 ID，默认使用温柔女声
            language: 语言 (en/zh/auto)
            save_path: 保存路径，默认自动生成
            
        Returns:
            音频文件路径
        """
        if not voice_id:
            voice_id = self._select_voice(language)
        
        # 生成缓存文件名
        if not save_path:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            save_path = self.cache_dir / f"claudio_{text_hash}.mp3"
        else:
            save_path = Path(save_path)
        
        # 如果已缓存，直接返回
        if save_path.exists():
            print(f"🎵 使用缓存音频: {save_path}")
            return str(save_path)
        
        # 调用 ElevenLabs API
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # 多语言模型
            "voice_settings": {
                "stability": 0.5,      # 稳定性 (0-1)
                "similarity_boost": 0.75,  # 相似度提升 (0-1)
                "style": 0.3,          # 风格化程度 (0-1)，低值更自然
                "use_speaker_boost": True
            }
        }
        
        try:
            print(f"🎙️ 生成语音: {text[:50]}...")
            response = requests.post(url, json=data, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # 保存音频
            with open(save_path, "wb") as f:
                f.write(response.content)
            
            print(f"✅ 音频已保存: {save_path}")
            return str(save_path)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ TTS 生成失败: {e}")
            return ""
    
    def _select_voice(self, language: str) -> str:
        """根据语言选择嗓音 - 使用免费默认嗓音"""
        # 使用免费默认嗓音 Bella，支持多语言
        return self.default_voice
    
    def play_audio(self, audio_path: str) -> bool:
        """播放音频文件"""
        import platform
        import subprocess
        
        system = platform.system()
        
        try:
            if system == "Darwin":  # macOS
                subprocess.run(["afplay", audio_path], check=True)
            elif system == "Linux":
                subprocess.run(["mpg123", "-q", audio_path], check=True)
            elif system == "Windows":
                import winsound
                winsound.PlaySound(audio_path, winsound.SND_FILENAME)
            else:
                print(f"⚠️ 不支持自动播放，请手动播放: {audio_path}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 播放失败: {e}")
            print(f"   请手动播放: {audio_path}")
            return False
    
    def speak_and_play(self, text: str, language: str = "auto", 
                       voice_id: Optional[str] = None) -> bool:
        """生成语音并播放"""
        audio_path = self.speak(text, voice_id, language)
        if audio_path:
            return self.play_audio(audio_path)
        return False
    
    def get_available_voices(self) -> list:
        """获取可用的嗓音列表"""
        url = f"{self.base_url}/voices"
        
        try:
            response = requests.get(url, headers={"xi-api-key": self.api_key})
            response.raise_for_status()
            voices = response.json().get("voices", [])
            
            return [
                {
                    "id": v["voice_id"],
                    "name": v["name"],
                    "category": v.get("category", "premade"),
                    "description": v.get("description", ""),
                    "preview_url": v.get("preview_url", "")
                }
                for v in voices
            ]
        except Exception as e:
            print(f"❌ 获取嗓音列表失败: {e}")
            return []


# 测试
if __name__ == "__main__":
    import os
    
    # 检查 API Key
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("请设置 ELEVENLABS_API_KEY 环境变量")
        print("获取方式: https://elevenlabs.io/app/settings/api-keys")
        exit(1)
    
    tts = ElevenLabsTTS()
    
    # 测试中文
    print("\n🎵 测试中文...")
    tts.speak_and_play("你好，我是 Claudio，你的 AI 音乐 DJ。让我为你推荐一些适合现在听的音乐。", language="zh")
    
    # 测试英文
    print("\n🎵 测试英文...")
    tts.speak_and_play("Hello, I'm Claudio, your AI music DJ. Let me recommend some music for you.", language="en")
    
    # 测试混合
    print("\n🎵 测试中英文混合...")
    tts.speak_and_play("接下来是周杰伦的《夜曲》，希望你喜欢。This song is perfect for your current mood.")
