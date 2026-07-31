import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import cache, models  # noqa: F401
from app.config import settings
from app.db import Base, SessionLocal, engine
from app.routers import auth, incidents, monitors, status
from app.seed import seed

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("vigil.api")


def wait_for_db(attempts: int = 30) -> None:
    for attempt in range(1, attempts + 1):
        try:
            with engine.connect():
                return
        except Exception:
            log.info("database not ready, retry %s/%s", attempt, attempts)
            time.sleep(2)
    raise SystemExit("Database never became reachable.")


@asynccontextmanager
async def lifespan(_: FastAPI):
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    if settings.seed_demo_data:
        db = SessionLocal()
        try:
            seed(db)
        finally:
            db.close()
    log.info("Vigil API ready")
    yield


app = FastAPI(
    title="Vigil API",
    version="0.1.0",
    description="Uptime and API monitoring with automatic incident detection.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(monitors.router)
app.include_router(incidents.router)
app.include_router(status.router)


@app.get("/health", tags=["ops"])
def health():
    checks = {"api": "ok", "database": "unreachable", "cache": "unreachable"}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        pass
    try:
        cache.client().ping()
        checks["cache"] = "ok"
    except Exception:
        pass
    return {"status": "ok" if "unreachable" not in checks.values() else "degraded", **checks}
