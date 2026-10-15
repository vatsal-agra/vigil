"""Regression suite: one test per defect fixed or contract that must never break again.

Run on its own with `pytest -m regression`. Each test names the defect or
acceptance criterion it guards, so a red test says what came back.
"""
from datetime import datetime, timedelta

import pytest

from app.models import Incident
from app.probe import apply_result, due_monitors, run_cycle
from helpers import ago, failed

pytestmark = pytest.mark.regression


def test_R1_open_incident_beyond_the_feed_cap_is_still_reported(client, signup, db):
    """Review 2 defect (commit 82be0dd): the dashboard showed 'Open incidents: 0'
    while a monitor was down, because the open incident was older than the newest
    100 rows of the capped feed. The fix relies on ?open_only=true reaching it."""
    auth, _ = signup()
    mid = client.post("/api/monitors", headers=auth, json={"name": "Legacy", "url": "https://l.test/"}).json()["id"]
    db.add(Incident(monitor_id=mid, cause="still broken", started_at=ago(days=30)))
    db.add_all([Incident(monitor_id=mid, cause=f"blip {n}", started_at=ago(hours=n), resolved_at=ago(hours=n) + timedelta(minutes=2))
                for n in range(1, 106)])
    db.commit()

    feed = client.get("/api/incidents", headers=auth).json()
    assert len(feed) == 100 and all(i["resolved_at"] for i in feed)      # the cap hides it ...
    [still_open] = client.get("/api/incidents?open_only=true", headers=auth).json()
    assert still_open["cause"] == "still broken"                         # ... the open-only query does not


def test_R2_a_single_failed_check_never_opens_an_incident(db, make_monitor):
    """US-13 AC3, the flap guard: one bad check is noise."""
    m = make_monitor()
    apply_result(db, m, failed(m.id))
    assert db.query(Incident).count() == 0


def test_R3_foreign_resources_are_404_not_403(client, signup):
    """US-04 AC2: a 403 would confirm that the monitor exists."""
    alice, _ = signup("alice@example.com")
    bob, _ = signup("bob@example.com")
    mid = client.post("/api/monitors", headers=alice, json={"name": "A", "url": "https://a.test/"}).json()["id"]
    assert client.get(f"/api/monitors/{mid}", headers=bob).status_code == 404


def test_R4_naive_timestamps_do_not_crash_the_scheduler(db, make_monitor):
    """due_monitors() must accept a last_checked_at without tzinfo (older rows, other drivers)."""
    m = make_monitor(interval_seconds=60)
    m.last_checked_at = datetime.utcnow() - timedelta(minutes=5)          # naive on purpose
    assert [x.id for x in due_monitors(db)] == [m.id]


def test_R5_the_public_page_never_leaks_urls_or_raw_errors(client, signup, db):
    """US-16 AC3."""
    auth, account = signup()
    client.post("/api/monitors", headers=auth,
                json={"name": "Payments", "url": "https://internal.secret/admin", "is_public": True})
    body = client.get(f"/api/status/{account['handle']}").text
    assert "internal.secret" not in body
    assert "error" not in body and "url" not in body


def test_R6_interval_bounds_are_enforced_on_update_as_well_as_create(client, signup):
    """US-07 AC2: the clamp must hold on PATCH, not only on POST."""
    auth, _ = signup()
    mid = client.post("/api/monitors", headers=auth, json={"name": "A", "url": "https://a.test/"}).json()["id"]
    assert client.patch(f"/api/monitors/{mid}", headers=auth, json={"interval_seconds": 5}).status_code == 422


def test_R7_run_cycle_never_closes_a_client_it_was_given(db, make_monitor, fake_web):
    """Review 3 refactor: run_cycle() accepts an injected client and must leave it open."""
    make_monitor(url="https://a.test/")
    web = fake_web({"https://a.test/": 200})
    run_cycle(db, web)
    assert web.is_closed is False
