# mission-comfortable Version 1.0 — MVP Blueprint

---

## 1. Module Responsibilities

### MT5 Platform / Broker API
The external dependency. Not code you write — the MetaTrader5 Python library.

**Provides:**
- Live tick and OHLCV candle data
- Account info (balance, equity, margin, open positions)
- Order placement, modification, and closure
- Historical OHLCV data (for backtesting and training)
- Connection to your Forex broker

**Your responsibility:** treat this as a black box. All interaction goes through the Market Data Service (for data) and Execution Engine (for orders). Nothing else touches MT5 directly.

---

### Market Data Service (MDS)
The single point of contact with MT5 for all market data.

**Responsibilities:**
- Establish and maintain the MT5 connection
- Subscribe to configured currency pairs
- Receive raw ticks and OHLCV candles from MT5
- Clean data (handle gaps, duplicate ticks, malformed candles)
- Normalize data format into a consistent internal structure
- Publish normalized MarketDataEvents to the bot via internal queue
- Handle MT5 disconnection and auto-reconnect
- Log connection status and data quality issues

**Does NOT:**
- Do feature engineering
- Know anything about bots or strategies
- Place orders

---

### Bot Engine
Where the trading intelligence lives. One bot for MVP.

**Responsibilities:**
- Listen for MarketDataEvents from MDS
- Perform feature engineering on each new candle:
  - EMA (fast and slow)
  - RSI
  - ATR (used for stop loss sizing)
  - Any additional indicators the strategy needs
- Run strategy logic (rule-based EMA crossover + RSI filter for MVP)
- Optionally pass features through an ML model (XGBoost confidence filter — Phase 2)
- Generate a SignalEvent: `{ pair, action, confidence, stop_loss, take_profit }`
- Send SignalEvent to Decision Engine
- Track and report its own performance metrics

**Does NOT:**
- Access MT5
- Place orders
- Make risk decisions
- Control capital

**Design principle:** build as a plug-in. The bot implements a `BaseBot` abstract class with a standard interface. Adding a second bot later means creating a new class — not rewriting the system.

---

### Decision Engine
The gatekeeper between the bot and the market. Combines signal aggregation and risk management for MVP.

**Responsibilities:**

*Risk Validation (in order):*
1. Check if action is BUY or SELL (ignore HOLD)
2. Check current drawdown vs. max allowed drawdown
3. Check daily P&L loss vs. daily loss limit
4. Check number of open positions vs. max allowed
5. Check if a trade on this pair is already open
6. Check account margin availability

*Position Sizing:*
- Calculate lot size based on: risk % per trade, account balance, ATR-based stop loss distance
- Formula: `lot_size = (balance × risk_pct) / (stop_loss_distance × pip_value)`
- Resize lot size down if it exceeds max_lot_size limit

*Decision Output:*
- APPROVED: signal passes all checks → forward to execution with calculated lot size
- REJECTED: signal fails a check → log reason, do not forward
- RESIZED: signal approved but lot size reduced to fit limits

*Future (multi-bot):*
- The aggregation layer (ranking signals by confidence, resolving conflicts) slots in here as a separate function before risk validation

**Does NOT:**
- Analyze market data
- Know what strategy the bot is using
- Place orders

---

### Execution Engine
The only component that talks to MT5 for orders.

**Responsibilities:**
- Receive approved DecisionEvents
- Check current mode: `paper` or `live`

*Paper Mode:*
- Simulate order at current market price
- Record synthetic entry price, timestamp, lot size
- Monitor open paper positions on each tick (check if SL or TP hit)
- Close paper position and record P&L when SL/TP triggered

*Live Mode:*
- Send order to MT5 via broker API
- Confirm fill (actual price, actual volume, timestamp)
- Track slippage (difference between requested and filled price)
- Handle failed orders (retry up to N times, then log failure)
- Monitor open positions (poll MT5 for position status)
- Close positions when SL/TP hit or manual close triggered

