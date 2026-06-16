"""Keeps historical match results up to date for leagues we track for predictions.

Fetches yesterday's finished fixtures from the Free API Live Football Data source
and stores final scores for any league we have historical data for, so the Poisson
model's training data keeps growing as each season progresses.
"""

import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("Europe/Athens")
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.db.database import Base, SessionLocal, engine
from app.db.models import Match
from data.ingestion import live_football_data
from data.ingestion.api_football_history import ADDITIONAL_LEAGUES, ADDITIONAL_LEAGUES_BY_SEARCH
from data.ingestion.csv_loader import LEAGUES, get_or_create_team

TRACKED_LEAGUES = set(LEAGUES.values()) | set(ADDITIONAL_LEAGUES.values()) | set(ADDITIONAL_LEAGUES_BY_SEARCH.keys())


def _season_for_date(d: date) -> str:
    start_year = d.year if d.month >= 7 else d.year - 1
    return f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"


def sync_finished_matches(target_day: date | None = None) -> int:
    """Stores final scores for finished fixtures in tracked leagues.

    Returns the number of matches stored or updated.
    """
    if not live_football_data.is_configured():
        return 0

    target_day = target_day or (datetime.now(_TZ).date() - timedelta(days=1))
    fixtures = live_football_data.get_fixtures_for_day(target_day)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    count = 0
    try:
        for fixture in fixtures:
            if fixture["status"] != "post":
                continue
            league = fixture["league"]
            if league not in TRACKED_LEAGUES:
                continue
            if fixture["home_score"] is None or fixture["away_score"] is None:
                continue

            home = get_or_create_team(db, fixture["home_team"], league)
            away = get_or_create_team(db, fixture["away_team"], league)
            match_date = datetime.fromisoformat(fixture["date"].replace("Z", "+00:00")).astimezone(_TZ).date()

            match = (
                db.query(Match)
                .filter_by(league=league, date=match_date, home_team_id=home.id, away_team_id=away.id)
                .first()
            )
            if match is None:
                match = Match(
                    league=league,
                    season=_season_for_date(match_date),
                    date=match_date,
                    home_team_id=home.id,
                    away_team_id=away.id,
                )
                db.add(match)

            match.home_goals = fixture["home_score"]
            match.away_goals = fixture["away_score"]
            count += 1

        db.commit()
    finally:
        db.close()

    return count


if __name__ == "__main__":
    print(f"Stored {sync_finished_matches()} results")
