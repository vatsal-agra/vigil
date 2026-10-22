"""Redis access for the response cache. The cache is optional: every function
here fails soft, so a Redis outage degrades speed, never correctness.

A small circuit breaker keeps an outage cheap. When Redis is unreachable, the
first call can take seconds (the stopped host's name has to time out in DNS
before a connection is even tried). After any failure the cache is skipped
for BREAKER_SECONDS, so only one request per window pays that cost.
"""
import json
import time
from typing import Any

import redis

from app.config import settings

BREAKER_SECONDS = 30.0

_client: redis.Redis | None = None
_skip_until = 0.0


def client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def _available() -> bool:
    return time.monotonic() >= _skip_until


def _trip() -> None:
    global _skip_until
    _skip_until = time.monotonic() + BREAKER_SECONDS


def get_json(key: str) -> Any | None:
    if not _available():
        return None
    try:
        raw = client().get(key)
    except redis.RedisError:
        _trip()
        return None
    return json.loads(raw) if raw else None


def set_json(key: str, value: Any, ttl_seconds: int = 30) -> None:
    if not _available():
        return
    try:
        client().setex(key, ttl_seconds, json.dumps(value, default=str))
    except redis.RedisError:
        _trip()


def invalidate(pattern: str) -> None:
    if not _available():
        return
    try:
        conn = client()
        for key in conn.scan_iter(match=pattern, count=200):
            conn.delete(key)
    except redis.RedisError:
        _trip()
