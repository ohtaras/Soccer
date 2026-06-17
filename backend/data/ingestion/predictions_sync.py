"""Daily sync: pre-generate and store predictions for today's fixtures.

Run every morning before matches start so win-rate history is complete
even if nobody opened the app that day.

Suggested Railway cron: 0 4 * * *  (04:00 UTC = 07:00 Athens summer)
"""

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.db.database import Base, SessionLocal, engine
from app.api.predictions import (
    _get_or_create_match,
    _matches_dataframe,
    _parse_fixture_date,
    _save_prediction,
)
from data.ingestion import live_football_data
from data.ingestion.api_football_history import ADDITIONAL_LEAGUES, ADDITIONAL_LEAGUES_BY_SEARCH
from data.ingestion.csv_loader import LEAGUES
from ml.poisson_model import PoissonModel

_TZ = ZoneInfo("Europe/Athens")

TRACKED_LEAGUES = (
    set(LEAGUES.values())
    | set(ADDITIONAL_LEAGUES.values())
    | set(ADDITIONAL_LEAGUES_BY_SEARCH.keys())
)


def sync_predictions(target_day=None) -> int:
    """Generate and store predictions for all tracked fixtures on target_day.

    Returns the number of predictions stored.
    """
    if not live_football_data.is_configured():
        print("FotMob API not configured, skipping predictions sync")
        return 0

    if target_day is None:
        target_day = datetime.now(_TZ).date()

    print(f"Generating predictions for {target_day} …")
    fixtures = live_football_data.get_fixtures_for_day(target_day)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    count = 0

    try:
        for fixture in fixtures:
            league = fixture.get("league")
            if not league or league not in TRACKED_LEAGUES:
                continue

            home_team = fixture.get("home_team")
            away_team = fixture.get("away_team")
            raw_date = fixture.get("date")
            if not home_team or not away_team or not raw_date:
                continue

            match_date = _parse_fixture_date(raw_date)

            df = _matches_dataframe(db, league, before_date=match_date)
            if df.empty:
                continue

            try:
                model = PoissonModel()
                model.fit(df)
                result = model.predict(home_team, away_team)
            except Exception as exc:
                print(f"  Model error {league} {home_team} vs {away_team}: {exc}")
                continue

            match = _get_or_create_match(db, league, home_team, away_team, match_date)
            _save_prediction(db, match.id, result)
            count += 1

        print(f"Done — {count} predictions stored for {target_day}.")
    finally:
        db.close()

    return count


if __name__ == "__main__":
    sync_predictions()
