import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import fixtures, predictions
from app.db.database import Base, SessionLocal, engine
from app.db.models import Match
from data.ingestion.csv_loader import main as load_historical_data

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


@app.on_event("startup")
def seed_historical_data():
    """On first boot (empty DB), load historical results from football-data.co.uk."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        has_data = db.query(Match).first() is not None
    finally:
        db.close()

    if has_data:
        return

    try:
        load_historical_data(["2324", "2425"])
    except Exception:
        logger.exception("Failed to load historical data on startup")


@app.get("/api/health")
def health():
    return {"status": "ok"}
