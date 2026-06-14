"""Backfills historical results for additional leagues via API-Football (RapidAPI).

football-data.co.uk (used by csv_loader) only covers ~11 European leagues. This
fills in a handful of other major leagues using API-Football's free tier
(100 requests/day) -- one request per league/season, so well within the limit.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.db.database import Base, SessionLocal, engine
from app.db.models import Match
from data.ingestion.csv_loader import get_or_create_team

API_HOST = "api-football-v1.p.rapidapi.com"
FIXTURES_URL = f"https://{API_HOST}/v3/fixtures"

# API-Football league ID -> "Country - League" name (must match leagues_map.py)
ADDITIONAL_LEAGUES = {
    71: "Brazil - Serie A",
    128: "Argentina - Liga Profesional",
    262: "Mexico - Liga MX",
    253: "United States - MLS",
}


def is_configured() -> bool:
    return bool(os.environ.get("RAPIDAPI_KEY"))


def fetch_finished_fixtures(league_id: int, season: str) -> list[dict]:
    api_key = os.environ["RAPIDAPI_KEY"]
    response = requests.get(
        FIXTURES_URL,
        params={"league": league_id, "season": season, "status": "FT"},
        headers={"x-rapidapi-key": api_key, "x-rapidapi-host": API_HOST},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("response", [])


def load_league_season(db, league_id: int, league_name: str, season: str) -> int:
    count = 0
    for item in fetch_finished_fixtures(league_id, season):
        teams = item["teams"]
        goals = item["goals"]
        if goals.get("home") is None or goals.get("away") is None:
            continue

        home = get_or_create_team(db, teams["home"]["name"], league_name)
        away = get_or_create_team(db, teams["away"]["name"], league_name)
        match_date = datetime.fromisoformat(item["fixture"]["date"]).date()

        match = Match(
            league=league_name,
            season=season,
            date=match_date,
            home_team_id=home.id,
            away_team_id=away.id,
            home_goals=goals["home"],
            away_goals=goals["away"],
        )
        db.add(match)
        count += 1

    db.commit()
    return count


def load_missing_leagues(seasons: list[str]) -> None:
    """Backfill historical data for any additional league not yet present in the DB.

    Safe to call on every startup: leagues that already have matches are skipped.
    """
    if not is_configured():
        return

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_leagues = {row[0] for row in db.query(Match.league).distinct().all()}
        for league_id, league_name in ADDITIONAL_LEAGUES.items():
            if league_name in existing_leagues:
                continue
            total = 0
            for season in seasons:
                total += load_league_season(db, league_id, league_name, season)
            print(f"Loaded {total} matches for {league_name}")
            existing_leagues.add(league_name)
    finally:
        db.close()


if __name__ == "__main__":
    load_missing_leagues(["2024", "2025"])
