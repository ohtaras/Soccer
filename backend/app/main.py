import logging
import threading
import time
from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import fixtures, predictions
from app.db.database import Base, SessionLocal, engine
from app.db.models import SyncState
from data.ingestion import api_football_history, predictions_sync, results_sync
from data.ingestion.csv_loader import load_missing_leagues

logger = logging.getLogger(__name__)

app = FastAPI(title="Soccer Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fixtures.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")

DAY_SECONDS = 24 * 60 * 60


def _seed_missing_leagues():
    try:
        load_missing_leagues(["2324", "2425"])
    except Exception:
        logger.exception("Failed to load historical data on startup")

    try:
        api_football_history.load_missing_leagues(["2024", "2025"])
    except Exception:
        logger.exception("Failed to load additional leagues' historical data on startup")


def _already_ran_today(key: str) -> bool:
    """Checks (and if not, claims) today's run for `key` in the DB.

    Prevents redeploys from re-hitting the rate-limited live-data API more
    than once per day — the in-process daemon threads otherwise fire again
    on every restart regardless of how recently they last ran.
    """
    today = date.today()
    db = SessionLocal()
    try:
        state = db.get(SyncState, key)
        if state is not None and state.last_run_date == today:
            return True
        if state is None:
            db.add(SyncState(key=key, last_run_date=today))
        else:
            state.last_run_date = today
        db.commit()
        return False
    finally:
        db.close()


def _sync_results_loop():
    while True:
        if _already_ran_today("sync_results"):
            time.sleep(DAY_SECONDS)
            continue
        try:
            count = results_sync.sync_finished_matches()
            logger.info("Synced %d finished match results", count)
        except Exception:
            logger.exception("Failed to sync finished match results")
        time.sleep(DAY_SECONDS)


def _sync_predictions_loop():
    while True:
        if _already_ran_today("sync_predictions"):
            time.sleep(DAY_SECONDS)
            continue
        try:
            count = predictions_sync.sync_predictions()
            logger.info("Stored %d predictions for today's fixtures", count)
        except Exception:
            logger.exception("Failed to sync today's predictions")
        time.sleep(DAY_SECONDS)


@app.on_event("startup")
def seed_historical_data():
    """Load historical results for any league not yet present in the DB.

    Runs in a background thread so the API can start serving requests
    (and pass health checks) immediately. Safe to run on every startup:
    leagues already loaded are skipped, so data is never duplicated.
    """
    Base.metadata.create_all(bind=engine)
    threading.Thread(target=_seed_missing_leagues, daemon=True).start()
    threading.Thread(target=_sync_results_loop, daemon=True).start()
    threading.Thread(target=_sync_predictions_loop, daemon=True).start()


@app.get("/api/health")
def health():
    return {"status": "ok"}