**In both modes:**
- Emit TradeEvents to Monitoring & Logging on open and close
- Maintain internal state of all open positions

**Does NOT:**
- Analyze signals
- Make risk decisions
- Contain any strategy logic

---

### Monitoring & Logging
The system's memory and observability layer.

**Responsibilities:**
- Receive and store all events from all modules (signals, decisions, trades, system events)
- Write structured records to PostgreSQL
- Track bot performance metrics:
  - Win rate, profit factor, Sharpe ratio, max drawdown, expectancy
  - Recalculate on every trade close
- Expose data via FastAPI to the React frontend
- Log system health events (MT5 connection status, component errors, latency)

**Does NOT:**
- Make any trading decisions
- Talk to MT5
- Contain business logic

---

### Database — PostgreSQL
Persistent storage for everything.

**Stores:**
- All signals (raw bot predictions, approved/rejected status)
- All trades (entry, exit, P&L, metadata)
- All risk events (why signals were rejected)
- Execution logs (fill prices, slippage, latency)
- System logs (component events, errors)
- Portfolio history snapshots (balance, equity, drawdown over time)
- Risk configuration (editable live risk parameters)
- Bot registry and configuration
- Bot performance metrics

---

### FastAPI Backend
Orchestration and API layer. Not where trading logic lives.

**Responsibilities:**
- REST API for all frontend data requests
- WebSocket server for real-time streaming (live prices, live signals, live trade updates)
- Bot management endpoints (start, stop, update config)
- Risk configuration endpoints (read and write risk params live)
- Trade history and portfolio endpoints
- System health endpoints

---

### React Frontend
The command centre. Visualization and configuration only — no trading logic.

**Pages:**
- **Dashboard** — portfolio balance, equity, daily P&L, open trades, last 5 closed trades, system health
- **Bot Management** — bot status, metrics, start/stop, config
- **Trade Log** — all open and closed trades with filters
- **Charts** — TradingView chart with entry/exit markers, live price
- **Risk Settings** — live-editable risk parameters, kill switch
- **System Monitor** — MT5 connection, bot uptime, WebSocket status, error log

---

### Backtesting (Offline Module)
Not part of the live pipeline. Runs offline before deploying any strategy.

**Responsibilities:**
- Fetch historical OHLCV data from MT5 for a given pair and timeframe
- Replay historical data through the bot's feature engineering and strategy logic
- Simulate decision engine risk checks and position sizing
- Record all simulated trades
- Report: win rate, profit factor, Sharpe ratio, max drawdown, expectancy, total trades
- Acts as a quality gate — a strategy must pass backtesting before going live

---

## 2. Data Flow

```
[MT5 Broker Feed]
        |
        | raw ticks / OHLCV candles
        ▼
[Market Data Service]
        |
        | MarketDataEvent (normalized OHLCV)
        ▼
[Bot Engine]
        |  - compute features (EMA, RSI, ATR)
        |  - run strategy logic
        |
        | SignalEvent { pair, action, confidence, sl, tp }
        ▼
[Decision Engine]
        |  - risk validation
        |  - position sizing
        |
        | DecisionEvent { action, status, lot_size, sl, tp }
        ▼
[Execution Engine] ──────────────────────────────► [MT5 Broker]
        |                                          (live mode only)
        | TradeEvent { trade_id, entry_price,
        |              status, mode, slippage }
        ▼
[Monitoring & Logging]
        |
        | writes to
        ▼
[PostgreSQL Database]
        |
        | queries
        ▼
[FastAPI Backend]
        |
        | REST / WebSocket
        ▼
[React Frontend]
```

**Key rules:**
- MT5 is accessed by exactly two components: MDS (data) and Execution Engine (orders)
- All inter-module communication uses typed event objects (defined in `shared/events.py`)
- The database is written to by Monitoring & Logging and read by FastAPI
- The frontend never talks to the trading pipeline directly — only through FastAPI

