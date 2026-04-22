#!/usr/bin/env python3
"""
Claudio - AI Music Curation Agent
个性化 AI 音乐电台 / AI DJ
"""

import os
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# 导入网易云音乐 API
try:
    from netease_api import NeteaseMusicAPI, NeteaseSong
    NETEASE_AVAILABLE = True
except ImportError:
    NETEASE_AVAILABLE = False

class TimeSlot(Enum):
    """时段定义"""
    EARLY_MORNING = "early_morning"  # 5:00-8:00
    MORNING = "morning"              # 8:00-12:00
    LUNCH = "lunch"                  # 12:00-14:00
    AFTERNOON = "afternoon"          # 14:00-18:00
    EVENING = "evening"              # 18:00-22:00
    NIGHT = "night"                  # 22:00-5:00

class Mood(Enum):
    """情绪/场景"""
    FOCUS = "focus"           # 专注工作
    RELAX = "relax"           # 放松休息
    ENERGIZE = "energize"     # 提神醒脑
    WORKOUT = "workout"       # 运动健身
    SLEEP = "sleep"           # 助眠
    PARTY = "party"           # 派对狂欢
    COMMUTE = "commute"       # 通勤路上

@dataclass
class Song:
    """歌曲信息"""
    title: str
    artist: str
    album: str
    duration_ms: int
    genre: List[str]
    mood: List[str]
    energy: float  # 0.0-1.0
    tempo: int     # BPM
    source_url: str = ""
    
@dataclass
class Playlist:
    """播放列表"""
    name: str
    description: str
    songs: List[Song]
    total_duration_ms: int = 0
    theme: str = ""
    
@dataclass
class DJMessage:
    """DJ 播报消息"""
    text: str
    mood: str
    context: Dict
    timestamp: datetime

