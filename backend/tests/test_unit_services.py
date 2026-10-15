"""Unit tests for the shared query helpers (app/services.py)."""
import pytest

from app.models import Check, Incident, User
from app.services import open_incident, rollup, slugify, unique_handle, unique_slug
from helpers import ago

pytestmark = pytest.mark.unit


def add_checks(db, monitor_id, *specs):
    for ok, latency, when in specs:
        db.add(Check(monitor_id=monitor_id, ok=ok, latency_ms=latency, checked_at=when,
                     status_code=200 if ok else 503))
    db.commit()


def test_rollup_computes_uptime_and_average_latency_of_successes(db, make_monitor):
    m = make_monitor()
    add_checks(db, m.id, (True, 100.0, ago(hours=1)), (True, 200.0, ago(hours=2)),
               (True, 300.0, ago(hours=3)), (False, 9000.0, ago(hours=4)))
    assert rollup(db, m.id) == {"uptime_24h": 75.0, "avg_latency_ms": 200.0, "checks_counted": 4}


def test_rollup_ignores_checks_older_than_the_window(db, make_monitor):
    m = make_monitor()
    add_checks(db, m.id, (True, 100.0, ago(hours=1)), (False, None, ago(hours=30)))
    assert rollup(db, m.id)["uptime_24h"] == 100.0
    assert rollup(db, m.id, hours=48)["uptime_24h"] == 50.0


def test_rollup_rounds_uptime_to_two_decimals(db, make_monitor):
    m = make_monitor()
    add_checks(db, m.id, *[(True, 100.0, ago(minutes=i + 1)) for i in range(2)],
               (False, None, ago(minutes=5)))
    assert rollup(db, m.id)["uptime_24h"] == 66.67


def test_rollup_of_an_unchecked_monitor_is_empty_not_zero(db, make_monitor):
    m = make_monitor()
    assert rollup(db, m.id) == {"uptime_24h": None, "avg_latency_ms": None, "checks_counted": 0}


def test_open_incident_returns_only_the_unresolved_one(db, make_monitor):
    m = make_monitor()
    db.add(Incident(monitor_id=m.id, cause="old", resolved_at=ago(hours=1)))
    db.add(Incident(monitor_id=m.id, cause="current"))
    db.commit()
    assert open_incident(db, m.id).cause == "current"


def test_open_incident_is_none_when_everything_is_resolved(db, make_monitor):
    m = make_monitor()
    db.add(Incident(monitor_id=m.id, cause="old", resolved_at=ago(hours=1)))
    db.commit()
    assert open_incident(db, m.id) is None


@pytest.mark.parametrize("raw, slug", [
    ("Checkout API (v2)!", "checkout-api-v2"),
    ("  Spaces  everywhere ", "spaces-everywhere"),
    ("UPPER", "upper"),
    ("!!!", "monitor"),
])
def test_slugify(raw, slug):
    assert slugify(raw) == slug


def test_unique_slug_appends_a_counter_per_owner(db, make_monitor, owner):
    make_monitor(name="Checkout API")
    assert unique_slug(db, owner.id, "Checkout API") == "checkout-api-2"
    make_monitor(name="Checkout API 2")
    assert unique_slug(db, owner.id, "checkout api") == "checkout-api-3"
    assert unique_slug(db, owner.id + 1, "Checkout API") == "checkout-api"   # other owners unaffected


def test_unique_handle_derives_from_the_email_and_avoids_collisions(db, owner):
    assert unique_handle(db, "Meera.K@example.com") == "meera-k"
    assert unique_handle(db, "owner@another.org") == "owner-2"
    db.add(User(email="o2@x.org", handle="owner-2", password_hash="x"))
    db.commit()
    assert unique_handle(db, "owner@third.org") == "owner-3"


# ------------------------------------------------------------------ mutation-driven

def test_rollup_defaults_to_exactly_24_hours(db, make_monitor):
    m = make_monitor()
    add_checks(db, m.id, (True, 100.0, ago(hours=1)), (False, None, ago(hours=24, minutes=30)))
    assert rollup(db, m.id)["checks_counted"] == 1


def test_rollup_includes_a_check_exactly_at_the_window_edge(db, make_monitor, monkeypatch):
    import app.services as services
    from datetime import datetime, timedelta, timezone
    now = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)

    class Frozen(datetime):
        @classmethod
        def now(cls, tz=None):
            return now

    monkeypatch.setattr(services, "datetime", Frozen)
    m = make_monitor()
    add_checks(db, m.id, (True, 100.0, now - timedelta(hours=24)))
    assert rollup(db, m.id)["checks_counted"] == 1


def test_rollup_rounds_latency_to_one_decimal(db, make_monitor):
    m = make_monitor()
    add_checks(db, m.id, (True, 123.456, ago(minutes=1)))
    assert rollup(db, m.id)["avg_latency_ms"] == 123.5
