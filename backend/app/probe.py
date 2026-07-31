"""One probe cycle: check due monitors, record results, open/close incidents."""
import logging
import time
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import cache
from app.config import settings
from app.models import Check, Incident, Monitor
from app.services import open_incident

log = logging.getLogger("vigil.probe")


def due_monitors(db: Session) -> list[Monitor]:
    now = datetime.now(timezone.utc)
    monitors = db.scalars(select(Monitor).where(Monitor.is_active.is_(True))).all()
    due = []
    for monitor in monitors:
        if monitor.last_checked_at is None:
            due.append(monitor)
            continue
        last = monitor.last_checked_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if now - last >= timedelta(seconds=monitor.interval_seconds):
            due.append(monitor)
    return due


def probe_once(client: httpx.Client, monitor: Monitor) -> Check:
    started = time.perf_counter()
    try:
        response = client.request(
            monitor.method, monitor.url, timeout=settings.probe_timeout_seconds
        )
        latency = (time.perf_counter() - started) * 1000
        return Check(
            monitor_id=monitor.id,
            status_code=response.status_code,
            latency_ms=round(latency, 1),
            ok=response.status_code == monitor.expected_status,
            error=None
            if response.status_code == monitor.expected_status
            else f"Expected {monitor.expected_status}, got {response.status_code}",
        )
    except httpx.TimeoutException:
        return Check(
            monitor_id=monitor.id,
            status_code=None,
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
            ok=False,
            error=f"No response within {settings.probe_timeout_seconds:.0f}s",
        )
    except httpx.HTTPError as exc:
        return Check(
            monitor_id=monitor.id,
            status_code=None,
            latency_ms=None,
            ok=False,
            error=f"Connection failed: {type(exc).__name__}",
        )


def apply_result(db: Session, monitor: Monitor, check: Check) -> None:
    monitor.last_checked_at = datetime.now(timezone.utc)

    if check.ok:
        monitor.consecutive_failures = 0
        slow = check.latency_ms is not None and check.latency_ms > 2000
        monitor.current_status = "degraded" if slow else "up"
        incident = open_incident(db, monitor.id)
        if incident is not None:
            incident.resolved_at = datetime.now(timezone.utc)
            minutes = (incident.resolved_at - incident.started_at).total_seconds() / 60
            incident.summary = (
                f"{monitor.name} recovered after {minutes:.0f} min. "
                f"Trigger: {incident.cause}. Now answering in {check.latency_ms:.0f} ms."
            )
    else:
        monitor.consecutive_failures += 1
        if monitor.consecutive_failures >= settings.failure_threshold:
            monitor.current_status = "down"
            if open_incident(db, monitor.id) is None:
                db.add(
                    Incident(
                        monitor_id=monitor.id,
                        cause=check.error or "check failed",
                        summary=None,
                    )
                )

    db.add(check)
    db.commit()
    cache.invalidate(f"monitors:list:{monitor.owner_id}")
    cache.invalidate(f"monitors:checks:{monitor.id}:*")
    cache.invalidate("status:public:*")


def run_cycle(db: Session) -> int:
    monitors = due_monitors(db)
    if not monitors:
        return 0
    with httpx.Client(follow_redirects=True) as client:
        for monitor in monitors:
            result = probe_once(client, monitor)
            apply_result(db, monitor, result)
            log.info(
                "checked %s -> %s (%s ms)",
                monitor.name,
                "ok" if result.ok else "fail",
                result.latency_ms,
            )
    return len(monitors)
