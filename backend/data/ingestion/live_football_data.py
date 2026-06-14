"""Fetches the day's fixtures from RapidAPI's "Free API Live Football Data".

Requires a RapidAPI key (free tier) in the RAPIDAPI_KEY env var.
"""

import os
import time
from datetime import date

import requests

API_HOST = "free-api-live-football-data.p.rapidapi.com"
MATCHES_BY_DATE_URL = f"https://{API_HOST}/football-get-matches-by-date"
LEAGUES_WITH_COUNTRY_URL = f"https://{API_HOST}/football-get-all-leagues-list-with-country"

# Cache responses to avoid hammering the free tier's rate limit.
_CACHE_TTL_SECONDS = 15 * 60
_cache: dict[str, tuple[float, dict]] = {}

# League names rarely change, so cache the leagues map for much longer.
_LEAGUES_CACHE_TTL_SECONDS = 24 * 60 * 60
_leagues_cache: tuple[float, dict[int, str]] | None = None


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


def get_raw_leagues_with_country() -> dict:
    """Returns the raw "leagues list with country" API response (uncached)."""
    api_key = os.environ["RAPIDAPI_KEY"]
    response = requests.get(
        LEAGUES_WITH_COUNTRY_URL,
        headers={"x-rapidapi-key": api_key, "x-rapidapi-host": API_HOST},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_leagues_by_id() -> dict[int, str]:
    """Returns a {league_id: "Country - League Name"} map, e.g. {203: "Norway - OBOS-ligaen"}.

    Returns an empty dict (rather than raising) if the lookup fails, so callers can
    fall back to a generic label without breaking the whole fixtures response.
    """
    global _leagues_cache

    if _leagues_cache and time.time() - _leagues_cache[0] < _LEAGUES_CACHE_TTL_SECONDS:
        return _leagues_cache[1]

    data = get_raw_leagues_with_country()

    leagues_by_id: dict[int, str] = {}
    for country in data.get("response", {}).get("leagues", []):
        country_name = country.get("name")
        for league in country.get("leagues", []):
            league_id = league.get("id")
            league_name = league.get("name")
            if league_id is None or not league_name:
                continue
            if country_name:
                leagues_by_id[league_id] = f"{country_name} - {league_name}"
            else:
                leagues_by_id[league_id] = league_name

    _leagues_cache = (time.time(), leagues_by_id)
    return leagues_by_id


def _status_to_state(status: dict) -> str:
    if status.get("finished"):
        return "post"
    if status.get("started"):
        return "in"
    return "pre"


def get_fixtures_for_day(day: date | None = None) -> list[dict]:
    data = get_raw_matches_by_date(day)

    try:
        leagues_by_id = get_leagues_by_id()
    except Exception:
        leagues_by_id = {}

    fixtures = []
    for match in data.get("response", {}).get("matches", []):
        status = match.get("status", {})
        if status.get("cancelled"):
            continue

        state = _status_to_state(status)
        home = match["home"]
        away = match["away"]

        fixtures.append(
            {
                "league": leagues_by_id.get(match["leagueId"], f"League {match['leagueId']}"),
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
