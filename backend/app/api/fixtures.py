import logging
from datetime import date

from fastapi import APIRouter

from data.ingestion import api_football, live_football_data
from data.ingestion.fixtures import get_fixtures_for_day

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/fixtures/today")
def fixtures_today():
    fixtures = None
    if api_football.is_configured():
        try:
            fixtures = api_football.get_fixtures_for_day()
        except Exception:
            logger.exception("API-Football fetch failed, falling back to ESPN")
            fixtures = None

    if fixtures is None:
        fixtures = get_fixtures_for_day()

    return {"date": date.today().isoformat(), "fixtures": fixtures}


@router.get("/debug/live-football-data-raw")
def debug_live_football_data_raw():
    """Temporary debug endpoint to inspect the raw API response shape."""
    if not live_football_data.is_configured():
        return {"error": "RAPIDAPI_KEY not set"}
    return live_football_data.get_raw_matches_by_date()
