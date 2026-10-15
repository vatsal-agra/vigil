"""Small builders shared by the test modules."""
from datetime import datetime, timedelta, timezone

from app.models import Check


def failed(monitor_id: int, error: str = "Expected 200, got 503") -> Check:
    return Check(monitor_id=monitor_id, status_code=503, latency_ms=120.0, ok=False, error=error)


def passed(monitor_id: int, latency_ms: float = 150.0) -> Check:
    return Check(monitor_id=monitor_id, status_code=200, latency_ms=latency_ms, ok=True, error=None)


def ago(**kwargs) -> datetime:
    return datetime.now(timezone.utc) - timedelta(**kwargs)
