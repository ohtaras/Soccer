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

# ISO alpha-2 country code → full name (used to label leagues not in LEAGUES_BY_ID)
_COUNTRY_CODE_TO_NAME = {
    "AL": "Albania", "DZ": "Algeria", "AD": "Andorra", "AO": "Angola",
    "AR": "Argentina", "AM": "Armenia", "AU": "Australia", "AT": "Austria",
    "AZ": "Azerbaijan", "BH": "Bahrain", "BD": "Bangladesh", "BY": "Belarus",
    "BE": "Belgium", "BJ": "Benin", "BO": "Bolivia", "BA": "Bosnia-Herzegovina",
    "BW": "Botswana", "BR": "Brazil", "BF": "Burkina Faso", "BI": "Burundi",
    "KH": "Cambodia", "CM": "Cameroon", "CA": "Canada", "CL": "Chile",
    "CN": "China", "CO": "Colombia", "CD": "Congo DR", "CG": "Congo",
    "CR": "Costa Rica", "HR": "Croatia", "CY": "Cyprus", "CZ": "Czech Republic",
    "DK": "Denmark", "EC": "Ecuador", "EG": "Egypt", "SV": "El Salvador",
    "EE": "Estonia", "ET": "Ethiopia", "FI": "Finland", "FR": "France",
    "GA": "Gabon", "GE": "Georgia", "DE": "Germany", "GH": "Ghana",
    "GR": "Greece", "GT": "Guatemala", "GN": "Guinea", "HN": "Honduras",
    "HU": "Hungary", "IS": "Iceland", "IN": "India", "ID": "Indonesia",
    "IR": "Iran", "IQ": "Iraq", "IE": "Ireland", "IL": "Israel", "IT": "Italy",
    "CI": "Ivory Coast", "JP": "Japan", "JO": "Jordan", "KZ": "Kazakhstan",
    "KE": "Kenya", "XK": "Kosovo", "KW": "Kuwait", "KG": "Kyrgyzstan",
    "LV": "Latvia", "LB": "Lebanon", "LY": "Libya", "LI": "Liechtenstein",
    "LT": "Lithuania", "LU": "Luxembourg", "MK": "North Macedonia",
    "MG": "Madagascar", "MW": "Malawi", "MY": "Malaysia", "ML": "Mali",
    "MT": "Malta", "MR": "Mauritania", "MX": "Mexico", "MD": "Moldova",
    "ME": "Montenegro", "MA": "Morocco", "MZ": "Mozambique", "NA": "Namibia",
    "NL": "Netherlands", "NZ": "New Zealand", "NI": "Nicaragua", "NE": "Niger",
    "NG": "Nigeria", "NO": "Norway", "OM": "Oman", "PS": "Palestine",
    "PA": "Panama", "PY": "Paraguay", "PE": "Peru", "PH": "Philippines",
    "PL": "Poland", "PT": "Portugal", "QA": "Qatar", "RO": "Romania",
    "RU": "Russia", "RW": "Rwanda", "SA": "Saudi Arabia", "SN": "Senegal",
    "RS": "Serbia", "SL": "Sierra Leone", "SK": "Slovakia", "SI": "Slovenia",
    "ZA": "South Africa", "SS": "South Sudan", "ES": "Spain", "SD": "Sudan",
    "SE": "Sweden", "CH": "Switzerland", "SY": "Syria", "TZ": "Tanzania",
    "TH": "Thailand", "TG": "Togo", "TN": "Tunisia", "TR": "Turkey",
    "TM": "Turkmenistan", "UG": "Uganda", "UA": "Ukraine",
    "AE": "United Arab Emirates", "US": "United States", "UY": "Uruguay",
    "UZ": "Uzbekistan", "VE": "Venezuela", "VN": "Vietnam", "YE": "Yemen",
    "ZM": "Zambia", "ZW": "Zimbabwe",
    "GB-ENG": "England", "GB-SCT": "Scotland", "GB-WLS": "Wales",
    "GB-NIR": "Northern Ireland", "INT": "International",
}


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
            raw = match.get("leagueName")
            if not raw:
                continue
            code = match.get("countryCode", "")
            country = _COUNTRY_CODE_TO_NAME.get(code.upper(), "")
            league_name = f"{country} - {raw}" if country else raw

        state = _status_to_state(status)
        home = match["home"]
        away = match["away"]

        fixtures.append(
            {
                "league": league_name,
                "date": status.get("utcTime"),
                "status": state,
                "minute": status.get("liveTime", {}).get("short") if state == "in" else None,
                "home_team": home["name"],
                "away_team": away["name"],
                "home_team_id": home.get("id"),
                "away_team_id": away.get("id"),
                "home_score": home.get("score") if state != "pre" else None,
                "away_score": away.get("score") if state != "pre" else None,
            }
        )

    return fixtures


if __name__ == "__main__":
    import json

    print(json.dumps(get_raw_matches_by_date(), indent=2)[:5000])
