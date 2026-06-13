"""AI 剧本杀 - Redis 缓存管理"""
from __future__ import annotations
import json
import logging
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis 缓存层：会话状态、排行榜、在线人数"""

    def __init__(self):
        self._client = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            if settings.REDIS_URL and settings.REDIS_URL.startswith(("redis-cli")):
                self._client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    ssl_cert_reqs=None,  # Upstash TLS
                )
            else:
                # 本地开发或 URL 无效时用内存字典模拟
                logger.warning("REDIS_URL 无效或未配置，降级为 FakeRedis（内存模式，进程重启后数据丢失）")
                self._client = FakeRedis()
        return self._client

    # ---- 会话管理 ----
    def save_session(self, game_id: str, data: dict, ttl: int = 3600):
        """保存游戏会话，默认1小时过期"""
        self.client.setex(f"session:{game_id}", ttl, json.dumps(data, ensure_ascii=False))

    def get_session(self, game_id: str):
        raw = self.client.get(f"session:{game_id}")
        return json.loads(raw) if raw else None

    def delete_session(self, game_id: str):
        self.client.delete(f"session:{game_id}")

    # ---- 排行榜 ----
    def update_leaderboard(self, nickname: str, score: float):
        self.client.zadd("leaderboard:scores", {nickname: score})

    def get_leaderboard(self, top_n: int = 10) -> list[dict]:
        results = self.client.zrevrange("leaderboard:scores", 0, top_n - 1, withscores=True)
        return [{"nickname": name, "score": score} for name, score in results]

    # ---- 在线人数 ----
    def incr_online(self) -> int:
        return self.client.incr("stats:online")

    def decr_online(self) -> int:
        return self.client.decr("stats:online")

    def get_online_count(self) -> int:
        val = self.client.get("stats:online")
        return int(val) if val else 0


class FakeRedis:
    """本地开发用：内存字典模拟 Redis"""

    def __init__(self):
        self._store = {}
        self._expiry = {}

    def setex(self, key, ttl, value):
        self._store[key] = value
        self._expiry[key] = ttl

    def get(self, key):
        return self._store.get(key)

    def delete(self, key):
        self._store.pop(key, None)

    def zadd(self, key, mapping):
        if key not in self._store:
            self._store[key] = {}
        self._store[key].update(mapping)

    def zrevrange(self, key, start, end, withscores=False):
        if key not in self._store:
            return []
        items = sorted(self._store[key].items(), key=lambda x: x[1], reverse=True)
        items = items[start:end + 1]
        if withscores:
            return items
        return [name for name, _ in items]

    def incr(self, key):
        val = int(self._store.get(key, 0)) + 1
        self._store[key] = str(val)
        return val

    def decr(self, key):
        val = int(self._store.get(key, 0)) - 1
        self._store[key] = str(val)
        return val


redis_mgr = RedisManager()
