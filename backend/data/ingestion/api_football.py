"""Fetches the full day's fixtures from API-Football (RapidAPI), covering ~1100 leagues.

Requires a RapidAPI key (free tier: 100 requests/day) in the RAPIDAPI_KEY env var.
Falls back to nothing (caller should fall back to fixtures.py / ESPN) if unset.
"""

import os
import time
from datetime import date

import requests

API_HOST = "api-football-v1.p.rapidapi.com"
FIXTURES_URL = f"https://{API_HOST}/v3/fixtures"

# Cache responses to stay well within the 100 requests/day free-tier limit.
_CACHE_TTL_SECONDS = 15 * 60
_cache: dict[str, tuple[float, list[dict]]] = {}

_STATUS_MAP = {
    "NS": "pre",
    "TBD": "pre",
    "FT": "post",
    "AET": "post",
    "PEN": "post",
    "PST": "post",
    "CANC": "post",
    "ABD": "post",
    "AWD": "post",
    "WO": "post",
}


def is_configured() -> bool:
    return bool(os.environ.get("RAPIDAPI_KEY"))


def _status_to_state(short: str) -> str:
    return _STATUS_MAP.get(short, "in")


def get_fixtures_for_day(day: date | None = None) -> list[dict]:
    """Returns all of the day's fixtures across every league API-Football covers."""
    day = day or date.today()
    date_str = day.isoformat()

    cached = _cache.get(date_str)
    if cached and time.time() - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    api_key = os.environ["RAPIDAPI_KEY"]
    response = requests.get(
        FIXTURES_URL,
        params={"date": date_str},
        headers={"x-rapidapi-key": api_key, "x-rapidapi-host": API_HOST},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    fixtures = []
    for item in data.get("response", []):
        fixture = item["fixture"]
        league = item["league"]
        teams = item["teams"]
        goals = item["goals"]

        fixtures.append(
            {
                "league": f"{league['country']} - {league['name']}" if league.get("country") else league["name"],
                "date": fixture["date"],
                "status": _status_to_state(fixture["status"]["short"]),
                "home_team": teams["home"]["name"],
                "away_team": teams["away"]["name"],
                "home_score": goals.get("home"),
                "away_score": goals.get("away"),
            }
        )

    _cache[date_str] = (time.time(), fixtures)
    return fixtures


if __name__ == "__main__":
    for f in get_fixtures_for_day():
        print(f)
