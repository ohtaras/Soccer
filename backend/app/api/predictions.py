import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Match, Team
from ml.poisson_model import PoissonModel

router = APIRouter()


def _matches_dataframe(db: Session, league: str) -> pd.DataFrame:
    rows = (
        db.query(Match, Team.name.label("home_name"))
        .join(Team, Match.home_team_id == Team.id)
        .filter(Match.league == league)
        .all()
    )

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


@router.get("/predictions")
def predict_match(home_team: str, away_team: str, league: str, db: Session = Depends(get_db)):
    df = _matches_dataframe(db, league)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No historical data for league '{league}'")

    model = PoissonModel()
    model.fit(df)
    return model.predict(home_team, away_team)
