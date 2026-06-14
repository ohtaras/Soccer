import logging
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import fixtures, predictions
from app.db.database import Base, engine
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


def _seed_missing_leagues():
    try:
        load_missing_leagues(["2324", "2425"])
    except Exception:
        logger.exception("Failed to load historical data on startup")


@app.on_event("startup")
def seed_historical_data():
    """Load historical results for any league not yet present in the DB.

    Runs in a background thread so the API can start serving requests
    (and pass health checks) immediately. Safe to run on every startup:
    leagues already loaded are skipped, so data is never duplicated.
    """
    Base.metadata.create_all(bind=engine)
    threading.Thread(target=_seed_missing_leagues, daemon=True).start()


@app.get("/api/health")
def health():
    return {"status": "ok"}
