"""Unit tests for the checking engine (app/probe.py).

The network is replaced by httpx.MockTransport, so every outcome a real target
can produce (match, mismatch, timeout, refused connection) is reproduced
deterministically. These are also the tests mutation testing runs against.
"""
from datetime import datetime

import httpx
import pytest

from app import cache
from app.config import settings
from app.models import Incident, Monitor
from app.probe import apply_result, due_monitors, probe_once, run_cycle
from app.services import open_incident
from helpers import ago, failed, passed

pytestmark = pytest.mark.unit

URL = "https://target.test/health"


def monitor(**fields) -> Monitor:
    base = dict(id=7, url=URL, method="GET", expected_status=200)
    base.update(fields)
    return Monitor(**base)


# ------------------------------------------------------------------ probe_once

def test_probe_once_records_a_matching_status_as_ok(fake_web):
    check = probe_once(fake_web({URL: 200}), monitor())
    assert check.ok is True
    assert check.status_code == 200
    assert check.error is None
    assert check.monitor_id == 7
    assert check.latency_ms is not None and check.latency_ms >= 0


def test_probe_once_reports_an_unexpected_status_in_plain_english(fake_web):
    check = probe_once(fake_web({URL: 503}), monitor())
    assert check.ok is False
    assert check.status_code == 503
    assert check.error == "Expected 200, got 503"


def test_probe_once_honours_a_custom_expected_status(fake_web):
    assert probe_once(fake_web({URL: 204}), monitor(expected_status=204)).ok is True
    assert probe_once(fake_web({URL: 200}), monitor(expected_status=204)).ok is False


def test_probe_once_uses_the_configured_http_method(fake_web):
    seen = []
    probe_once(fake_web({URL: 200}, seen), monitor(method="HEAD"))
    assert [r.method for r in seen] == ["HEAD"]


def test_probe_once_turns_a_timeout_into_a_readable_failure(fake_web):
    check = probe_once(fake_web({URL: httpx.ReadTimeout}), monitor())
    assert check.ok is False
    assert check.status_code is None
    assert check.error == f"No response within {settings.probe_timeout_seconds:.0f}s"
    assert check.latency_ms is not None          # a timeout still has a duration


def test_probe_once_names_the_connection_error_without_a_traceback(fake_web):
    check = probe_once(fake_web({URL: httpx.ConnectError}), monitor())
    assert check.ok is False
    assert check.latency_ms is None
    assert check.error == "Connection failed: ConnectError"


# ------------------------------------------------------------------ due_monitors

def test_a_never_checked_monitor_is_due(db, make_monitor):
    m = make_monitor()
    assert [x.id for x in due_monitors(db)] == [m.id]


def test_a_monitor_inside_its_interval_is_not_due(db, make_monitor):
    make_monitor(interval_seconds=60, last_checked_at=ago(seconds=10))
    assert due_monitors(db) == []


def test_a_monitor_past_its_interval_is_due(db, make_monitor):
    m = make_monitor(interval_seconds=60, last_checked_at=ago(seconds=61))
    assert [x.id for x in due_monitors(db)] == [m.id]


def test_a_paused_monitor_is_never_due(db, make_monitor):
    make_monitor(is_active=False)
    assert due_monitors(db) == []


# ------------------------------------------------------------------ apply_result

def test_one_failure_is_noise_not_an_incident(db, make_monitor):
    m = make_monitor()
    apply_result(db, m, failed(m.id))
    assert m.consecutive_failures == 1
    assert m.current_status == "pending"
    assert open_incident(db, m.id) is None


def test_the_second_consecutive_failure_opens_an_incident(db, make_monitor):
    m = make_monitor()
    apply_result(db, m, failed(m.id))
    apply_result(db, m, failed(m.id, error="No response within 8s"))
    assert m.current_status == "down"
    incident = open_incident(db, m.id)
    assert incident is not None
    assert incident.cause == "No response within 8s"


def test_continued_failures_do_not_open_duplicate_incidents(db, make_monitor):
    m = make_monitor()
    for _ in range(4):
        apply_result(db, m, failed(m.id))
    assert db.query(Incident).filter_by(monitor_id=m.id).count() == 1


def test_the_failure_threshold_comes_from_settings(db, make_monitor, monkeypatch):
    monkeypatch.setattr(settings, "failure_threshold", 3)
    m = make_monitor()
    apply_result(db, m, failed(m.id))
    apply_result(db, m, failed(m.id))
    assert m.current_status != "down"
    apply_result(db, m, failed(m.id))
    assert m.current_status == "down"


def test_recovery_resolves_the_incident_and_writes_a_summary(db, make_monitor):
    m = make_monitor(name="Checkout API")
    apply_result(db, m, failed(m.id))
    apply_result(db, m, failed(m.id))
    incident = open_incident(db, m.id)

    apply_result(db, m, passed(m.id, latency_ms=212.4))

    db.refresh(incident)
    assert incident.resolved_at is not None
    assert m.current_status == "up"
    assert m.consecutive_failures == 0
    assert incident.summary.startswith("Checkout API recovered after ")
    assert "Trigger: Expected 200, got 503." in incident.summary
    assert incident.summary.endswith("Now answering in 212 ms.")


def test_a_success_resets_the_failure_counter(db, make_monitor):
    m = make_monitor()
    apply_result(db, m, failed(m.id))
    apply_result(db, m, passed(m.id))
    apply_result(db, m, failed(m.id))
    assert m.consecutive_failures == 1
    assert open_incident(db, m.id) is None


