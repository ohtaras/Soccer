from datetime import date

from fastapi import APIRouter

from data.ingestion.fixtures import get_fixtures_for_day

router = APIRouter()


@router.get("/fixtures/today")
def fixtures_today():
    return {"date": date.today().isoformat(), "fixtures": get_fixtures_for_day()}
