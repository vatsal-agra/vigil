"""Test harness: real PostgreSQL and Redis, isolated from development data.

Tests run against `<DATABASE_URL database>_test` and Redis database 15, so
`docker compose exec api pytest` never touches the demo account. The test
database is created on first use. Environment variables are rewritten
*before* any `app` module is imported, because `app.config.settings` and the
SQLAlchemy engine are built at import time.
"""
import os
from urllib.parse import urlsplit, urlunsplit

DEV_DB_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://vigil:vigil@localhost:5432/vigil")
_db = urlsplit(DEV_DB_URL)
_name = _db.path.lstrip("/")
TEST_DB_URL = urlunsplit(_db._replace(path="/" + (_name if _name.endswith("_test") else _name + "_test")))
TEST_REDIS_URL = urlunsplit(
    urlsplit(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))._replace(path="/15")
)

os.environ.update(
    DATABASE_URL=TEST_DB_URL,
    REDIS_URL=TEST_REDIS_URL,
    SEED_DEMO_DATA="false",
    JWT_SECRET="test-secret",
)


def _ensure_test_database() -> None:
    from sqlalchemy import create_engine, text

    admin = create_engine(DEV_DB_URL, isolation_level="AUTOCOMMIT")
    name = urlsplit(TEST_DB_URL).path.lstrip("/")
    with admin.connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": name})
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()


_ensure_test_database()

# ---------------------------------------------------------------- app imports

from datetime import datetime, timedelta, timezone  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app import cache  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import Check, Incident, Monitor, User  # noqa: E402
from app.security import hash_password  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def clean_state():
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE checks, incidents, monitors, users RESTART IDENTITY CASCADE"))
    cache.client().flushdb()
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def signup(client):
    """Register a user through the real API; returns (auth headers, account json)."""

    def _signup(email="rhea@example.com", password="correct-horse-1"):
        r = client.post("/api/auth/register", json={"email": email, "password": password})
        assert r.status_code == 201, r.text
        body = r.json()
        return {"Authorization": f"Bearer {body['access_token']}"}, body

    return _signup


@pytest.fixture
def owner(db):
    user = User(email="owner@example.com", handle="owner", password_hash=hash_password("x" * 10))
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def make_monitor(db, owner):
    def _make(name="Checkout API", url="https://target.test/health", **fields):
        monitor = Monitor(owner_id=owner.id, name=name, slug=name.lower().replace(" ", "-"),
                          url=url, **fields)
        db.add(monitor)
        db.commit()
        return monitor

    return _make


@pytest.fixture
def fake_web():
    """An httpx client whose responses the test scripts per URL.

    fake_web({"https://a.test/": 200, "https://b.test/": httpx.ReadTimeout})
    """

    def _client(routes: dict, seen: list | None = None) -> httpx.Client:
        def handler(request: httpx.Request) -> httpx.Response:
            if seen is not None:
                seen.append(request)
            outcome = routes[str(request.url)]
            if isinstance(outcome, type) and issubclass(outcome, Exception):
                raise outcome("simulated", request=request)
            return httpx.Response(outcome)

        return httpx.Client(transport=httpx.MockTransport(handler))

    return _client

