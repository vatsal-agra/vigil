"""Unauthenticated public status page feed, heavily cached."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import cache
from app.db import get_db
from app.models import Monitor, User
from app.services import rollup

router = APIRouter(prefix="/api/status", tags=["status"])

PUBLIC_TTL = 20


@router.get("/{handle}")
def public_status(handle: str, db: Session = Depends(get_db)):
    key = f"status:public:{handle}"
    cached = cache.get_json(key)
    if cached is not None:
        return cached

    user = db.scalar(select(User).where(User.handle == handle))
    if user is None:
        raise HTTPException(status_code=404, detail="No status page at that address.")

    monitors = db.scalars(
        select(Monitor)
        .where(Monitor.owner_id == user.id, Monitor.is_public.is_(True))
        .order_by(Monitor.name)
    ).all()

    services = []
    for monitor in monitors:
        stats = rollup(db, monitor.id)
        services.append(
            {
                "name": monitor.name,
                "slug": monitor.slug,
                "status": monitor.current_status,
                "uptime_24h": stats["uptime_24h"],
                "avg_latency_ms": stats["avg_latency_ms"],
            }
        )

    overall = "operational"
    if any(s["status"] == "down" for s in services):
        overall = "major outage"
    elif any(s["status"] == "degraded" for s in services):
        overall = "degraded"

    payload = {"handle": handle, "overall": overall, "services": services}
    cache.set_json(key, payload, PUBLIC_TTL)
    return payload
