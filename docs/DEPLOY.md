# Deploy στο Railway

Το repo περιέχει `railway.toml` για το `backend/` και το `frontend/`, ώστε να
γίνουν deploy ως δύο ξεχωριστά services στο ίδιο project.

## 1. Δημιουργία project

1. Στο [railway.app](https://railway.app) → **New Project** → **Deploy from
   GitHub repo** → επιλέγεις `ohtaras/Soccer`.
2. Στο project, πρόσθεσε ένα **Postgres** plugin (**+ New** → **Database** →
   **PostgreSQL**). Το Railway θα δημιουργήσει αυτόματα ένα `DATABASE_URL`.

## 2. Backend service

1. **+ New** → **GitHub Repo** → `ohtaras/Soccer`.
2. **Settings → General → Root Directory**: `backend`
3. **Variables**: πρόσθεσε `DATABASE_URL` ως reference στο Postgres plugin
   (Railway: "Add Reference" → επιλέγεις το Postgres service → `DATABASE_URL`).
4. Κάνε deploy. Το `railway.toml` ορίζει το start command
   (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
5. Μόλις τρέξει, πάρε το public URL του service (**Settings → Networking →
   Generate Domain**) — π.χ. `https://soccer-backend.up.railway.app`.

### Φόρτωση ιστορικών δεδομένων (μία φορά)

Μέσω **Railway CLI** (`railway login`, `railway link`, μετά):

```bash
railway run --service backend python data/ingestion/csv_loader.py 2324 2425
```

Αυτό φορτώνει τα ιστορικά αποτελέσματα (top-5 λίγκες) στη Postgres. Δεν
χρειάζεται να τρέχει σε κάθε deploy — μόνο μία φορά (ή όποτε θέλεις refresh
των δεδομένων).

## 3. Frontend service

1. **+ New** → **GitHub Repo** → `ohtaras/Soccer` (ίδιο repo, νέο service).
2. **Settings → General → Root Directory**: `frontend`
3. **Variables**: πρόσθεσε
   ```
   VITE_API_URL=https://<το-url-του-backend>/api
   ```
   (το URL από το βήμα 2.5, με `/api` στο τέλος). Αυτό χρειάζεται να υπάρχει
   **πριν** το build, γιατί το Vite το "ψήνει" μέσα στο bundle.
4. Κάνε deploy. Το `railway.toml` κάνει `npm run build` και σερβίρει το
   `dist/` με `serve`.
5. Πάρε το public URL του frontend service (**Settings → Networking →
   Generate Domain**) — αυτό είναι το link που ανοίγεις στον browser.

## 4. Έλεγχος

- Backend health: `https://<backend-url>/api/health` → `{"status":"ok"}`
- Frontend: `https://<frontend-url>` → dashboard με αγώνες ημέρας
