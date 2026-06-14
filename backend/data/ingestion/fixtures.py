"""Fetches today's fixtures/results from ESPN's public scoreboard endpoint (no API key)."""

from datetime import date

import requests

SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"

# ESPN league slugs
LEAGUES = {
    "eng.1": "Premier League",
    "eng.2": "Championship",
    "eng.3": "League One",
    "eng.4": "League Two",
    "eng.5": "National League",
    "esp.1": "La Liga",
    "esp.2": "La Liga 2",
    "ger.1": "Bundesliga",
    "ger.2": "2. Bundesliga",
    "ita.1": "Serie A",
    "ita.2": "Serie B",
    "fra.1": "Ligue 1",
    "fra.2": "Ligue 2",
    "ned.1": "Eredivisie",
    "por.1": "Primeira Liga",
    "tur.1": "Süper Lig",
    "bel.1": "Pro League",
    "sco.1": "Premiership",
    "sco.2": "Scottish Championship",
    "sco.3": "Scottish League One",
    "sco.4": "Scottish League Two",
    "gre.1": "Super League Greece",
    "uefa.champions": "UEFA Champions League",
    "uefa.europa": "UEFA Europa League",
    "uefa.europa.conf": "UEFA Europa Conference League",
    "fifa.world": "FIFA World Cup",
    "usa.1": "MLS",
    "mex.1": "Liga MX",
    "bra.1": "Brasileirão",
    "arg.1": "Liga Profesional Argentina",
    "ksa.1": "Saudi Pro League",
    "jpn.1": "J1 League",
}


def get_fixtures_for_day(day: date | None = None) -> list[dict]:
    """Returns today's (or given day's) fixtures across the configured leagues."""
    day = day or date.today()
    date_param = day.strftime("%Y%m%d")

    fixtures = []
    for slug, league_name in LEAGUES.items():
        url = SCOREBOARD_URL.format(league=slug)
        try:
            response = requests.get(url, params={"dates": date_param}, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            continue

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