---

## 3. Database Schema

```sql
-- Bot registry
CREATE TABLE bots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    version         VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    strategy_type   VARCHAR(50) NOT NULL,       -- 'technical', 'fundamental'
    timeframe       VARCHAR(10) NOT NULL,        -- 'M5', 'M15', 'H1', etc.
    status          VARCHAR(20) NOT NULL DEFAULT 'stopped',  -- 'active', 'paused', 'stopped'
    mode            VARCHAR(10) NOT NULL DEFAULT 'paper',    -- 'paper', 'live'
    config          JSONB NOT NULL DEFAULT '{}', -- strategy parameters
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Raw bot signal predictions (every signal, approved or not)
CREATE TABLE signals (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id            UUID NOT NULL REFERENCES bots(id),
    pair              VARCHAR(10) NOT NULL,       -- 'EURUSD'
    action            VARCHAR(10) NOT NULL,        -- 'BUY', 'SELL', 'HOLD'
    confidence        FLOAT NOT NULL,              -- 0.0 to 1.0
    stop_loss         FLOAT NOT NULL,
    take_profit       FLOAT NOT NULL,
    timeframe         VARCHAR(10) NOT NULL,
    status            VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'approved', 'rejected', 'resized'
    rejection_reason  TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Executed trades (paper and live)
CREATE TABLE trades (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id       UUID NOT NULL REFERENCES signals(id),
    bot_id          UUID NOT NULL REFERENCES bots(id),
    pair            VARCHAR(10) NOT NULL,
    direction       VARCHAR(10) NOT NULL,          -- 'BUY', 'SELL'
    entry_price     FLOAT NOT NULL,
    exit_price      FLOAT,
    lot_size        FLOAT NOT NULL,
    stop_loss       FLOAT NOT NULL,
    take_profit     FLOAT NOT NULL,
    opened_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at       TIMESTAMPTZ,
    pnl             FLOAT,                         -- in account currency
    pnl_pips        FLOAT,
    status          VARCHAR(20) NOT NULL DEFAULT 'open',  -- 'open', 'closed', 'cancelled'
    close_reason    VARCHAR(50),                   -- 'sl_hit', 'tp_hit', 'manual', 'kill_switch'
    mode            VARCHAR(10) NOT NULL           -- 'paper', 'live'
);

-- Risk engine decisions and violations
CREATE TABLE risk_events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id   UUID REFERENCES signals(id),
    event_type  VARCHAR(50) NOT NULL,  -- 'drawdown_limit', 'daily_loss_limit',
                                       -- 'max_positions', 'signal_rejected',
                                       -- 'position_resized', 'kill_switch'
    details     JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Execution details (fill confirmation, slippage, retries)
CREATE TABLE execution_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id        UUID NOT NULL REFERENCES trades(id),
    action          VARCHAR(20) NOT NULL,   -- 'open', 'close', 'modify', 'retry'
    price           FLOAT NOT NULL,
    volume          FLOAT NOT NULL,
    slippage_pips   FLOAT,
    latency_ms      INT,
    status          VARCHAR(20) NOT NULL,   -- 'success', 'failed'
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- System-wide structured logs
CREATE TABLE system_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component   VARCHAR(50) NOT NULL,   -- 'mds', 'bot', 'decision_engine',
                                        -- 'execution', 'api'
    level       VARCHAR(20) NOT NULL,   -- 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    message     TEXT NOT NULL,
    metadata    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Portfolio snapshots over time (for equity curve)
CREATE TABLE portfolio_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    balance         FLOAT NOT NULL,
    equity          FLOAT NOT NULL,
    open_pnl        FLOAT NOT NULL DEFAULT 0,
    drawdown_pct    FLOAT NOT NULL DEFAULT 0,
    mode            VARCHAR(10) NOT NULL   -- 'paper', 'live'
);

-- Live-editable risk configuration
CREATE TABLE risk_config (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    max_drawdown_pct        FLOAT NOT NULL DEFAULT 10.0,
    max_open_trades         INT NOT NULL DEFAULT 3,
    daily_loss_limit_pct    FLOAT NOT NULL DEFAULT 5.0,
    risk_per_trade_pct      FLOAT NOT NULL DEFAULT 1.0,
    max_lot_size            FLOAT NOT NULL DEFAULT 0.10,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Computed bot performance metrics (recalculated on each trade close)
CREATE TABLE bot_metrics (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id              UUID NOT NULL REFERENCES bots(id),
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_trades        INT NOT NULL DEFAULT 0,
    win_rate            FLOAT,   -- % of winning trades
    profit_factor       FLOAT,   -- gross profit / gross loss
    sharpe_ratio        FLOAT,
    max_drawdown_pct    FLOAT,
    expectancy          FLOAT    -- avg profit per trade
);

-- Indexes for common queries
CREATE INDEX idx_trades_bot_id ON trades(bot_id);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_opened_at ON trades(opened_at DESC);
CREATE INDEX idx_signals_bot_id ON signals(bot_id);
CREATE INDEX idx_signals_status ON signals(status);
CREATE INDEX idx_system_logs_component ON system_logs(component);
CREATE INDEX idx_system_logs_level ON system_logs(level);
CREATE INDEX idx_portfolio_history_timestamp ON portfolio_history(timestamp DESC);
```

