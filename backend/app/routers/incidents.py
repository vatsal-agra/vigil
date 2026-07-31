from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Incident, Monitor, User
from app.schemas import IncidentOut
from app.security import current_user

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    open_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    stmt = (
        select(Incident, Monitor.name)
        .join(Monitor, Monitor.id == Incident.monitor_id)
        .where(Monitor.owner_id == user.id)
        .order_by(Incident.started_at.desc())
        .limit(100)
    )
    if open_only:
        stmt = stmt.where(Incident.resolved_at.is_(None))

    results = []
    for incident, monitor_name in db.execute(stmt).all():
        item = IncidentOut.model_validate(incident)
        item.monitor_name = monitor_name
        results.append(item)
    return results


@router.post("/{incident_id}/acknowledge", response_model=IncidentOut)
def acknowledge(
    incident_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    incident = db.get(Incident, incident_id)
    if incident is None or incident.monitor.owner_id != user.id:
        raise HTTPException(status_code=404, detail="No incident with that id.")
    incident.acknowledged = True
    db.commit()
    item = IncidentOut.model_validate(incident)
    item.monitor_name = incident.monitor.name
    return item
