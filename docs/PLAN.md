# Soccer Prediction Project — Plan

## Στόχος
Ανάλυση των αγώνων ποδοσφαίρου της ημέρας και πρόβλεψη αποτελεσμάτων (1X2,
αναμενόμενα γκολ), χωρίς εξάρτηση από paid API ή mock data.

## Πηγές δεδομένων
- **Ιστορικά αποτελέσματα**: CSV από [football-data.co.uk](https://www.football-data.co.uk)
  (top-5 ευρωπαϊκές λίγκες + Championship, Eredivisie, Primeira Liga, Süper Lig,
  Pro League, Scottish Premiership, Ελληνική Super League, χωρίς API key) —
  `backend/data/ingestion/csv_loader.py`
- **Αγώνες ημέρας**: ESPN public scoreboard JSON endpoint (χωρίς API key),
  κάλυψη top-5 λίγκες + Championship, Eredivisie, Primeira Liga, Süper Lig,
  Pro League, Scottish Premiership, Ελληνική Super League, UEFA Champions
  League/Europa League/Conference League, FIFA World Cup —
  `backend/data/ingestion/fixtures.py`
- **Μελλοντικά**: δυνατότητα προσθήκης API key (π.χ. API-Football) για live
  ενημερώσεις/odds.

## Αρχιτεκτονική
```
backend/
  app/            FastAPI app (routes: /fixtures/today, /predictions, /predictions/history)
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
6. ✅ Αποθήκευση προβλέψεων στη DB (πίνακας `predictions`, endpoint `/predictions/history`)
7. ✅ Εμπλουτισμός κάλυψης λιγκών (περισσότερες ευρωπαϊκές λίγκες, UEFA
   κύπελλα, FIFA World Cup) για να υπάρχουν περισσότεροι αγώνες κάθε μέρα.
   Backfill ιστορικών δεδομένων για νέες λίγκες τρέχει αυτόματα στο startup
   (`load_missing_leagues`), χωρίς να ξαναφορτώνει ήδη υπάρχουσες λίγκες.
8. Επόμενα βήματα:
   - Αυτοματοποιημένο ETL (cron/scheduled job) για ανανέωση ιστορικών δεδομένων
   - Βελτίωση μοντέλου (form, head-to-head, injuries)
   - Ιστορικά δεδομένα για UEFA κύπελλα / World Cup ώστε να υπάρχουν
     προβλέψεις και για διεθνείς διοργανώσεις
