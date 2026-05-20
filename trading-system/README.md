# Trading System

An ML-powered Forex trading system with a centralized risk engine, automated signal generation, and a React dashboard.

---

## Architecture

```
MT5 → Market Data Service → Bot Engine → Decision Engine → Execution Engine
                                                                    ↓
                                               Monitoring & Logging → PostgreSQL
                                                                    ↓
                                                    FastAPI → React Frontend
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- MetaTrader 5 (Windows only — required for live/paper trading)

---

## Backend Setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Configure environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials and MT5 login
```

### Create the database

```bash
# In PostgreSQL shell or pgAdmin:
CREATE DATABASE trading_db;
```

### Run migrations

```bash
alembic upgrade head
```

### Start the backend

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173  
Backend API at: http://localhost:8000  
API docs at: http://localhost:8000/docs

---

## Project Structure

```
trading-system/
├── backend/
│   ├── alembic/            # Database migrations
│   ├── api/                # FastAPI app and routes
│   ├── core/               # Trading pipeline modules
│   │   ├── market_data_service/
│   │   ├── bot_engine/
│   │   ├── decision_engine/
│   │   ├── execution_engine/
│   │   └── monitoring/
│   ├── db/                 # SQLAlchemy models and session
│   ├── shared/             # Events, config, constants
│   ├── backtesting/        # Offline backtesting module
│   └── tests/
└── frontend/
    └── src/
        ├── pages/          # 6 dashboard pages
        ├── components/     # Shared UI components
        ├── hooks/          # React hooks
        └── api/            # Axios client
```

---

## Implementation Phases

- [x] **Phase 1** — Project foundation, DB schema, FastAPI skeleton, React shell
- [ ] **Phase 2** — Market Data Service (MT5 connection, live data)
- [ ] **Phase 3** — Bot Engine (feature engineering, signal generation)
- [ ] **Phase 4** — Decision Engine (risk validation, position sizing)
- [ ] **Phase 5** — Execution Engine (paper trading mode)
- [ ] **Phase 6** — Monitoring & Logging
- [ ] **Phase 7** — Backtesting
- [ ] **Phase 8** — Backend API (all routes + WebSocket)
- [ ] **Phase 9** — Frontend (all 6 pages wired up)
- [ ] **Phase 10** — Live trading on MT5 demo account

---

## Notes

- MetaTrader5 Python library only works on **Windows 64-bit**
- Always validate a strategy with backtesting before enabling paper trading
- Always run paper trading for at least 48 hours before switching to live
- Never commit `.env` to version control