---

## 4. Internal Event Schema

All inter-module communication uses these Pydantic models, defined in `backend/shared/events.py`. Using typed events means any change to the data contract is caught immediately.

```python
from pydantic import BaseModel, UUID4
from typing import Literal, Optional
from datetime import datetime
from uuid import uuid4


# MDS → Bot Engine
class MarketDataEvent(BaseModel):
    pair: str                  # e.g. "EURUSD"
    timeframe: str             # e.g. "M15"
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


# Bot Engine → Decision Engine
class SignalEvent(BaseModel):
    signal_id: UUID4 = uuid4()
    bot_id: str
    pair: str
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float           # 0.0 to 1.0
    stop_loss: float
    take_profit: float
    timeframe: str
    timestamp: datetime
    metadata: dict = {}         # optional extra info (indicators, reasons)


# Decision Engine → Execution Engine
class DecisionEvent(BaseModel):
    decision_id: UUID4 = uuid4()
    signal_id: UUID4
    pair: str
    action: Literal["BUY", "SELL"]
    status: Literal["APPROVED", "REJECTED", "RESIZED"]
    lot_size: float
    stop_loss: float
    take_profit: float
    rejection_reason: Optional[str] = None
    timestamp: datetime


# Execution Engine → Monitoring & Logging
class TradeEvent(BaseModel):
    trade_id: UUID4 = uuid4()
    decision_id: UUID4
    pair: str
    direction: Literal["BUY", "SELL"]
    entry_price: float
    lot_size: float
    stop_loss: float
    take_profit: float
    mode: Literal["paper", "live"]
    status: Literal["opened", "closed", "failed"]
    timestamp: datetime
    fill_latency_ms: Optional[int] = None
    slippage_pips: Optional[float] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    close_reason: Optional[str] = None  # 'sl_hit', 'tp_hit', 'manual'


# System health events (any module → Monitoring)
class SystemEvent(BaseModel):
    component: Literal["mds", "bot", "decision_engine", "execution", "api"]
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    message: str
    metadata: dict = {}
    timestamp: datetime
```

---

## 5. MVP Feature Checklist

### Infrastructure
- [ ] PostgreSQL running locally
- [ ] All database tables created via Alembic migration
- [ ] FastAPI app running with `/health` endpoint
- [ ] React app running with all 6 pages (empty shells)
- [ ] Frontend successfully calls FastAPI health endpoint
- [ ] Environment variables and config loaded from `.env`

