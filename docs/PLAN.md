# Soccer Prediction Project — Plan

## Στόχος
Ανάλυση των αγώνων ποδοσφαίρου της ημέρας και πρόβλεψη αποτελεσμάτων (1X2,
αναμενόμενα γκολ), χωρίς εξάρτηση από paid API ή mock data.

## Πηγές δεδομένων
- **Ιστορικά αποτελέσματα**: CSV από [football-data.co.uk](https://www.football-data.co.uk)
  (top-5 ευρωπαϊκές λίγκες, χωρίς API key) — `backend/data/ingestion/csv_loader.py`
- **Αγώνες ημέρας**: ESPN public scoreboard JSON endpoint (χωρίς API key) —
  `backend/data/ingestion/fixtures.py`
- **Μελλοντικά**: δυνατότητα προσθήκης API key (π.χ. API-Football) για live
  ενημερώσεις/odds.

## Αρχιτεκτονική
```
backend/
  app/            FastAPI app (routes: /fixtures/today, /predictions)
  data/ingestion/ scripts λήψης δεδομένων
  ml/             prediction models (baseline: Poisson)
frontend/         React + Vite dashboard
```

## Roadmap
1. ✅ Scaffolding backend + frontend, DB models (Team, Match, Prediction)
2. ✅ Ingestion ιστορικών δεδομένων (top-5 λίγκες) από football-data.co.uk
3. ✅ Fixtures ημέρας από ESPN scoreboard
4. ✅ Baseline Poisson model για πρόβλεψη 1X2 + αναμενόμενα γκολ
5. ✅ React dashboard: λίστα αγώνων ημέρας + κουμπί πρόβλεψης
6. Επόμενα βήματα:
   - Αυτοματοποιημένο ETL (cron/scheduled job) για ανανέωση ιστορικών δεδομένων
   - Αποθήκευση προβλέψεων στη DB (πίνακας `predictions`)
   - Βελτίωση μοντέλου (form, head-to-head, injuries)
   - Προσθήκη ελληνικής Super League σε ιστορικά δεδομένα όταν βρεθεί πηγή
