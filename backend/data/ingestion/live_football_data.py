"""Fetches the day's fixtures from RapidAPI's "Free API Live Football Data".

Requires a RapidAPI key (free tier) in the RAPIDAPI_KEY env var.
"""

import os
import time
from datetime import date

import requests

from data.ingestion.leagues_map import LEAGUES_BY_ID

API_HOST = "free-api-live-football-data.p.rapidapi.com"
MATCHES_BY_DATE_URL = f"https://{API_HOST}/football-get-matches-by-date"

# Cache responses to avoid hammering the free tier's rate limit.
_CACHE_TTL_SECONDS = 15 * 60
_cache: dict[str, tuple[float, dict]] = {}


def is_configured() -> bool:
    return bool(os.environ.get("RAPIDAPI_KEY"))


def get_raw_matches_by_date(day: date | None = None) -> dict:
    """Returns the raw API response for the given day (defaults to today)."""
    day = day or date.today()
    date_str = day.strftime("%Y%m%d")

    cached = _cache.get(date_str)
    if cached and time.time() - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    api_key = os.environ["RAPIDAPI_KEY"]
    response = requests.get(
        MATCHES_BY_DATE_URL,
        params={"date": date_str},
        headers={"x-rapidapi-key": api_key, "x-rapidapi-host": API_HOST},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    _cache[date_str] = (time.time(), data)
    return data


def _status_to_state(status: dict) -> str:
    if status.get("finished"):
        return "post"
    if status.get("started"):
        return "in"
    return "pre"


def get_fixtures_for_day(day: date | None = None) -> list[dict]:
    data = get_raw_matches_by_date(day)

    fixtures = []
    for match in data.get("response", {}).get("matches", []):
        status = match.get("status", {})
        if status.get("cancelled"):
            continue

        league_name = LEAGUES_BY_ID.get(match["leagueId"])
        if league_name is None:
            continue

        state = _status_to_state(status)
        home = match["home"]
        away = match["away"]

        fixtures.append(
            {
                "league": league_name,
                "date": status.get("utcTime"),
                "status": state,
                "home_team": home["name"],
                "away_team": away["name"],
                "home_score": home.get("score") if state != "pre" else None,
                "away_score": away.get("score") if state != "pre" else None,
            }
        )

    return fixtures


if __name__ == "__main__":
    import json

    print(json.dumps(get_raw_matches_by_date(), indent=2)[:5000])