### Market Data Service
- [ ] MT5 connects and authenticates successfully
- [ ] Live OHLCV candles stream for at least one pair
- [ ] Data is normalized and published as `MarketDataEvent`
- [ ] MDS auto-reconnects on MT5 disconnect
- [ ] Connection status written to `system_logs`

### Bot Engine
- [ ] Bot receives `MarketDataEvent` from MDS
- [ ] Feature engineering computes EMA (fast/slow), RSI, ATR correctly
- [ ] Strategy logic produces BUY / SELL / HOLD signal
- [ ] Confidence score attached to signal
- [ ] Stop loss and take profit levels calculated
- [ ] `SignalEvent` emitted and sent to Decision Engine
- [ ] All signals written to `signals` table

### Decision Engine
- [ ] Max drawdown check works correctly
- [ ] Daily loss limit check works correctly
- [ ] Max open positions check works correctly
- [ ] Duplicate pair check works (no two trades on same pair)
- [ ] Position sizing formula produces correct lot sizes
- [ ] APPROVED signals forwarded to Execution Engine
- [ ] REJECTED signals logged to `risk_events` with reason
- [ ] RESIZED signals forwarded with corrected lot size

### Execution Engine — Paper Mode
- [ ] Paper order recorded at current market price on approval
- [ ] Open paper position stored in internal state
- [ ] Position monitor checks SL/TP on every new tick
- [ ] Position closed and P&L calculated when SL/TP triggered
- [ ] `TradeEvent` (opened) emitted on entry
- [ ] `TradeEvent` (closed) emitted on exit with P&L and close reason

### Monitoring & Logging
- [ ] All `SignalEvent`s written to `signals` table
- [ ] All `TradeEvent`s written to `trades` and `execution_logs` tables
- [ ] All `SystemEvent`s written to `system_logs` table
- [ ] Bot metrics recalculated and written to `bot_metrics` on every trade close
- [ ] Portfolio snapshot written to `portfolio_history` periodically

### Backtesting
- [ ] Historical OHLCV data fetched from MT5 for target pair
- [ ] Bot feature engineering runs on historical data
- [ ] Strategy generates signals on historical data
- [ ] Decision engine simulates risk checks on historical signals
- [ ] All simulated trades recorded
- [ ] Report output: win rate, profit factor, Sharpe, max drawdown, expectancy

### Backend API
- [ ] `GET /portfolio` — current balance, equity, daily P&L
- [ ] `GET /trades` — all trades with filters (status, date, pair)
- [ ] `GET /trades/{id}` — single trade detail
- [ ] `GET /signals` — signal log with approved/rejected status
- [ ] `GET /bots` — bot list with status and metrics
- [ ] `PATCH /bots/{id}` — start/stop bot, update config
- [ ] `GET /risk/config` — current risk parameters
- [ ] `PUT /risk/config` — update risk parameters
- [ ] `POST /risk/kill-switch` — pause all bots immediately
- [ ] `GET /system/health` — component status
- [ ] `GET /system/logs` — system log feed
- [ ] `WS /ws/prices` — live price stream
- [ ] `WS /ws/signals` — live signal stream
- [ ] `WS /ws/trades` — live trade update stream

### Frontend
- [ ] **Dashboard** — balance, equity, daily P&L, open positions count, active bot status, last 5 closed trades, system health indicator
- [ ] **Bot Management** — bot card with status, metrics, start/stop toggle, mode toggle (paper/live), config editor
- [ ] **Trade Log** — table of all trades, filterable by status/pair/date, win/loss badge, P&L column
- [ ] **Charts** — TradingView chart, pair selector, timeframe selector, entry/exit markers plotted from trade data
- [ ] **Risk Settings** — editable form for all risk parameters, kill switch button, live save
- [ ] **System Monitor** — MT5 connection status, bot uptime, last signal timestamp, WebSocket status, error log feed

