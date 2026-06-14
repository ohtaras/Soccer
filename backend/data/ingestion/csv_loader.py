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
# Must match the "Country - League" names from data/ingestion/leagues_map.py,
# so historical data lines up with fixtures from live_football_data.
LEAGUES = {
    "E0": "England - Premier League",
    "E1": "England - Championship",
    "E2": "England - League One",
    "E3": "England - League Two",
    "EC": "England - National League",
    "SP1": "Spain - LaLiga",
    "SP2": "Spain - LaLiga2",
    "D1": "Germany - Bundesliga",
    "D2": "Germany - 2. Bundesliga",
    "I1": "Italy - Serie A",
    "I2": "Italy - Serie B",
    "F1": "France - Ligue 1",
    "F2": "France - Ligue 2",
    "N1": "Netherlands - Eredivisie",
    "P1": "Portugal - Liga Portugal",
    "T1": "Turkiye - Süper Lig",
    "B1": "Belgium - First Division A",
    "SC0": "Scotland - Premiership",
    "SC1": "Scotland - Championship",
    "SC2": "Scotland - League One",
    "SC3": "Scotland - League Two",
    "G1": "Greece - Super League 1",
}

# Previous (pre-country-prefix) names, for renaming rows from older deployments.
LEGACY_LEAGUE_NAMES = {
    "Premier League": "England - Premier League",
    "Championship": "England - Championship",
    "League One": "England - League One",
    "League Two": "England - League Two",
    "National League": "England - National League",
    "La Liga": "Spain - LaLiga",
    "La Liga 2": "Spain - LaLiga2",
    "Bundesliga": "Germany - Bundesliga",
    "2. Bundesliga": "Germany - 2. Bundesliga",
    "Serie A": "Italy - Serie A",
    "Serie B": "Italy - Serie B",
    "Ligue 1": "France - Ligue 1",
    "Ligue 2": "France - Ligue 2",
    "Eredivisie": "Netherlands - Eredivisie",
    "Primeira Liga": "Portugal - Liga Portugal",
    "Süper Lig": "Turkiye - Süper Lig",
    "Pro League": "Belgium - First Division A",
    "Premiership": "Scotland - Premiership",
    "Scottish Championship": "Scotland - Championship",
    "Scottish League One": "Scotland - League One",
    "Scottish League Two": "Scotland - League Two",
    "Super League Greece": "Greece - Super League 1",
}


def _rename_legacy_leagues(db) -> None:
    """Renames league labels from older deployments to the current "Country - League" format."""
    for old_name, new_name in LEGACY_LEAGUE_NAMES.items():
        db.query(Match).filter(Match.league == old_name).update({Match.league: new_name})
        db.query(Team).filter(Team.league == old_name).update({Team.league: new_name})
    db.commit()


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
        _rename_legacy_leagues(db)
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
