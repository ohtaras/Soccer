# Soccer

Πρόβλεψη αποτελεσμάτων ποδοσφαίρου: ανάλυση αγώνων ημέρας με βάση ιστορικά
στατιστικά, χωρίς εξάρτηση από paid API ή mock data.

Δες [docs/PLAN.md](docs/PLAN.md) για το πλάνο/αρχιτεκτονική.

## Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Postgres (local)
docker compose up -d

# Φόρτωση ιστορικών δεδομένων (top-5 ευρωπαϊκές λίγκες)
python data/ingestion/csv_loader.py 2324 2425

# Εκκίνηση API
uvicorn app.main:app --reload
```

API διαθέσιμο στο `http://localhost:8000/api`:
- `GET /api/fixtures/today` — αγώνες ημέρας
- `GET /api/predictions?home_team=...&away_team=...&league=...` — πρόβλεψη

## Frontend

```bash
cd frontend
npm install
npm run dev
```