### Live Trading (Final Gate — demo account first)
- [ ] MT5 live order placement tested on demo account
- [ ] Fill confirmation and slippage tracking working
- [ ] Failed order retry logic tested
- [ ] System runs stable for 48 hours on demo without crashing

---

## 6. Repository Structure

```
trading-system/
│
├── backend/
│   ├── core/
│   │   ├── market_data_service/
│   │   │   ├── __init__.py
│   │   │   ├── connector.py       # MT5 connection and auth
│   │   │   ├── feed.py            # tick and candle streaming
│   │   │   ├── normalizer.py      # data cleaning and formatting
│   │   │   └── publisher.py       # publishes MarketDataEvent to queue
│   │   │
│   │   ├── bot_engine/
│   │   │   ├── __init__.py
│   │   │   ├── base_bot.py        # abstract BaseBot interface
│   │   │   ├── features.py        # feature engineering (EMA, RSI, ATR)
│   │   │   ├── bots/
│   │   │   │   └── technical_bot.py   # EMA crossover + RSI strategy
│   │   │   └── registry.py        # bot registration and lookup
│   │   │
│   │   ├── decision_engine/
│   │   │   ├── __init__.py
│   │   │   ├── risk.py            # risk validation checks
│   │   │   ├── sizer.py           # position sizing formula
│   │   │   ├── aggregator.py      # future: multi-bot signal ranking
│   │   │   └── engine.py          # main decision orchestration
│   │   │
│   │   ├── execution_engine/
│   │   │   ├── __init__.py
│   │   │   ├── paper.py           # paper trading simulator
│   │   │   ├── live.py            # MT5 live order execution
│   │   │   ├── monitor.py         # open position monitoring (SL/TP)
│   │   │   ├── executor.py        # routes to paper or live based on mode
│   │   │   └── recovery.py        # retry logic and fault handling
│   │   │
│   │   └── monitoring/
│   │       ├── __init__.py
│   │       ├── logger.py          # structured event logging to DB
│   │       └── metrics.py         # bot performance metric calculator
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── portfolio.py
│   │   │   ├── trades.py
│   │   │   ├── signals.py
│   │   │   ├── bots.py
│   │   │   ├── risk.py
│   │   │   └── system.py
│   │   └── websocket/
│   │       └── streams.py         # WebSocket handlers (prices, signals, trades)
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   ├── schemas.py             # Pydantic request/response schemas
│   │   ├── session.py             # DB session management
│   │   └── migrations/            # Alembic migration files
│   │       └── versions/
│   │
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── events.py              # all internal event Pydantic models
│   │   ├── config.py              # loads settings from .env and YAML
│   │   └── constants.py           # shared constants (timeframes, pairs, etc.)
│   │
│   ├── backtesting/
│   │   ├── __init__.py
│   │   ├── data_fetcher.py        # fetches historical OHLCV from MT5
│   │   ├── runner.py              # replays data through bot + decision engine
│   │   └── reporter.py            # calculates and prints performance metrics
│   │
│   ├── config/
│   │   ├── settings.yaml          # risk params, bot params, pair config
│   │   └── .env                   # secrets (MT5 login, DB URL) — never commit
│   │
│   ├── tests/
│   │   ├── test_market_data.py
│   │   ├── test_bot_engine.py
│   │   ├── test_decision_engine.py
│   │   ├── test_execution.py
│   │   └── test_api.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── BotManagement.jsx
│   │   │   ├── TradeLog.jsx
│   │   │   ├── Charts.jsx
│   │   │   ├── RiskSettings.jsx
│   │   │   └── SystemMonitor.jsx
│   │   │
│   │   ├── components/
│   │   │   ├── BotCard.jsx
│   │   │   ├── TradeTable.jsx
│   │   │   ├── MetricCard.jsx
│   │   │   ├── SignalFeed.jsx
│   │   │   ├── RiskPanel.jsx
│   │   │   ├── SystemHealthBadge.jsx
│   │   │   └── TradingChart.jsx   # TradingView wrapper
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js    # WebSocket connection manager
│   │   │   ├── useTrades.js
│   │   │   ├── usePortfolio.js
│   │   │   └── useSystemHealth.js
│   │   │
│   │   ├── api/
│   │   │   └── client.js          # axios instance with base URL
│   │   │
│   │   ├── App.jsx                # router and layout
│   │   └── main.jsx
│   │
│   ├── public/
│   └── package.json
│
├── .gitignore
└── README.md
```

