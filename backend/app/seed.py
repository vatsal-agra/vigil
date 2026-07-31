"""Creates a demo account with monitors and backfilled history for screenshots."""
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Check, Incident, Monitor, User
from app.security import hash_password

DEMO_EMAIL = "demo@vigil.dev"
DEMO_HANDLE = "demo"
DEMO_PASSWORD = "vigil-demo-2026"

FIXTURES = [
    ("Marketing site", "https://example.com", 60, True, "up"),
    ("Checkout API", "https://httpbin.org/status/200", 60, True, "up"),
    ("Search service", "https://httpbin.org/delay/3", 120, True, "degraded"),
    ("Legacy invoice worker", "https://httpbin.org/status/503", 60, False, "down"),
]


def seed(db: Session) -> None:
    if db.scalar(select(User).where(User.email == DEMO_EMAIL)):
        return

    user = User(
        email=DEMO_EMAIL,
        handle=DEMO_HANDLE,
        password_hash=hash_password(DEMO_PASSWORD),
    )
    db.add(user)
    db.flush()

    now = datetime.now(timezone.utc)
    for name, url, interval, is_public, status in FIXTURES:
        monitor = Monitor(
            owner_id=user.id,
            name=name,
            slug=name.lower().replace(" ", "-"),
            url=url,
            interval_seconds=interval,
            is_public=is_public,
            current_status=status,
            last_checked_at=now,
        )
        db.add(monitor)
        db.flush()

        base = {"up": 180, "degraded": 2400, "down": 900}[status]
        for step in range(96):
            when = now - timedelta(minutes=15 * (96 - step))
            failing = status == "down" and step > 80
            db.add(
                Check(
                    monitor_id=monitor.id,
                    checked_at=when,
                    status_code=None if failing else 200,
                    latency_ms=None if failing else round(random.gauss(base, base * 0.18), 1),
                    ok=not failing,
                    error="Connection failed: ConnectError" if failing else None,
                )
            )

        if status == "down":
            db.add(
                Incident(
                    monitor_id=monitor.id,
                    started_at=now - timedelta(minutes=225),
                    cause="Expected 200, got 503",
                )
            )

    db.commit()