class MusicCurator:
    """音乐策展核心类"""
    
    def __init__(self, user_id: str = "default", use_netease: bool = True):
        self.user_id = user_id
        self.current_playlist: Optional[Playlist] = None
        self.current_song_index = 0
        self.conversation_history: List[Dict] = []
        
        # 初始化网易云音乐 API
        self.netease = None
        if use_netease and NETEASE_AVAILABLE:
            try:
                self.netease = NeteaseMusicAPI()
                # 测试连接
                self.netease._request("/search", {"keywords": "test", "limit": 1})
                print("✅ 网易云音乐 API 连接成功")
            except Exception as e:
                print(f"⚠️ 网易云音乐 API 未启动: {e}")
                print("   请运行: npx NeteaseCloudMusicApi")
                self.netease = None
    
    # 时段-风格映射
    TIME_MOOD_MAP = {
        TimeSlot.EARLY_MORNING: {
            "moods": [Mood.RELAX, Mood.FOCUS],
            "genres": ["ambient", "jazz", "classical", "acoustic"],
            "energy_range": (0.2, 0.5),
            "dj_persona": "温柔唤醒者"
        },
        TimeSlot.MORNING: {
            "moods": [Mood.FOCUS, Mood.ENERGIZE],
            "genres": ["indie", "pop", "electronic", "folk"],
            "energy_range": (0.4, 0.7),
            "dj_persona": "活力启动器"
        },
        TimeSlot.LUNCH: {
            "moods": [Mood.RELAX, Mood.ENERGIZE],
            "genres": ["pop", "r&b", "indie", "world"],
            "energy_range": (0.5, 0.8),
            "dj_persona": "午间陪伴者"
        },
        TimeSlot.AFTERNOON: {
            "moods": [Mood.FOCUS, Mood.RELAX],
            "genres": ["electronic", "ambient", "jazz", "classical"],
            "energy_range": (0.3, 0.6),
            "dj_persona": "深度工作助手"
        },
        TimeSlot.EVENING: {
            "moods": [Mood.RELAX, Mood.ENERGIZE],
            "genres": ["indie", "rock", "electronic", "r&b"],
            "energy_range": (0.5, 0.8),
            "dj_persona": "傍晚放松师"
        },
        TimeSlot.NIGHT: {
            "moods": [Mood.RELAX, Mood.SLEEP],
            "genres": ["ambient", "classical", "jazz", "lo-fi"],
            "energy_range": (0.1, 0.4),
            "dj_persona": "深夜守护者"
        }
    }
    
    # 用户偏好学习
    USER_PREFERENCES = {
        "favorite_genres": [],
        "favorite_artists": [],
        "avoid_genres": [],
        "energy_preference": 0.5,
        "discovery_ratio": 0.3,  # 新发现歌曲比例
    }
    
    def get_current_time_slot(self) -> TimeSlot:
        """获取当前时段"""
        hour = datetime.now().hour
        if 5 <= hour < 8:
            return TimeSlot.EARLY_MORNING
        elif 8 <= hour < 12:
            return TimeSlot.MORNING
        elif 12 <= hour < 14:
            return TimeSlot.LUNCH
        elif 14 <= hour < 18:
            return TimeSlot.AFTERNOON
        elif 18 <= hour < 22:
            return TimeSlot.EVENING
        else:
            return TimeSlot.NIGHT
    
    def generate_dj_intro(self, context: Dict) -> str:
        """生成 DJ 开场白"""
        time_slot = self.get_current_time_slot()
        config = self.TIME_MOOD_MAP[time_slot]
        
        hour = datetime.now().hour
        minute = datetime.now().minute
        
        # 根据时段生成不同的开场白
        intros = {
            TimeSlot.EARLY_MORNING: [
                f"早上好，现在是 {hour}:{minute:02d}。让轻柔的音乐陪你慢慢醒来。",
                f"清晨 {hour} 点，世界还在苏醒。这是一天中最宁静的时刻。",
                f"{hour}:{minute:02d}，新的一天开始了。用音乐为你的早晨注入温暖。"
            ],
            TimeSlot.MORNING: [
                f"上午好！{hour}:{minute:02d}，是时候让大脑进入工作状态了。",
                f"{hour} 点的上午，来一些能让你专注的音乐吧。",
                f"早上 {hour}:{minute:02d}，让节奏带动你的效率。"
            ],
            TimeSlot.LUNCH: [
                f"中午 {hour}:{minute:02d}，午休时间。放松一下，吃点好的。",
                f"午餐时间到！{hour} 点，让音乐陪你享受这段休息时光。",
                f"{hour}:{minute:02d}，午间的音乐时光，为你充电。"
            ],
            TimeSlot.AFTERNOON: [
                f"下午 {hour}:{minute:02d}，继续专注。这些音乐能帮你保持状态。",
                f"{hour} 点的下午，来一些适合深度工作的背景音乐。",
                f"下午好，{hour}:{minute:02d}。让音乐成为你工作的伙伴。"
            ],
            TimeSlot.EVENING: [
                f"晚上 {hour}:{minute:02d}，工作结束了。是时候放松一下。",
                f"{hour} 点的傍晚，让音乐陪你度过这段过渡时光。",
                f"晚上好，{hour}:{minute:02d}。这些歌能让你的 evening 更美好。"
            ],
            TimeSlot.NIGHT: [
                f"深夜 {hour}:{minute:02d}，世界安静了。让音乐陪你度过这段独处时光。",
                f"{hour} 点的夜晚，来一些能帮助放松的音乐。",
                f"{hour}:{minute:02d}，夜深人静。这些歌适合现在的你。"
            ]
        }
        
        intro = random.choice(intros[time_slot])
        
        # 添加天气信息（如果有）
        if "weather" in context:
            weather = context["weather"]
            intro += f" 外面{weather}，"
            if "雨" in weather or "雪" in weather:
                intro += "这样的天气最适合 indoors 听音乐。"
            elif "晴" in weather:
                intro += "不过既然你在室内，那就让音乐陪伴你。"
        
        return intro
    
    def parse_user_request(self, request: str) -> Dict:
        """解析用户自然语言请求"""
        request = request.lower()
        
        # 情绪关键词映射
        mood_keywords = {
            "专注": Mood.FOCUS,
            "工作": Mood.FOCUS,
            "学习": Mood.FOCUS,
            "放松": Mood.RELAX,
            "休息": Mood.RELAX,
            "睡觉": Mood.SLEEP,
            "助眠": Mood.SLEEP,
            "运动": Mood.WORKOUT,
            "健身": Mood.WORKOUT,
            "提神": Mood.ENERGIZE,
            "醒脑": Mood.ENERGIZE,
            "派对": Mood.PARTY,
            "嗨": Mood.PARTY,
            "通勤": Mood.COMMUTE,
            "路上": Mood.COMMUTE,
        }
        
        # 风格关键词
        genre_keywords = {
            "电子": "electronic",
            "电音": "electronic",
            "爵士": "jazz",
            "古典": "classical",
            "流行": "pop",
            "摇滚": "rock",
            "民谣": "folk",
            "说唱": "hip-hop",
            "嘻哈": "hip-hop",
            "r&b": "r&b",
            "轻音乐": "ambient",
            "纯音乐": "instrumental",
            "韩语": "k-pop",
            "日语": "j-pop",
            "英语": "english",
            "华语": "mandarin",
        }
        
        parsed = {
            "mood": None,
            "genres": [],
            "energy": None,
            "duration_minutes": 30,  # 默认30分钟
            "artist": None,
            "language": None,
        }
        
        # 解析情绪
        for keyword, mood in mood_keywords.items():
            if keyword in request:
                parsed["mood"] = mood
                break
        
        # 解析风格
        for keyword, genre in genre_keywords.items():
            if keyword in request:
                parsed["genres"].append(genre)
        
        # 解析能量级别
        if any(word in request for word in ["轻", "柔", "慢", "安静"]):
            parsed["energy"] = 0.3
        elif any(word in request for word in ["重", "快", "躁", "嗨"]):
            parsed["energy"] = 0.8
        
        # 解析时长
        if "小时" in request:
            import re
            match = re.search(r'(\d+)\s*小时', request)
            if match:
                parsed["duration_minutes"] = int(match.group(1)) * 60
        elif "分钟" in request:
            import re
            match = re.search(r'(\d+)\s*分钟', request)
            if match:
                parsed["duration_minutes"] = int(match.group(1))
        
        return parsed
    
    def create_playlist(self, request: str, context: Dict = None) -> Playlist:
        """创建播放列表"""
        if context is None:
            context = {}
        
        # 解析用户请求
        parsed = self.parse_user_request(request)
        
        # 如果没有指定情绪，根据时段自动选择
        if parsed["mood"] is None:
            time_slot = self.get_current_time_slot()
            parsed["mood"] = self.TIME_MOOD_MAP[time_slot]["moods"][0]
        
        # 生成播放列表
        # 这里应该调用音乐 API，现在用模拟数据
        songs = self._fetch_songs(parsed)
        
        # 生成播放列表名称和描述
        playlist_name = self._generate_playlist_name(parsed)
        playlist_desc = self._generate_playlist_description(parsed, context)
        
        playlist = Playlist(
            name=playlist_name,
            description=playlist_desc,
            songs=songs,
            theme=parsed["mood"].value if parsed["mood"] else "mixed"
        )
        
        # 计算总时长
        playlist.total_duration_ms = sum(song.duration_ms for song in songs)
        
        self.current_playlist = playlist
        self.current_song_index = 0
        
        return playlist
    
    def _fetch_songs(self, criteria: Dict) -> List[Song]:
        """获取歌曲（优先使用网易云音乐 API）"""
        
        # 如果有网易云音乐 API，优先使用
        if self.netease:
            try:
                return self._fetch_from_netease(criteria)
            except Exception as e:
                print(f"网易云音乐获取失败，使用模拟数据: {e}")
        
        # 模拟歌曲库
        mock_songs = [
            Song("비행운", "MoonMoon", "飞行云", 240000, ["indie", "korean"], ["relax", "focus"], 0.4, 85),
            Song("Weightless", "Marconi Union", "Weightless", 480000, ["ambient"], ["sleep", "relax"], 0.2, 60),
            Song("Lovers in Japan", "Coldplay", "Viva La Vida", 240000, ["rock", "pop"], ["energize"], 0.7, 120),
            Song("夜曲", "周杰伦", "十一月的萧邦", 240000, ["mandarin", "pop"], ["relax", "focus"], 0.5, 90),
            Song("Clair de Lune", "Claude Debussy", "Suite bergamasque", 300000, ["classical"], ["focus", "relax"], 0.3, 70),
            Song("Tycho - A Walk", "Tycho", "Dive", 300000, ["electronic", "ambient"], ["focus"], 0.5, 95),
            Song("Bonobo - Kiara", "Bonobo", "Black Sands", 240000, ["electronic", "downtempo"], ["focus"], 0.6, 100),
            Song("富士山下", "陈奕迅", "What's Going On...?", 240000, ["mandarin", "pop"], ["relax"], 0.4, 85),
        ]
        
        # 根据条件筛选
        filtered = mock_songs
        
        if criteria.get("genres"):
            filtered = [s for s in filtered if any(g in s.genre for g in criteria["genres"])]
        
        if criteria.get("mood"):
            mood_value = criteria["mood"].value
            filtered = [s for s in filtered if mood_value in s.mood]
        
        if criteria.get("energy") is not None:
            target_energy = criteria["energy"]
            filtered = [s for s in filtered if abs(s.energy - target_energy) < 0.3]
        
        # 如果没有匹配，返回全部
        if not filtered:
            filtered = mock_songs
        
        # 随机排序，增加多样性
        random.shuffle(filtered)
        
        # 限制数量（根据时长）
        target_duration = criteria.get("duration_minutes", 30) * 60 * 1000
        selected = []
        current_duration = 0
        
        for song in filtered:
            if current_duration + song.duration_ms <= target_duration:
                selected.append(song)
                current_duration += song.duration_ms
            if current_duration >= target_duration * 0.8:  # 达到80%目标时长即可
                break
        
        return selected if selected else filtered[:5]
    
    def _fetch_from_netease(self, criteria: Dict) -> List[Song]:
        """从网易云音乐获取歌曲"""
        mood = criteria.get("mood")
        genres = criteria.get("genres", [])
        keywords = criteria.get("keywords", "")
        
        # 构建搜索关键词
        search_keywords = []
        
        # 根据情绪选择关键词
        if mood:
            mood_keywords = {
                Mood.FOCUS: "专注 学习 工作 纯音乐",
                Mood.RELAX: "放松 轻音乐 治愈 安静",
                Mood.ENERGIZE: "提神 醒脑 活力 节奏",
                Mood.WORKOUT: "运动 健身 跑步 动感",
                Mood.SLEEP: "助眠 睡眠 冥想 轻音乐",
                Mood.PARTY: "派对 狂欢 嗨 夜店",
                Mood.COMMUTE: "通勤 路上 车载 轻松",
            }
            search_keywords.append(mood_keywords.get(mood, ""))
        
        # 添加风格关键词
        genre_map = {
            "electronic": "电子",
            "jazz": "爵士",
            "classical": "古典",
            "pop": "流行",
            "rock": "摇滚",
            "folk": "民谣",
            "hip-hop": "说唱",
            "r&b": "R&B",
            "ambient": "轻音乐",
            "k-pop": "韩语",
            "j-pop": "日语",
            "mandarin": "华语",
        }
        for genre in genres:
            if genre in genre_map:
                search_keywords.append(genre_map[genre])
        
        # 如果有关键词，直接使用
        if keywords:
            search_keywords.append(keywords)
        
        # 默认搜索
        if not search_keywords:
            search_keywords = ["热门 推荐"]
        
        # 搜索歌曲
        query = " ".join(search_keywords)
        print(f"搜索网易云音乐: {query}")
        
        netease_songs = self.netease.search_songs(query, limit=20)
        
        # 转换为 Song 对象
        songs = []
        for ns in netease_songs:
            # 估算 energy 和 mood
            energy = 0.5
            mood_tags = ["relax"]
            
            # 根据歌名和艺人简单判断
            if any(word in ns.title for word in ["摇滚", "动感", "嗨", "Run", "Power"]):
                energy = 0.8
                mood_tags = ["energize", "workout"]
            elif any(word in ns.title for word in ["安静", "睡眠", "冥想", "Sleep", "Quiet"]):
                energy = 0.2
                mood_tags = ["sleep", "relax"]
            elif any(word in ns.title for word in ["专注", "学习", "工作", "Study", "Focus"]):
                energy = 0.4
                mood_tags = ["focus"]
            
            song = Song(
                title=ns.title,
                artist=ns.artist,
                album=ns.album,
                duration_ms=ns.duration_ms,
                genre=["pop"],  # 简化处理
                mood=mood_tags,
                energy=energy,
                tempo=100,  # 默认值
                source_url=f"https://music.163.com/song?id={ns.id}"
            )
            songs.append(song)
        
        # 根据时长限制筛选
        target_duration = criteria.get("duration_minutes", 30) * 60 * 1000
        selected = []
        current_duration = 0
        
        for song in songs:
            if current_duration + song.duration_ms <= target_duration:
                selected.append(song)
                current_duration += song.duration_ms
            if current_duration >= target_duration * 0.8:
                break
        
        return selected if selected else songs[:10]
    
    def _generate_playlist_name(self, criteria: Dict) -> str:
        """生成播放列表名称"""
        mood = criteria.get("mood")
        genres = criteria.get("genres", [])
        
        templates = [
            "Claudio 的 {mood}时光",
            "{mood}专用",
            "适合{mood}的歌单",
            "Claudio 精选：{mood}",
        ]
        
        mood_names = {
            Mood.FOCUS: "专注",
            Mood.RELAX: "放松",
            Mood.ENERGIZE: "提神",
            Mood.WORKOUT: "运动",
            Mood.SLEEP: "助眠",
            Mood.PARTY: "派对",
            Mood.COMMUTE: "通勤",
        }
        
        mood_name = mood_names.get(mood, "精选")
        template = random.choice(templates)
        
        return template.format(mood=mood_name)
    
    def _generate_playlist_description(self, criteria: Dict, context: Dict) -> str:
        """生成播放列表描述"""
        time_slot = self.get_current_time_slot()
        mood = criteria.get("mood")
        
        descriptions = {
            Mood.FOCUS: [
                "这些音乐能帮你进入心流状态，屏蔽干扰，专注当下。",
                "精选适合深度工作的背景音乐，不抢戏但足够好听。",
                "让大脑保持清醒，让注意力保持集中。",
            ],
            Mood.RELAX: [
                "放下紧绷的神经，让音乐带你进入放松的状态。",
                "适合休息、冥想或什么都不做的时候听。",
                "慢下来，深呼吸，享受这段宁静时光。",
            ],
            Mood.ENERGIZE: [
                "需要动力的时候，这些歌能给你能量。",
                "让节奏带动你的心跳，提神醒脑。",
                "适合需要爆发力的时刻。",
            ],
            Mood.SLEEP: [
                "轻柔的音乐，帮助你放松身心，进入梦乡。",
                "睡前聆听，让大脑慢慢安静下来。",
                "祝你有个好梦。",
            ],
        }
        
        if mood in descriptions:
            return random.choice(descriptions[mood])
        
        return "Claudio 为你精心挑选的音乐，希望你喜欢。"
    
    def get_current_song(self) -> Optional[Song]:
        """获取当前播放的歌曲"""
        if not self.current_playlist or not self.current_playlist.songs:
            return None
        
        if self.current_song_index < len(self.current_playlist.songs):
            return self.current_playlist.songs[self.current_song_index]
        return None
    
    def next_song(self) -> Optional[Song]:
        """下一首"""
        if not self.current_playlist:
            return None
        
        self.current_song_index += 1
        if self.current_song_index >= len(self.current_playlist.songs):
            self.current_song_index = 0  # 循环播放
        
        return self.get_current_song()
    
    def previous_song(self) -> Optional[Song]:
        """上一首"""
        if not self.current_playlist:
            return None
        
        self.current_song_index -= 1
        if self.current_song_index < 0:
            self.current_song_index = len(self.current_playlist.songs) - 1
        
        return self.get_current_song()
    
    def generate_song_intro(self, song: Song) -> str:
        """生成歌曲介绍"""
        intros = [
            f"接下来是 {song.artist} 的《{song.title}》。",
            f"这首歌来自 {song.artist}，歌名是《{song.title}》。",
            f"{song.artist} 的《{song.title}》，希望你喜欢。",
            f"下面这首歌是《{song.title}》，演唱者是 {song.artist}。",
        ]
        
        # 根据歌曲特点添加描述
        if song.energy > 0.7:
            intros.append(f"来一首节奏感强的，{song.artist} 的《{song.title}》。")
        elif song.energy < 0.3:
            intros.append(f"放慢节奏，听听 {song.artist} 的《{song.title}》。")
        
        return random.choice(intros)


