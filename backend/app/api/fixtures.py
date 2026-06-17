import logging
from datetime import date

import requests
from fastapi import APIRouter, Query

from data.ingestion import api_football, live_football_data
from data.ingestion.fixtures import get_fixtures_for_day

logger = logging.getLogger(__name__)

router = APIRouter()


def _log_fetch_failure(source: str, exc: Exception) -> None:
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        logger.error(
            "%s fetch failed: HTTP %s — %s",
            source, exc.response.status_code, exc.response.text[:300],
        )
    else:
        logger.exception("%s fetch failed", source)


@router.get("/fixtures/today")
def fixtures_today(date_str: str | None = Query(None, alias="date")):
    day = date.fromisoformat(date_str) if date_str else date.today()

    fixtures = None

    if live_football_data.is_configured():
        try:
            fixtures = live_football_data.get_fixtures_for_day(day)
        except Exception as exc:
            _log_fetch_failure("Free API Live Football Data", exc)
            fixtures = None

    if fixtures is None and api_football.is_configured():
        try:
            fixtures = api_football.get_fixtures_for_day(day)
        except Exception as exc:
            _log_fetch_failure("API-Football", exc)
            fixtures = None

    if fixtures is None:
        fixtures = get_fixtures_for_day(day)

    return {"date": day.isoformat(), "fixtures": fixtures}


@router.get("/debug/live-football-data-raw")
def debug_live_football_data_raw():
    """Temporary debug endpoint to inspect the raw API response shape."""
    if not live_football_data.is_configured():
        return {"error": "RAPIDAPI_KEY not set"}
    return live_football_data.get_raw_matches_by_date()
