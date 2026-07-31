import json
from typing import Any

import redis

from app.config import settings

_client: redis.Redis | None = None


def client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def get_json(key: str) -> Any | None:
    try:
        raw = client().get(key)
    except redis.RedisError:
        return None
    return json.loads(raw) if raw else None


def set_json(key: str, value: Any, ttl_seconds: int = 30) -> None:
    try:
        client().setex(key, ttl_seconds, json.dumps(value, default=str))
    except redis.RedisError:
        pass


def invalidate(pattern: str) -> None:
    try:
        conn = client()
        for key in conn.scan_iter(match=pattern, count=200):
            conn.delete(key)
    except redis.RedisError:
        pass
