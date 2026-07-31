"""Shared query helpers used by both the API and the probe worker."""
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Check, Incident, Monitor, User


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "monitor"


def unique_slug(db: Session, owner_id: int, name: str) -> str:
    base = slugify(name)
    candidate, suffix = base, 2
    while db.scalar(
        select(Monitor.id).where(Monitor.owner_id == owner_id, Monitor.slug == candidate)
    ):
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def rollup(db: Session, monitor_id: int, hours: int = 24) -> dict:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    total, passed, avg_latency = db.execute(
        select(
            func.count(Check.id),
            func.count(Check.id).filter(Check.ok.is_(True)),
            func.avg(Check.latency_ms).filter(Check.ok.is_(True)),
        ).where(Check.monitor_id == monitor_id, Check.checked_at >= since)
    ).one()
    return {
        "uptime_24h": round(passed / total * 100, 2) if total else None,
        "avg_latency_ms": round(float(avg_latency), 1) if avg_latency else None,
        "checks_counted": total,
    }


def open_incident(db: Session, monitor_id: int) -> Incident | None:
    return db.scalar(
        select(Incident).where(
            Incident.monitor_id == monitor_id, Incident.resolved_at.is_(None)
        )
    )


def unique_handle(db: Session, email: str) -> str:
    base = slugify(email.split("@")[0])
    candidate, suffix = base, 2
    while db.scalar(select(User.id).where(User.handle == candidate)):
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate
