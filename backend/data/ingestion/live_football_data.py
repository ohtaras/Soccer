"""Fetches the day's fixtures from RapidAPI's "Free API Live Football Data".

Requires a RapidAPI key (free tier) in the RAPIDAPI_KEY env var.
"""

import os
import time
from datetime import date

import requests

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


def get_fixtures_for_day(day: date | None = None) -> list[dict]:
    raise NotImplementedError("Need a sample response before this can be implemented")


if __name__ == "__main__":
    import json

    print(json.dumps(get_raw_matches_by_date(), indent=2)[:5000])
