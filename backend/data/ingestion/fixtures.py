"""Fetches today's fixtures/results from ESPN's public scoreboard endpoint (no API key)."""

from datetime import date

import requests

SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"

# ESPN league slugs
LEAGUES = {
    "eng.1": "Premier League",
    "esp.1": "La Liga",
    "ger.1": "Bundesliga",
    "ita.1": "Serie A",
    "fra.1": "Ligue 1",
    "gre.1": "Super League Greece",
}


def get_fixtures_for_day(day: date | None = None) -> list[dict]:
    """Returns today's (or given day's) fixtures across the configured leagues."""
    day = day or date.today()
    date_param = day.strftime("%Y%m%d")

    fixtures = []
    for slug, league_name in LEAGUES.items():
        url = SCOREBOARD_URL.format(league=slug)
        response = requests.get(url, params={"dates": date_param}, timeout=30)
        response.raise_for_status()
        data = response.json()

        for event in data.get("events", []):
            competition = event["competitions"][0]
            competitors = competition["competitors"]
            home = next(c for c in competitors if c["homeAway"] == "home")
            away = next(c for c in competitors if c["homeAway"] == "away")

            fixtures.append(
                {
                    "league": league_name,
                    "date": event["date"],
                    "status": competition["status"]["type"]["state"],
                    "home_team": home["team"]["displayName"],
                    "away_team": away["team"]["displayName"],
                    "home_score": home.get("score"),
                    "away_score": away.get("score"),
                }
            )

    return fixtures


if __name__ == "__main__":
    for f in get_fixtures_for_day():
        print(f)
