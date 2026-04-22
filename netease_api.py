#!/usr/bin/env python3
"""
网易云音乐 API 封装
基于 Binaryify/NeteaseCloudMusicApi
"""

import requests
import json
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class NeteaseSong:
    """网易云音乐歌曲"""
    id: int
    title: str
    artist: str
    album: str
    duration_ms: int
    cover_url: str
    mp3_url: str = ""
    
@dataclass
class NeteasePlaylist:
    """网易云音乐歌单"""
    id: int
    name: str
    description: str
    cover_url: str
    songs: List[NeteaseSong]
    play_count: int
    creator: str


class NeteaseMusicAPI:
    """网易云音乐 API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """发送请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise Exception(f"无法连接到网易云音乐 API，请确保服务已启动：{self.base_url}")
        except requests.exceptions.Timeout:
            raise Exception("请求超时，请检查网络连接")
        except Exception as e:
            raise Exception(f"API 请求失败: {str(e)}")
    
    def search_songs(self, keywords: str, limit: int = 20) -> List[NeteaseSong]:
        """搜索歌曲
        
        Args:
            keywords: 搜索关键词
            limit: 返回数量
            
        Returns:
            歌曲列表
        """
        result = self._request("/search", {
            "keywords": keywords,
            "type": 1,  # 歌曲搜索
            "limit": limit
        })
        
        songs = []
        if "result" in result and "songs" in result["result"]:
            for song_data in result["result"]["songs"]:
                song = NeteaseSong(
                    id=song_data["id"],
                    title=song_data["name"],
                    artist=", ".join([a["name"] for a in song_data.get("artists", [])]),
                    album=song_data.get("album", {}).get("name", ""),
                    duration_ms=song_data.get("duration", 0),
                    cover_url=song_data.get("album", {}).get("picUrl", "")
                )
                songs.append(song)
        
        return songs
    
    def search_playlists(self, keywords: str, limit: int = 10) -> List[Dict]:
        """搜索歌单"""
        result = self._request("/search", {
            "keywords": keywords,
            "type": 1000,  # 歌单搜索
            "limit": limit
        })
        
        playlists = []
        if "result" in result and "playlists" in result["result"]:
            for pl_data in result["result"]["playlists"]:
                playlist = {
                    "id": pl_data["id"],
                    "name": pl_data["name"],
                    "description": pl_data.get("description", ""),
                    "cover_url": pl_data.get("coverImgUrl", ""),
                    "play_count": pl_data.get("playCount", 0),
                    "creator": pl_data.get("creator", {}).get("nickname", "")
                }
                playlists.append(playlist)
        
        return playlists
    
    def get_playlist_detail(self, playlist_id: int) -> NeteasePlaylist:
        """获取歌单详情"""
        result = self._request("/playlist/detail", {
            "id": playlist_id
        })
        
        if "playlist" not in result:
            raise Exception("歌单不存在或无法访问")
        
        pl_data = result["playlist"]
        
        # 获取歌曲详情
        songs = []
        track_ids = [t["id"] for t in pl_data.get("trackIds", [])]
        
        # 批量获取歌曲 URL
        song_urls = self.get_song_urls(track_ids[:50])  # 最多50首
        
        for track in pl_data.get("tracks", [])[:50]:
            song_id = track["id"]
            song = NeteaseSong(
                id=song_id,
                title=track["name"],
                artist=", ".join([a["name"] for a in track.get("ar", [])]),
                album=track.get("al", {}).get("name", ""),
                duration_ms=track.get("dt", 0),
                cover_url=track.get("al", {}).get("picUrl", ""),
                mp3_url=song_urls.get(song_id, "")
            )
            songs.append(song)
        
        return NeteasePlaylist(
            id=pl_data["id"],
            name=pl_data["name"],
            description=pl_data.get("description", ""),
            cover_url=pl_data.get("coverImgUrl", ""),
            songs=songs,
            play_count=pl_data.get("playCount", 0),
            creator=pl_data.get("creator", {}).get("nickname", "")
        )
    
    def get_song_urls(self, song_ids: List[int]) -> Dict[int, str]:
        """获取歌曲播放链接"""
        if not song_ids:
            return {}
        
        ids_str = ",".join(map(str, song_ids))
        result = self._request("/song/url/v1", {
            "id": ids_str,
            "level": "standard"  # standard, higher, exhigh, lossless, hires
        })
        
        urls = {}
        if "data" in result:
            for song_data in result["data"]:
                song_id = song_data.get("id")
                url = song_data.get("url", "")
                if song_id and url:
                    urls[song_id] = url
        
        return urls
    
    def get_song_lyric(self, song_id: int) -> str:
        """获取歌词"""
        result = self._request("/lyric", {"id": song_id})
        
        # 优先获取翻译歌词，否则获取原歌词
        if "lrc" in result and "lyric" in result["lrc"]:
            return result["lrc"]["lyric"]
        return ""
    
    def get_user_playlists(self, uid: int, limit: int = 30) -> List[Dict]:
        """获取用户歌单"""
        result = self._request("/user/playlist", {
            "uid": uid,
            "limit": limit
        })
        
        playlists = []
        if "playlist" in result:
            for pl_data in result["playlist"]:
                playlist = {
                    "id": pl_data["id"],
                    "name": pl_data["name"],
                    "description": pl_data.get("description", ""),
                    "cover_url": pl_data.get("coverImgUrl", ""),
                    "play_count": pl_data.get("playCount", 0)
                }
                playlists.append(playlist)
        
        return playlists
    
    def get_recommend_songs(self) -> List[NeteaseSong]:
        """获取每日推荐歌曲（需要登录）"""
        result = self._request("/recommend/songs")
        
        songs = []
        if "data" in result and "dailySongs" in result["data"]:
            for song_data in result["data"]["dailySongs"]:
                song = NeteaseSong(
                    id=song_data["id"],
                    title=song_data["name"],
                    artist=", ".join([a["name"] for a in song_data.get("artists", [])]),
                    album=song_data.get("album", {}).get("name", ""),
                    duration_ms=song_data.get("duration", 0),
                    cover_url=song_data.get("album", {}).get("picUrl", "")
                )
                songs.append(song)
        
        return songs
    
    def search_by_mood(self, mood: str, limit: int = 20) -> List[NeteaseSong]:
        """根据情绪搜索歌曲
        
        将情绪映射到中文关键词进行搜索
        """
        mood_keywords = {
            "focus": "专注 学习 工作 纯音乐",
            "relax": "放松 轻音乐 治愈 安静",
            "energize": "提神 醒脑 活力 节奏",
            "workout": "运动 健身 跑步 动感",
            "sleep": "助眠 睡眠 冥想 轻音乐",
            "party": "派对 狂欢 嗨 夜店",
            "commute": "通勤 路上 车载 轻松",
        }
        
        keywords = mood_keywords.get(mood, mood)
        return self.search_songs(keywords, limit)
    
    def format_song_for_display(self, song: NeteaseSong, index: int = None) -> str:
        """格式化歌曲显示"""
        duration_min = song.duration_ms // 60000
        duration_sec = (song.duration_ms // 1000) % 60
        
        prefix = f"{index}. " if index else ""
        return f"{prefix}《{song.title}》- {song.artist} ({duration_min}:{duration_sec:02d})"


# 测试
if __name__ == "__main__":
    api = NeteaseMusicAPI()
    
    print("测试搜索歌曲...")
    try:
        songs = api.search_songs("周杰伦", limit=5)
        for i, song in enumerate(songs, 1):
            print(api.format_song_for_display(song, i))
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n测试搜索歌单...")
    try:
        playlists = api.search_playlists("工作 专注", limit=3)
        for pl in playlists:
            print(f"- {pl['name']} ({pl['play_count']} 次播放)")
    except Exception as e:
        print(f"错误: {e}")