@pytest.mark.parametrize("latency, status", [(150.0, "up"), (2000.0, "up"), (2000.1, "degraded")])
def test_slow_but_successful_checks_are_degraded_above_two_seconds(db, make_monitor, latency, status):
    m = make_monitor()
    apply_result(db, m, passed(m.id, latency_ms=latency))
    assert m.current_status == status


def test_every_result_is_stored_and_timestamped(db, make_monitor):
    m = make_monitor()
    before = datetime.now(m.created_at.tzinfo)
    apply_result(db, m, passed(m.id))
    assert m.last_checked_at >= before
    assert len(m.checks) == 1


def test_a_result_invalidates_exactly_the_affected_cache_keys(db, make_monitor):
    m = make_monitor()
    for key in (f"monitors:list:{m.owner_id}", f"monitors:checks:{m.id}:24",
                "status:public:owner", "monitors:list:999"):
        cache.set_json(key, {"stale": True})

    apply_result(db, m, passed(m.id))

    assert cache.get_json(f"monitors:list:{m.owner_id}") is None
    assert cache.get_json(f"monitors:checks:{m.id}:24") is None
    assert cache.get_json("status:public:owner") is None
    assert cache.get_json("monitors:list:999") == {"stale": True}   # another user's cache survives


# ------------------------------------------------------------------ run_cycle

def test_run_cycle_probes_only_due_monitors_and_reports_the_count(db, make_monitor, fake_web):
    due = make_monitor(name="Due", url="https://due.test/")
    make_monitor(name="Fresh", url="https://fresh.test/", last_checked_at=ago(seconds=5))
    seen = []
    assert run_cycle(db, fake_web({"https://due.test/": 200}, seen)) == 1
    assert [str(r.url) for r in seen] == ["https://due.test/"]
    assert due.current_status == "up"


def test_run_cycle_with_nothing_due_does_no_work(db, fake_web):
    assert run_cycle(db, fake_web({})) == 0


# ------------------------------------------------------------------ mutation-driven
# Added after the first mutmut run: each test below kills mutants that survived it
# (exact latency arithmetic, rounding, boundaries, client ownership, log output).

class FakeClock:
    def __init__(self, *readings):
        self._readings = iter(readings)

    def perf_counter(self):
        return next(self._readings)


def frozen_at(moment):
    class Frozen(datetime):
        @classmethod
        def now(cls, tz=None):
            return moment
    return Frozen


def test_latency_is_measured_in_milliseconds_to_one_decimal(fake_web, monkeypatch):
    import app.probe as probe
    web = fake_web({URL: 200})
    monkeypatch.setattr(probe, "time", FakeClock(10.0, 10.123456))
    assert probe_once(web, monitor()).latency_ms == 123.5


def test_a_timeout_records_its_duration_in_milliseconds(fake_web, monkeypatch):
    import app.probe as probe
    web = fake_web({URL: httpx.ReadTimeout})
    monkeypatch.setattr(probe, "time", FakeClock(10.0, 18.123456))
    assert probe_once(web, monitor()).latency_ms == 8123.5


def test_a_monitor_is_due_at_exactly_its_interval(db, make_monitor, monkeypatch):
    import app.probe as probe
    from datetime import timezone, timedelta
    now = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(probe, "datetime", frozen_at(now))
    m = make_monitor(interval_seconds=60, last_checked_at=now - timedelta(seconds=60))
    assert [x.id for x in due_monitors(db)] == [m.id]


def test_every_never_checked_monitor_is_due_not_just_the_first(db, make_monitor):
    a = make_monitor(name="A", url="https://a.test/")
    b = make_monitor(name="B", url="https://b.test/")
    assert sorted(x.id for x in due_monitors(db)) == [a.id, b.id]


def test_the_recovery_summary_reports_the_outage_length_in_minutes(db, make_monitor):
    m = make_monitor(name="Checkout API")
    apply_result(db, m, failed(m.id))
    apply_result(db, m, failed(m.id))
    incident = open_incident(db, m.id)
    incident.started_at = ago(minutes=30)
    db.commit()
    apply_result(db, m, passed(m.id))
    db.refresh(incident)
    assert incident.summary.startswith("Checkout API recovered after 30 min.")


def test_a_failure_without_an_error_message_still_names_a_cause(db, make_monitor):
    m = make_monitor()
    from app.models import Check
    for _ in range(2):
        apply_result(db, m, Check(monitor_id=m.id, ok=False, status_code=None, latency_ms=None, error=None))
    assert open_incident(db, m.id).cause == "check failed"


def test_run_cycle_closes_the_client_it_creates_and_follows_redirects(db, make_monitor, monkeypatch):
    import app.probe as probe
    real_client = httpx.Client
    made = []

    def factory(**kwargs):
        c = real_client(transport=httpx.MockTransport(lambda r: httpx.Response(200)), **kwargs)
        made.append((c, kwargs))
        return c

    make_monitor()
    monkeypatch.setattr(probe.httpx, "Client", factory)
    probe.run_cycle(db)
    [(client, kwargs)] = made
    assert kwargs == {"follow_redirects": True}
    assert client.is_closed


def test_run_cycle_logs_each_check(db, make_monitor, fake_web, caplog):
    import logging
    make_monitor(name="Up", url="https://up.test/")
    make_monitor(name="Down", url="https://down.test/")
    caplog.set_level(logging.INFO, logger="vigil.probe")
    run_cycle(db, fake_web({"https://up.test/": 200, "https://down.test/": 500}))
    lines = sorted(r.getMessage().split(" (")[0] for r in caplog.records if r.name == "vigil.probe")
    assert lines == ["checked Down -> fail", "checked Up -> ok"]