---

## 7. Implementation Order

Build in this sequence. Each phase produces something testable before moving to the next.

---

### Phase 1 — Project Foundation
*Goal: empty but wired-up skeleton running locally*

1. Initialize git repo, create folder structure
2. Set up Python virtual environment, create `requirements.txt`
3. Install and run PostgreSQL locally
4. Write SQLAlchemy models (`db/models.py`)
5. Set up Alembic, run first migration (create all tables)
6. Create FastAPI app with a single `GET /health` endpoint
7. Confirm FastAPI connects to PostgreSQL on startup
8. Create React app (Vite), install React Router, create 6 empty page components
9. Add sidebar navigation between pages
10. Confirm React app calls `/health` and displays a response

**Checkpoint:** FastAPI running, DB migrated, React talking to backend. ✓

---

### Phase 2 — Market Data Service
*Goal: live Forex candles flowing through the system*

11. Install `MetaTrader5` Python library
12. Build `connector.py` — connect, login, verify account
13. Build `feed.py` — subscribe to EURUSD, stream M15 candles
14. Build `normalizer.py` — clean and format candles into `MarketDataEvent`
15. Build `publisher.py` — put `MarketDataEvent` into an `asyncio.Queue`
16. Write a simple consumer that prints events to console
17. Test: confirm live EURUSD M15 candles print with correct OHLCV values
18. Add reconnection logic and log connection status to `system_logs`

**Checkpoint:** Live market data flowing and logged. ✓

---

### Phase 3 — Bot Engine
*Goal: bot generating trade signals from live data*

19. Write `base_bot.py` — abstract `BaseBot` class with standard interface
20. Build `features.py`:
    - `compute_ema(prices, period)` 
    - `compute_rsi(prices, period)`
    - `compute_atr(highs, lows, closes, period)`
21. Build `technical_bot.py`:
    - Maintain a rolling window of candles
    - Compute features on each new candle
    - EMA crossover logic (fast crosses above/below slow)
    - RSI filter (only BUY if RSI < 70, only SELL if RSI > 30)
    - Attach confidence score (simple rule: distance of crossover / ATR)
    - Calculate SL (entry ± 1.5 × ATR) and TP (entry ± 3 × ATR)
    - Emit `SignalEvent`
22. Wire bot to consume from MDS queue
23. Test: confirm bot generates BUY/SELL signals with valid SL/TP values

**Checkpoint:** Bot generating signals from live data. ✓

---

### Phase 4 — Decision Engine
*Goal: signals being validated against risk rules before execution*

24. Build `risk.py`:
    - `check_drawdown(current_equity, peak_equity, max_pct)` → bool
    - `check_daily_loss(todays_pnl, balance, limit_pct)` → bool
    - `check_open_positions(open_count, max_count)` → bool
    - `check_pair_already_open(pair, open_positions)` → bool
25. Build `sizer.py`:
    - `calculate_lot_size(balance, risk_pct, sl_distance_pips, pip_value)` → float
    - Cap at `max_lot_size` from risk config
26. Build `engine.py`:
    - Run all risk checks in sequence
    - If any fail → emit REJECTED `DecisionEvent`, write to `risk_events`
    - If all pass → calculate lot size, emit APPROVED `DecisionEvent`
