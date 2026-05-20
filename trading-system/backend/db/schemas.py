"""
Pydantic schemas for FastAPI request/response serialization.
These are separate from SQLAlchemy models — models talk to the DB,
schemas talk to the API.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


# ─── Bot ──────────────────────────────────────────────────────
class BotResponse(BaseModel):
    id:            UUID
    name:          str
    version:       str
    strategy_type: str
    timeframe:     str
    status:        str
    mode:          str
    config:        dict
    created_at:    datetime

    model_config = {"from_attributes": True}


class BotUpdate(BaseModel):
    status: Optional[str] = None   # active, paused, stopped
    mode:   Optional[str] = None   # paper, live
    config: Optional[dict] = None


# ─── Signal ───────────────────────────────────────────────────
class SignalResponse(BaseModel):
    id:               UUID
    bot_id:           UUID
    pair:             str
    action:           str
    confidence:       float
    stop_loss:        float
    take_profit:      float
    timeframe:        str
    status:           str
    rejection_reason: Optional[str]
    created_at:       datetime

    model_config = {"from_attributes": True}


# ─── Trade ────────────────────────────────────────────────────
class TradeResponse(BaseModel):
    id:           UUID
    signal_id:    UUID
    bot_id:       UUID
    pair:         str
    direction:    str
    entry_price:  float
    exit_price:   Optional[float]
    lot_size:     float
    stop_loss:    float
    take_profit:  float
    opened_at:    datetime
    closed_at:    Optional[datetime]
    pnl:          Optional[float]
    pnl_pips:     Optional[float]
    status:       str
    close_reason: Optional[str]
    mode:         str

    model_config = {"from_attributes": True}


# ─── Risk Config ──────────────────────────────────────────────
class RiskConfigResponse(BaseModel):
    id:                   UUID
    max_drawdown_pct:     float
    max_open_trades:      int
    daily_loss_limit_pct: float
    risk_per_trade_pct:   float
    max_lot_size:         float
    is_active:            bool

    model_config = {"from_attributes": True}


class RiskConfigUpdate(BaseModel):
    max_drawdown_pct:     Optional[float] = None
    max_open_trades:      Optional[int]   = None
    daily_loss_limit_pct: Optional[float] = None
    risk_per_trade_pct:   Optional[float] = None
    max_lot_size:         Optional[float] = None


# ─── Portfolio ────────────────────────────────────────────────
class PortfolioResponse(BaseModel):
    balance:      float
    equity:       float
    open_pnl:     float
    drawdown_pct: float
    mode:         str


# ─── System Health ────────────────────────────────────────────
class HealthResponse(BaseModel):
    status:   str
    database: str
    version:  str


# ─── Bot Metrics ──────────────────────────────────────────────
class BotMetricResponse(BaseModel):
    bot_id:           UUID
    timestamp:        datetime
    total_trades:     int
    win_rate:         Optional[float]
    profit_factor:    Optional[float]
    sharpe_ratio:     Optional[float]
    max_drawdown_pct: Optional[float]
    expectancy:       Optional[float]

    model_config = {"from_attributes": True}
