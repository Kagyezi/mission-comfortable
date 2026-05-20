# Phase 1 Setup Guide

Follow these steps in order. Each section ends with a verification step — don't move on until it passes.

---

## Prerequisites

Install these before starting:

| Tool | Version | Download |
|---|---|---|
| Python | 3.11 or 3.12 | https://python.org/downloads |
| PostgreSQL | 16+ | https://www.postgresql.org/download/windows |
| Node.js | 20+ | https://nodejs.org |
| Git | Any | https://git-scm.com |

During PostgreSQL install, note the password you set for the `postgres` user — you'll need it below.

---

## Step 1 — Clone / open the project

If you're starting fresh:
```
git init trading-system
cd trading-system
```

Or just open the extracted folder in your terminal.

---

## Step 2 — Set up the Python virtual environment

```bash
# Windows
cd trading-system
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

Install dependencies:
```bash
pip install -r backend/requirements.txt
```

---

## Step 3 — Create the database

Open pgAdmin (installed with PostgreSQL) or use the command line:

```bash
# Connect to PostgreSQL
psql -U postgres

# Inside psql, create the database:
CREATE DATABASE trading_system;

# Verify it was created:
\l

# Exit psql:
\q
```

---

## Step 4 — Configure environment variables

```bash
# Copy the example file
copy backend\config\.env.example backend\config\.env    # Windows
cp backend/config/.env.example backend/config/.env      # Mac/Linux
```

Open `backend/config/.env` in any text editor and fill in:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/trading_system
```

Replace `YOUR_PASSWORD` with the PostgreSQL password you set during installation.

Leave the MT5 fields empty for now — those are filled in Phase 2.

---

## Step 5 — Run database migrations

This creates all 9 tables in your database:

```bash
# Run from the project root (where alembic.ini lives)
# Make sure your venv is activated first

alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

**Verify:** Open pgAdmin, connect to `trading_system` database, and confirm
you can see tables: `bots`, `signals`, `trades`, `risk_events`, etc.

---

## Step 6 — Start the FastAPI backend

```bash
# From the project root, with venv activated:
uvicorn backend.api.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Verify:** Open http://localhost:8000/health in your browser.
You should see:
```json
{
  "status": "ok",
  "database": "connected",
  "version": "0.1.0"
}
```

Also visit http://localhost:8000/docs — the auto-generated Swagger UI.

---

## Step 7 — Set up the React frontend

Open a NEW terminal window (keep the backend running in the first one):

```bash
cd trading-system/frontend
npm install
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

**Verify:** Open http://localhost:5173 in your browser.

You should see the trading dashboard with a dark sidebar. The Dashboard page
should show green dots for "API: Online" and "Database: Connected".

---

## Step 8 — Run the tests

```bash
# From project root, with venv activated:
pytest backend/tests/test_health.py -v
```

Expected output:
```
PASSED backend/tests/test_health.py::test_root_endpoint
PASSED backend/tests/test_health.py::test_health_endpoint_structure
PASSED backend/tests/test_health.py::test_health_endpoint_db_connected
```

---

## Phase 1 Complete ✓

You should now have:
- ✅ PostgreSQL running with all tables created
- ✅ FastAPI serving at http://localhost:8000
- ✅ React dashboard at http://localhost:5173
- ✅ Frontend calling backend and showing green system status
- ✅ All tests passing

**Next:** Phase 2 — Market Data Service (MT5 connection + live price streaming)

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'backend'`**
Make sure you're running uvicorn from the project root, not from inside the `backend/` folder.

**`psycopg2.OperationalError: could not connect to server`**
- Check PostgreSQL is running (Windows: open Services, look for PostgreSQL)
- Double-check the password in your `.env` file
- Make sure the database `trading_system` was created

**`alembic: command not found`**
Your virtual environment isn't activated. Run `venv\Scripts\activate` first.

**React page is blank / navigation not working**
Make sure you installed `react-router-dom`: `npm install react-router-dom axios`

**`CORS error` in browser console**
The FastAPI backend isn't running, or it's running on a different port.
Check that uvicorn is running on port 8000.