27. Wire Decision Engine between bot output and execution input
28. Test: manually set risk limits to force rejections and confirm they log correctly

**Checkpoint:** Risk rules enforced, decisions logged. ✓

---

### Phase 5 — Execution Engine (Paper Mode)
*Goal: full pipeline running end-to-end in paper mode*

29. Build `paper.py`:
    - On APPROVED `DecisionEvent`: record synthetic trade at current price
    - Maintain a dict of open paper positions keyed by trade_id
30. Build `monitor.py`:
    - On every `MarketDataEvent`: check each open position's SL and TP
    - If current price crosses SL → close position, record P&L as negative
    - If current price crosses TP → close position, record P&L as positive
31. Build `executor.py` — routes to `paper.py` or `live.py` based on mode flag
32. Wire `TradeEvent` emissions (opened, closed) to Monitoring & Logging
33. Test: run full pipeline for several hours, confirm trades open, hit SL/TP, close correctly

**Checkpoint:** Full pipeline working in paper mode. ✓

---

### Phase 6 — Monitoring & Logging
*Goal: all events persisted to database*

34. Build `logger.py` — async writer that inserts events into correct tables
35. Wire every module to emit `SystemEvent` on errors and key state changes
36. Build `metrics.py`:
    - On every trade close, recalculate win rate, profit factor, Sharpe, max drawdown, expectancy
    - Write results to `bot_metrics`
37. Add periodic portfolio snapshot writer (every 15 minutes → `portfolio_history`)
38. Test: after a paper trading session, verify all tables have correct records

**Checkpoint:** Complete audit trail in PostgreSQL. ✓

---

### Phase 7 — Backtesting
*Goal: validate strategy on historical data before going live*

39. Build `data_fetcher.py` — pull 6–12 months of EURUSD M15 data from MT5
40. Build `runner.py` — replay historical candles through bot + decision engine (no live MT5)
41. Build `reporter.py` — print performance report to console
42. Run backtests, review results, iterate on strategy parameters
43. Only proceed to Phase 8 if backtest results are acceptable

**Checkpoint:** Strategy validated on historical data. ✓

---

### Phase 8 — Backend API
*Goal: FastAPI serving all data the frontend needs*

44. Build REST routes (portfolio, trades, signals, bots, risk, system)
45. Build WebSocket streams (prices, signals, trade updates)
46. Test all endpoints with a REST client (Postman or Insomnia)
47. Test WebSocket connections with a simple browser script

**Checkpoint:** All API endpoints working and returning correct data. ✓

---

### Phase 9 — Frontend
*Goal: fully functional dashboard connected to live backend*

48. **Dashboard** — fetch portfolio data, open trades, last 5 trades, system health
49. **Trade Log** — fetch and display all trades, add status/pair/date filters
50. **Charts** — integrate TradingView Lightweight Charts, overlay entry/exit markers
51. **Bot Management** — display bot card, wire start/stop toggle, mode toggle (paper/live)
52. **Risk Settings** — build editable form, wire save to `PUT /risk/config`, add kill switch button
53. **System Monitor** — display MT5 status, bot uptime, last signal time, error log feed
54. Connect WebSocket hooks for real-time updates across all pages

**Checkpoint:** All 6 pages functional with live data. ✓

---

### Phase 10 — Live Trading (Demo Account)
*Goal: stable live execution before touching real money*

55. Build `live.py` — MT5 live order placement via `order_send()`
56. Build retry logic (up to 3 attempts on failed order, then log and alert)
57. Switch mode to `live`, connect to MT5 demo account
58. Monitor for 48 hours continuously
59. Verify: no crashes, correct SL/TP execution, slippage within acceptable range
60. Review all logs and fix any edge cases found

**Checkpoint:** System runs stably on demo for 48 hours. ✓

**Only after this checkpoint: switch to a real account with minimum capital.**

---

*End of Blueprint*
