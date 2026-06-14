import logging
from datetime import date

from fastapi import APIRouter

from data.ingestion import api_football
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
