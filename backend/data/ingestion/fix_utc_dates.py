"""One-time migration: fix Match.date records stored in UTC to Europe/Athens.

Matches played after 21:00 UTC (midnight Athens) were stored under the UTC
date instead of the Athens date. This script re-fetches FotMob data for each
date in the DB, computes the correct Athens date from the match utcTime, and
updates any mismatched records.

Run once on the Railway instance:
    python backend/data/ingestion/fix_utc_dates.py
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.db.database import SessionLocal
from app.db.models import Match, Prediction, Team
from data.ingestion import live_football_data

TZ = ZoneInfo("Europe/Athens")


def fix_utc_dates():
    db = SessionLocal()
    fixed = 0

    try:
        all_dates = sorted({row.date for row in db.query(Match.date).all()})
        print(f"Checking {len(all_dates)} distinct match dates...")

        for day in all_dates:
            # A late-UTC match on `day` would appear on `day+1` in Athens.
            # So we check FotMob for `day` (the UTC date we stored) to find
            # fixtures whose Athens date is actually `day+1`.
            try:
                fixtures = live_football_data.get_fixtures_for_day(day)
            except Exception as exc:
                print(f"  {day}: FotMob fetch failed ({exc}), skipping")
                continue

            for fixture in fixtures:
                raw_date = fixture.get("date")
                if not raw_date:
                    continue

                utc_dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                utc_date = utc_dt.date()
                athens_date = utc_dt.astimezone(TZ).date()

                if utc_date == athens_date:
                    continue  # No discrepancy for this fixture

                league = fixture.get("league")
                home_name = fixture.get("home_team")
                away_name = fixture.get("away_team")
                if not league or not home_name or not away_name:
                    continue

                home = db.query(Team).filter_by(name=home_name).first()
                away = db.query(Team).filter_by(name=away_name).first()
                if not home or not away:
                    continue

                wrong = db.query(Match).filter_by(
                    league=league, date=utc_date,
                    home_team_id=home.id, away_team_id=away.id,
                ).first()
                if wrong is None:
                    continue

                correct = db.query(Match).filter_by(
                    league=league, date=athens_date,
                    home_team_id=home.id, away_team_id=away.id,
                ).first()

                if correct is None:
                    print(f"  Fix: {league} {home_name} vs {away_name}: {utc_date} → {athens_date}")
                    wrong.date = athens_date
                    fixed += 1
                else:
                    # Correct record already exists — transfer prediction then remove duplicate
                    wrong_pred = db.query(Prediction).filter_by(match_id=wrong.id).first()
                    correct_pred = db.query(Prediction).filter_by(match_id=correct.id).first()
                    if wrong_pred:
                        if correct_pred is None:
                            wrong_pred.match_id = correct.id
                        else:
                            db.delete(wrong_pred)
                    db.delete(wrong)
                    fixed += 1

        db.commit()
        print(f"Done — fixed {fixed} match(es).")
    finally:
        db.close()


if __name__ == "__main__":
    fix_utc_dates()
