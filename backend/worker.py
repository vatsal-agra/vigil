"""Standalone probe worker. Runs as its own container so the API stays responsive."""
import logging
import time

from app.config import settings
from app.db import SessionLocal, engine
from app.db import Base  # noqa: F401  (ensures metadata is populated)
from app.probe import run_cycle

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s  %(name)s  %(levelname)s  %(message)s"
)
log = logging.getLogger("vigil.worker")


def wait_for_db(attempts: int = 30) -> None:
    for attempt in range(1, attempts + 1):
        try:
            with engine.connect():
                return
        except Exception:
            log.info("database not ready, retry %s/%s", attempt, attempts)
            time.sleep(2)
    raise SystemExit("Database never became reachable.")


def main() -> None:
    wait_for_db()
    log.info("worker online, cycle every %ss", settings.probe_interval_seconds)
    while True:
        db = SessionLocal()
        try:
            checked = run_cycle(db)
            if checked:
                log.info("cycle complete, %s monitor(s) checked", checked)
        except Exception:
            log.exception("cycle failed, continuing")
        finally:
            db.close()
        time.sleep(settings.probe_interval_seconds)


if __name__ == "__main__":
    import app.models  # noqa: F401

    main()
