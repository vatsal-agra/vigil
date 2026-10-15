"""Integration tests: the HTTP API with the real database, cache and auth.

Requests go through FastAPI's full stack (routing, validation, dependencies,
SQLAlchemy, PostgreSQL, Redis) via TestClient. Each test maps to one or more
acceptance criteria in docs/user-stories.md.
"""
import pytest
from sqlalchemy import text

from app.models import Check, Incident
from helpers import ago

pytestmark = pytest.mark.integration


# ------------------------------------------------------------------ accounts (US-01..04)

def test_register_signs_the_user_in(client):
    r = client.post("/api/auth/register", json={"email": "rhea@example.com", "password": "correct-horse-1"})
    assert r.status_code == 201
    body = r.json()
    assert body["handle"] == "rhea"
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.json()["email"] == "rhea@example.com"


def test_duplicate_email_is_a_409_with_a_readable_message(client, signup):
    signup()
    r = client.post("/api/auth/register", json={"email": "rhea@example.com", "password": "another-pass"})
    assert r.status_code == 409
    assert r.json()["detail"] == "That email already has an account."


def test_short_passwords_are_rejected(client):
    r = client.post("/api/auth/register", json={"email": "a@example.com", "password": "short"})
    assert r.status_code == 422


def test_login_does_not_reveal_whether_an_email_exists(client, signup):
    signup()
    wrong_pw = client.post("/api/auth/login", json={"email": "rhea@example.com", "password": "nope-nope-nope"})
    no_user = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "nope-nope-nope"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json()


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer not-a-real-token"}])
def test_protected_routes_require_a_valid_token(client, headers):
    assert client.get("/api/monitors", headers=headers).status_code == 401


# ------------------------------------------------------------------ monitors (US-05..12)

def test_a_new_monitor_needs_only_a_name_and_url(client, signup):
    auth, _ = signup()
    r = client.post("/api/monitors", headers=auth, json={"name": "Checkout API", "url": "https://shop.test/health"})
    assert r.status_code == 201
    m = r.json()
    assert (m["method"], m["expected_status"], m["interval_seconds"]) == ("GET", 200, 60)
    assert m["current_status"] == "pending"
    assert m["is_public"] is False
    assert m["slug"] == "checkout-api"


@pytest.mark.parametrize("interval, code", [(29, 422), (30, 201), (3600, 201), (3601, 422)])
def test_interval_is_clamped_to_30_through_3600_seconds(client, signup, interval, code):
    auth, _ = signup()
    r = client.post("/api/monitors", headers=auth,
                    json={"name": f"m{interval}", "url": "https://x.test/", "interval_seconds": interval})
    assert r.status_code == code


def test_the_list_carries_uptime_and_latency_per_monitor(client, signup, db):
    auth, _ = signup()
    mid = client.post("/api/monitors", headers=auth, json={"name": "A", "url": "https://a.test/"}).json()["id"]
    db.add_all([Check(monitor_id=mid, ok=True, latency_ms=100.0, checked_at=ago(minutes=5)),
                Check(monitor_id=mid, ok=False, latency_ms=None, checked_at=ago(minutes=4))])
    db.commit()
    [row] = client.get("/api/monitors", headers=auth).json()
    assert row["uptime_24h"] == 50.0
    assert row["avg_latency_ms"] == 100.0


def test_another_users_monitor_is_a_404_for_every_verb(client, signup):
    alice, _ = signup("alice@example.com")
    bob, _ = signup("bob@example.com")
    mid = client.post("/api/monitors", headers=alice, json={"name": "A", "url": "https://a.test/"}).json()["id"]
    assert client.get(f"/api/monitors/{mid}", headers=bob).status_code == 404
    assert client.patch(f"/api/monitors/{mid}", headers=bob, json={"name": "pwned"}).status_code == 404
    assert client.delete(f"/api/monitors/{mid}", headers=bob).status_code == 404
    assert client.get("/api/monitors", headers=bob).json() == []
    assert client.get(f"/api/monitors/{mid}", headers=alice).json()["name"] == "A"


