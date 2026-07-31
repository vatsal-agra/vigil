from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import cache
from app.db import get_db
from app.models import Check, Monitor, User
from app.schemas import CheckOut, MonitorIn, MonitorOut, MonitorPatch
from app.security import current_user
from app.services import rollup, unique_slug

router = APIRouter(prefix="/api/monitors", tags=["monitors"])

LIST_TTL = 15
SERIES_TTL = 30


def _owned(db: Session, monitor_id: int, user: User) -> Monitor:
    monitor = db.get(Monitor, monitor_id)
    if monitor is None or monitor.owner_id != user.id:
        raise HTTPException(status_code=404, detail="No monitor with that id.")
    return monitor


@router.get("", response_model=list[MonitorOut])
def list_monitors(db: Session = Depends(get_db), user: User = Depends(current_user)):
    key = f"monitors:list:{user.id}"
    cached = cache.get_json(key)
    if cached is not None:
        return cached

    monitors = db.scalars(
        select(Monitor).where(Monitor.owner_id == user.id).order_by(Monitor.id)
    ).all()
    payload = []
    for monitor in monitors:
        item = MonitorOut.model_validate(monitor).model_dump()
        item.update(
            {k: v for k, v in rollup(db, monitor.id).items() if k != "checks_counted"}
        )
        payload.append(item)
    cache.set_json(key, payload, LIST_TTL)
    return payload


@router.post("", response_model=MonitorOut, status_code=status.HTTP_201_CREATED)
def create_monitor(
    body: MonitorIn, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    monitor = Monitor(
        owner_id=user.id,
        name=body.name,
        slug=unique_slug(db, user.id, body.name),
        url=body.url,
        method=body.method.upper(),
        expected_status=body.expected_status,
        interval_seconds=body.interval_seconds,
        is_public=body.is_public,
    )
    db.add(monitor)
    db.commit()
    cache.invalidate(f"monitors:list:{user.id}")
    return MonitorOut.model_validate(monitor)


@router.get("/{monitor_id}", response_model=MonitorOut)
def get_monitor(
    monitor_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    monitor = _owned(db, monitor_id, user)
    item = MonitorOut.model_validate(monitor).model_dump()
    item.update({k: v for k, v in rollup(db, monitor.id).items() if k != "checks_counted"})
    return item


@router.patch("/{monitor_id}", response_model=MonitorOut)
def update_monitor(
    monitor_id: int,
    body: MonitorPatch,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    monitor = _owned(db, monitor_id, user)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(monitor, field, value)
    db.commit()
    cache.invalidate(f"monitors:*:{user.id}")
    return MonitorOut.model_validate(monitor)


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_monitor(
    monitor_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    monitor = _owned(db, monitor_id, user)
    db.delete(monitor)
    db.commit()
    cache.invalidate(f"monitors:list:{user.id}")


@router.get("/{monitor_id}/checks", response_model=list[CheckOut])
def monitor_checks(
    monitor_id: int,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    monitor = _owned(db, monitor_id, user)
    key = f"monitors:checks:{monitor.id}:{hours}"
    cached = cache.get_json(key)
    if cached is not None:
        return cached

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = db.scalars(
        select(Check)
        .where(Check.monitor_id == monitor.id, Check.checked_at >= since)
        .order_by(Check.checked_at.desc())
        .limit(300)
    ).all()
    payload = [CheckOut.model_validate(row).model_dump() for row in reversed(rows)]
    cache.set_json(key, payload, SERIES_TTL)
    return payload
