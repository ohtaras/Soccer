from datetime import date as date_cls, datetime

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Match, Prediction, Team
from ml.poisson_model import PoissonModel

router = APIRouter()


def _matches_dataframe(db: Session, league: str, before_date: date_cls | None = None) -> pd.DataFrame:
    query = (
        db.query(Match, Team.name.label("home_name"))
        .join(Team, Match.home_team_id == Team.id)
        .filter(Match.league == league)
        .filter(Match.home_goals.isnot(None))
    )
    if before_date is not None:
        query = query.filter(Match.date < before_date)
    rows = query.all()

    home_team_id = {t.id: t.name for t in db.query(Team).all()}

    records = []
    for match, _ in rows:
        records.append(
            {
                "home_team": home_team_id[match.home_team_id],
                "away_team": home_team_id[match.away_team_id],
                "home_goals": match.home_goals,
                "away_goals": match.away_goals,
            }
        )
    return pd.DataFrame.from_records(records)


def _parse_fixture_date(value: str | None) -> date_cls:
    if not value:
        return date_cls.today()
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _season_for_date(d: date_cls) -> str:
    start_year = d.year if d.month >= 7 else d.year - 1
    return f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"


def _get_or_create_team(db: Session, name: str, league: str) -> Team:
    team = db.query(Team).filter_by(name=name).first()
    if team is None:
        team = Team(name=name, league=league)
        db.add(team)
        db.flush()
    return team


def _get_or_create_match(db: Session, league: str, home_team: str, away_team: str, match_date: date_cls) -> Match:
    home = _get_or_create_team(db, home_team, league)
    away = _get_or_create_team(db, away_team, league)

    match = (
        db.query(Match)
        .filter_by(league=league, date=match_date, home_team_id=home.id, away_team_id=away.id)
        .first()
    )
    if match is None:
        match = Match(
            league=league,
            season=_season_for_date(match_date),
            date=match_date,
            home_team_id=home.id,
            away_team_id=away.id,
        )
        db.add(match)
        db.flush()
    return match


def _save_prediction(db: Session, match_id: int, result: dict) -> None:
    prediction = db.query(Prediction).filter_by(match_id=match_id).first()
    if prediction is None:
        prediction = Prediction(match_id=match_id)
        db.add(prediction)

    prediction.home_win_prob = float(result["home_win_prob"])
    prediction.draw_prob = float(result["draw_prob"])
    prediction.away_win_prob = float(result["away_win_prob"])
    prediction.predicted_home_goals = float(result["expected_home_goals"])
    prediction.predicted_away_goals = float(result["expected_away_goals"])

    db.commit()


@router.get("/predictions")
def predict_match(
    home_team: str,
    away_team: str,
    league: str,
    date: str | None = None,
    db: Session = Depends(get_db),
):
    match_date = _parse_fixture_date(date)
    df = _matches_dataframe(db, league, before_date=match_date)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No historical data for league '{league}'")

    model = PoissonModel()
    model.fit(df)
    result = model.predict(home_team, away_team)

    match = _get_or_create_match(db, league, home_team, away_team, match_date)
    _save_prediction(db, match.id, result)

    return result


@router.get("/predictions/leagues")
def predictions_leagues(db: Session = Depends(get_db)):
    """Returns the list of leagues we have historical data for (and can predict)."""
    rows = db.query(Match.league).distinct().all()
    return sorted(row[0] for row in rows)


@router.get("/predictions/history")
def predictions_history(db: Session = Depends(get_db)):
    rows = (
        db.query(Prediction, Match)
        .join(Match, Prediction.match_id == Match.id)
        .order_by(Match.date.desc())
        .all()
    )

    teams = {t.id: t.name for t in db.query(Team).all()}

    return [
        {
            "league": match.league,
            "date": match.date.isoformat(),
            "home_team": teams[match.home_team_id],
            "away_team": teams[match.away_team_id],
            "expected_home_goals": prediction.predicted_home_goals,
            "expected_away_goals": prediction.predicted_away_goals,
            "home_win_prob": prediction.home_win_prob,
            "draw_prob": prediction.draw_prob,
            "away_win_prob": prediction.away_win_prob,
        }
        for prediction, match in rows
    ]