def test_pausing_a_monitor_takes_it_out_of_the_probe_schedule(client, signup, db):
    from app.probe import due_monitors

    auth, _ = signup()
    mid = client.post("/api/monitors", headers=auth, json={"name": "A", "url": "https://a.test/"}).json()["id"]
    assert [m.id for m in due_monitors(db)] == [mid]
    client.patch(f"/api/monitors/{mid}", headers=auth, json={"is_active": False})
    db.expire_all()
    assert due_monitors(db) == []


def test_deleting_a_monitor_cascades_to_its_checks_and_incidents(client, signup, db):
    auth, _ = signup()
    mid = client.post("/api/monitors", headers=auth, json={"name": "A", "url": "https://a.test/"}).json()["id"]
    db.add_all([Check(monitor_id=mid, ok=False), Incident(monitor_id=mid, cause="x")])
    db.commit()
    assert client.delete(f"/api/monitors/{mid}", headers=auth).status_code == 204
    counts = db.execute(text("SELECT (SELECT count(*) FROM checks), (SELECT count(*) FROM incidents)")).one()
    assert tuple(counts) == (0, 0)


def test_the_series_endpoint_returns_checks_oldest_first(client, signup, db):
    auth, _ = signup()
    mid = client.post("/api/monitors", headers=auth, json={"name": "A", "url": "https://a.test/"}).json()["id"]
    db.add_all([Check(monitor_id=mid, ok=True, latency_ms=float(n), checked_at=ago(minutes=n)) for n in (1, 3, 2)])
    db.commit()
    series = client.get(f"/api/monitors/{mid}/checks", headers=auth).json()
    assert [c["latency_ms"] for c in series] == [3.0, 2.0, 1.0]
    assert client.get(f"/api/monitors/{mid}/checks?hours=0", headers=auth).status_code == 422


# ------------------------------------------------------------------ incidents (US-15, US-18)

def test_the_incident_feed_filters_and_acknowledges(client, signup, db):
    auth, _ = signup()
    other, _ = signup("bob@example.com")
    mid = client.post("/api/monitors", headers=auth, json={"name": "A", "url": "https://a.test/"}).json()["id"]
    db.add_all([Incident(monitor_id=mid, cause="old", resolved_at=ago(hours=1), started_at=ago(hours=2)),
                Incident(monitor_id=mid, cause="now")])
    db.commit()

    assert len(client.get("/api/incidents", headers=auth).json()) == 2
    [open_one] = client.get("/api/incidents?open_only=true", headers=auth).json()
    assert open_one["cause"] == "now" and open_one["monitor_name"] == "A"

    assert client.post(f"/api/incidents/{open_one['id']}/acknowledge", headers=other).status_code == 404
    acked = client.post(f"/api/incidents/{open_one['id']}/acknowledge", headers=auth).json()
    assert acked["acknowledged"] is True
    assert acked["resolved_at"] is None          # acknowledging does not resolve


# ------------------------------------------------------------------ public status (US-16, US-17)

def test_the_status_page_shows_only_public_monitors_without_auth(client, signup):
    auth, account = signup()
    client.post("/api/monitors", headers=auth, json={"name": "Public API", "url": "https://p.test/", "is_public": True})
    client.post("/api/monitors", headers=auth, json={"name": "Internal DB", "url": "https://i.test/"})
    page = client.get(f"/api/status/{account['handle']}").json()
    assert [s["name"] for s in page["services"]] == ["Public API"]
    assert page["overall"] == "operational"


def test_an_unknown_status_page_is_a_404(client):
    r = client.get("/api/status/nobody")
    assert r.status_code == 404
    assert r.json()["detail"] == "No status page at that address."


# ------------------------------------------------------------------ operations (US-24)

def test_health_reports_each_dependency(client):
    assert client.get("/health").json() == {"status": "ok", "api": "ok", "database": "ok", "cache": "ok"}
