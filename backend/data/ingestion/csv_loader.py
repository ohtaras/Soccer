"""Loads historical match results from football-data.co.uk (free CSV, no API key)."""

import io
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.db.database import Base, SessionLocal, engine
from app.db.models import Match, Team

BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{div}.csv"

# football-data.co.uk division codes -> readable league name
# (must match the league names used in data/ingestion/fixtures.py)
LEAGUES = {
    "E0": "Premier League",
    "E1": "Championship",
    "SP1": "La Liga",
    "D1": "Bundesliga",
    "I1": "Serie A",
    "F1": "Ligue 1",
    "N1": "Eredivisie",
    "P1": "Primeira Liga",
    "T1": "Süper Lig",
    "B1": "Pro League",
    "SC0": "Premiership",
    "G1": "Super League Greece",
}


def _parse_date(value: str) -> datetime.date:
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date format: {value}")


def fetch_csv(div: str, season: str) -> pd.DataFrame:
    url = BASE_URL.format(season=season, div=div)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pd.read_csv(io.StringIO(response.text))


def get_or_create_team(db, name: str, league: str) -> Team:
    team = db.query(Team).filter_by(name=name).first()
    if team is None:
        team = Team(name=name, league=league)
        db.add(team)
        db.flush()
    return team


def load_division(db, div: str, season: str) -> int:
    league = LEAGUES[div]
    df = fetch_csv(div, season)
    df = df.dropna(subset=["HomeTeam", "AwayTeam", "Date"])

    count = 0
    for _, row in df.iterrows():
        home = get_or_create_team(db, row["HomeTeam"], league)
        away = get_or_create_team(db, row["AwayTeam"], league)

        match = Match(
            league=league,
            season=season,
            date=_parse_date(row["Date"]),
            home_team_id=home.id,
            away_team_id=away.id,
            home_goals=int(row["FTHG"]) if not pd.isna(row.get("FTHG")) else None,
            away_goals=int(row["FTAG"]) if not pd.isna(row.get("FTAG")) else None,
        )
        db.add(match)
        count += 1

    db.commit()
    return count


def main(seasons: list[str]):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for season in seasons:
            for div in LEAGUES:
                n = load_division(db, div, season)
                print(f"Loaded {n} matches for {LEAGUES[div]} ({season})")
    finally:
        db.close()


def load_missing_leagues(seasons: list[str]):
    """Backfill historical data for any league in LEAGUES not yet present in the DB.

    Safe to call on every startup against an already-seeded DB: leagues that
    already have matches are skipped, so previously-loaded data is never
    duplicated.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_leagues = {row[0] for row in db.query(Match.league).distinct().all()}
        for season in seasons:
            for div, league in LEAGUES.items():
                if league in existing_leagues:
                    continue
                n = load_division(db, div, season)
                print(f"Loaded {n} matches for {league} ({season})")
                existing_leagues.add(league)
    finally:
        db.close()


if __name__ == "__main__":
    # season codes are in YYZZ form, e.g. "2324" = 2023/24 season
    seasons = sys.argv[1:] or ["2324", "2425"]
    main(seasons)
