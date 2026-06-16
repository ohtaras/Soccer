"""Baseline Poisson-based match outcome prediction model.

Estimates each team's attack/defense strength from historical goals scored
and conceded, then predicts the expected goals and 1X2 probabilities for a
fixture using independent Poisson distributions.
"""

from dataclasses import dataclass

import pandas as pd
from scipy.stats import poisson


@dataclass
class TeamStrength:
    attack: float
    defense: float


class PoissonModel:
    MAX_GOALS = 10

    def __init__(self):
        self.home_advantage = 1.0
        self.league_avg_home_goals = 1.0
        self.league_avg_away_goals = 1.0
        self.strengths: dict[str, TeamStrength] = {}

    def fit(self, matches: pd.DataFrame) -> None:
        """matches must have columns: home_team, away_team, home_goals, away_goals."""
        matches = matches.dropna(subset=["home_goals", "away_goals"])

        self.league_avg_home_goals = matches["home_goals"].mean()
        self.league_avg_away_goals = matches["away_goals"].mean()

        teams = pd.unique(matches[["home_team", "away_team"]].values.ravel())
        for team in teams:
            home_games = matches[matches["home_team"] == team]
            away_games = matches[matches["away_team"] == team]

            goals_scored = pd.concat([home_games["home_goals"], away_games["away_goals"]])
            goals_conceded = pd.concat([home_games["away_goals"], away_games["home_goals"]])

            league_avg_goals = (self.league_avg_home_goals + self.league_avg_away_goals) / 2
            attack = goals_scored.mean() / league_avg_goals if len(goals_scored) else 1.0
            defense = goals_conceded.mean() / league_avg_goals if len(goals_conceded) else 1.0

            self.strengths[team] = TeamStrength(attack=attack, defense=defense)

    def predict(self, home_team: str, away_team: str) -> dict:
        home = self.strengths.get(home_team, TeamStrength(1.0, 1.0))
        away = self.strengths.get(away_team, TeamStrength(1.0, 1.0))

        expected_home_goals = self.league_avg_home_goals * home.attack * away.defense
        expected_away_goals = self.league_avg_away_goals * away.attack * home.defense

        home_win = draw = away_win = 0.0
        both_score = over_25 = over_15 = 0.0

        for i in range(self.MAX_GOALS):
            for j in range(self.MAX_GOALS):
                p = poisson.pmf(i, expected_home_goals) * poisson.pmf(j, expected_away_goals)
                if i > j:
                    home_win += p
                elif i == j:
                    draw += p
                else:
                    away_win += p
                if i >= 1 and j >= 1:
                    both_score += p
                if i + j >= 3:
                    over_25 += p
                if i + j >= 2:
                    over_15 += p

        markets = {
            "1": home_win,
            "X": draw,
            "2": away_win,
            "GG": both_score,
            "NG": 1 - both_score,
            "Over 2.5": over_25,
            "Under 2.5": 1 - over_25,
            "Over 1.5": over_15,
            "Under 1.5": 1 - over_15,
        }
        best_market, best_prob = max(markets.items(), key=lambda x: x[1])

        return {
            "expected_home_goals": expected_home_goals,
            "expected_away_goals": expected_away_goals,
            "home_win_prob": home_win,
            "draw_prob": draw,
            "away_win_prob": away_win,
            "both_teams_score_prob": both_score,
            "over_25_prob": over_25,
            "over_15_prob": over_15,
            "best_bet": {"market": best_market, "probability": best_prob},
        }
