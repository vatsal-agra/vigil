"""Integration test of the full outage lifecycle across API, worker, database and cache.

A monitor is created through the API, the worker's run_cycle() probes a fake
target that goes down and comes back, and the outcome is read back through
the dashboard API and the public status page: the same path a real outage takes.
"""
import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration

URL = "https://shop.test/health"


def make_due(db):
    """Skip the wait: mark every monitor as never checked."""
    db.execute(text("UPDATE monitors SET last_checked_at = NULL"))
    db.commit()
    db.expire_all()


def test_an_outage_is_detected_recorded_and_explained_end_to_end(client, signup, db, fake_web):
    from app.probe import run_cycle

    auth, account = signup()
    mid = client.post("/api/monitors", headers=auth,
                      json={"name": "Checkout API", "url": URL, "is_public": True}).json()["id"]

    # warm the caches the way a browser would, so invalidation is exercised too
    assert client.get("/api/monitors", headers=auth).json()[0]["current_status"] == "pending"
    assert client.get(f"/api/status/{account['handle']}").json()["overall"] == "operational"

    # the target starts failing: one failure is tolerated, the second opens an incident
    run_cycle(db, fake_web({URL: 503}))
    assert client.get("/api/incidents?open_only=true", headers=auth).json() == []
    make_due(db)
    run_cycle(db, fake_web({URL: 503}))

    assert client.get(f"/api/monitors/{mid}", headers=auth).json()["current_status"] == "down"
    [incident] = client.get("/api/incidents?open_only=true", headers=auth).json()
    assert incident["cause"] == "Expected 200, got 503"
    assert client.get(f"/api/status/{account['handle']}").json()["overall"] == "major outage"

    # the target recovers: the incident closes itself with a plain-English summary
    make_due(db)
    run_cycle(db, fake_web({URL: 200}))

    assert client.get("/api/monitors", headers=auth).json()[0]["current_status"] == "up"
    assert client.get("/api/incidents?open_only=true", headers=auth).json() == []
    [resolved] = client.get("/api/incidents", headers=auth).json()
    assert resolved["summary"].startswith("Checkout API recovered after")
    assert client.get(f"/api/status/{account['handle']}").json()["overall"] == "operational"
    series = client.get(f"/api/monitors/{mid}/checks", headers=auth).json()
    assert [c["ok"] for c in series] == [False, False, True]


def test_a_slow_target_degrades_the_public_banner(client, signup, db, fake_web, monkeypatch):
    from app import probe

    auth, account = signup()
    client.post("/api/monitors", headers=auth, json={"name": "Search", "url": URL, "is_public": True})
    clock = iter([0.0, 2.5])                                   # a 2.5 s response, only as probe.py sees it
    monkeypatch.setattr(probe, "time", type("Clock", (), {"perf_counter": staticmethod(lambda: next(clock))}))
    probe.run_cycle(db, fake_web({URL: 200}))
    page = client.get(f"/api/status/{account['handle']}").json()
    assert page["overall"] == "degraded"
    assert page["services"][0]["status"] == "degraded"
