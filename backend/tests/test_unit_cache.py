"""Unit tests for the fail-soft cache and its circuit breaker (app/cache.py)."""
import pytest
import redis

from app import cache

pytestmark = pytest.mark.unit


class Clock:
    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now


class DeadRedis:
    """Stands in for an unreachable Redis and counts how often it is tried."""

    def __init__(self):
        self.calls = 0

    def _fail(self, *args, **kwargs):
        self.calls += 1
        raise redis.ConnectionError("simulated outage")

    get = setex = scan_iter = _fail


@pytest.fixture
def outage(monkeypatch):
    clock, dead = Clock(), DeadRedis()
    monkeypatch.setattr(cache, "time", clock)
    monkeypatch.setattr(cache, "client", lambda: dead)
    monkeypatch.setattr(cache, "_skip_until", 0.0)
    return clock, dead


def test_a_working_cache_round_trips_json():
    cache.set_json("k", {"a": [1, 2]}, ttl_seconds=30)
    assert cache.get_json("k") == {"a": [1, 2]}
    cache.invalidate("k")
    assert cache.get_json("k") is None


def test_an_outage_looks_like_a_miss_and_never_raises(outage):
    assert cache.get_json("k") is None
    cache.set_json("k", {"a": 1})
    cache.invalidate("k*")


def test_after_one_failure_redis_is_skipped_for_the_breaker_window(outage):
    clock, dead = outage
    cache.get_json("k")
    assert dead.calls == 1
    for _ in range(5):                                   # dashboard polls during the outage
        cache.get_json("k")
        cache.set_json("k", 1)
        cache.invalidate("k*")
    assert dead.calls == 1                               # none of them waited on Redis


def test_redis_is_retried_once_the_window_has_passed(outage):
    clock, dead = outage
    cache.get_json("k")
    clock.now += cache.BREAKER_SECONDS - 0.1
    cache.get_json("k")
    assert dead.calls == 1
    clock.now += 0.2
    cache.get_json("k")
    assert dead.calls == 2