# Telegram Bot 接口
class ClaudioTelegramBot:
    """Telegram Bot 封装"""
    
    def __init__(self, token: str):
        self.token = token
        self.curator = MusicCurator()
    
    def handle_message(self, message: str, user_id: str) -> Dict:
        """处理用户消息"""
        message = message.strip()
        
        # 命令处理
        if message.startswith("/"):
            return self._handle_command(message, user_id)
        
        # 自然语言请求
        return self._handle_natural_language(message, user_id)
    
    def _handle_command(self, command: str, user_id: str) -> Dict:
        """处理命令"""
        cmd = command.lower()
        
        if cmd == "/start":
            return {
                "type": "text",
                "content": """🎵 你好，我是 Claudio，你的 AI 音乐 DJ。

我可以根据你的心情、时间和场景，为你推荐最适合的音乐。

试试对我说：
• "我想听点适合写代码的歌"
• "给我一些放松的音乐"
• "提神醒脑的歌单"
• "助眠音乐，30分钟"

或者使用命令：
/now - 查看当前播放
/next - 下一首
/prev - 上一首
/status - 播放状态"""
            }
        
        elif cmd == "/now":
            song = self.curator.get_current_song()
            if song:
                return {
                    "type": "text",
                    "content": f"🎶 正在播放：\n《{song.title}》- {song.artist}\n专辑：{song.album}"
                }
            else:
                return {
                    "type": "text",
                    "content": "还没有播放列表，试试说\"我想听音乐\""
                }
        
        elif cmd in ["/next", "/skip"]:
            song = self.curator.next_song()
            if song:
                intro = self.curator.generate_song_intro(song)
                return {
                    "type": "text",
                    "content": f"⏭️ {intro}"
                }
            else:
                return {
                    "type": "text",
                    "content": "已经是最后一首了"
                }
        
        elif cmd == "/prev":
            song = self.curator.previous_song()
            if song:
                intro = self.curator.generate_song_intro(song)
                return {
                    "type": "text",
                    "content": f"⏮️ {intro}"
                }
            else:
                return {
                    "type": "text",
                    "content": "已经是第一首了"
                }
        
        elif cmd == "/status":
            playlist = self.curator.current_playlist
            if playlist:
                current = self.curator.current_song_index + 1
                total = len(playlist.songs)
                return {
                    "type": "text",
                    "content": f"📻 {playlist.name}\n第 {current}/{total} 首\n主题：{playlist.description[:50]}..."
                }
            else:
                return {
                    "type": "text",
                    "content": "当前没有播放列表"
                }
        
        else:
            return {
                "type": "text",
                "content": "未知命令，试试 /start 查看帮助"
            }
    
    def _handle_natural_language(self, message: str, user_id: str) -> Dict:
        """处理自然语言"""
        # 创建播放列表
        playlist = self.curator.create_playlist(message)
        
        # 生成 DJ 开场白
        context = {"user_request": message}
        dj_intro = self.curator.generate_dj_intro(context)
        
        # 构建回复
        songs_text = "\n".join([
            f"{i+1}. 《{song.title}》- {song.artist} ({song.duration_ms//60000}:{(song.duration_ms//1000)%60:02d})"
            for i, song in enumerate(playlist.songs[:5])  # 只显示前5首
        ])
        
        if len(playlist.songs) > 5:
            songs_text += f"\n... 还有 {len(playlist.songs) - 5} 首"
        
        total_minutes = playlist.total_duration_ms // 60000
        
        response = f"""{dj_intro}

🎵 {playlist.name}
{playlist.description}

📋 播放列表（约 {total_minutes} 分钟）：
{songs_text}

💬 随时告诉我：
• "换一批" - 重新生成
• "下一首" - 跳过当前
• "适合...的歌" - 新的推荐"""
        
        return {
            "type": "text",
            "content": response
        }


# 测试
if __name__ == "__main__":
    bot = ClaudioTelegramBot("test_token")
    
    # 测试自然语言
    test_messages = [
        "我想听点适合写代码的歌",
        "给我一些放松的音乐",
        "提神醒脑的歌单",
        "助眠音乐，30分钟",
    ]
    
    for msg in test_messages:
        print(f"\n用户: {msg}")
        response = bot.handle_message(msg, "test_user")
        print(f"Claudio: {response['content'][:200]}...")
