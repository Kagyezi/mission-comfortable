"""
Internal event schemas — the contracts between every module in the pipeline.

Data flow:
  MarketDataEvent  →  MDS         → Bot Engine
  SignalEvent      →  Bot Engine  → Decision Engine
  DecisionEvent    →  Decision    → Execution Engine
  TradeEvent       →  Execution   → Monitoring & Logging
  SystemEvent      →  Any module  → Monitoring & Logging
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
from uuid import UUID, uuid4


# ──────────────────────────────────────────────
# MDS → Bot Engine
# ──────────────────────────────────────────────
class MarketDataEvent(BaseModel):
    """One normalized OHLCV candle published by the Market Data Service."""
    pair:       str       # e.g. "EURUSD"
    timeframe:  str       # e.g. "M15"
    timestamp:  datetime
    open:       float
    high:       float
    low:        float
    close:      float
    volume:     float


# ──────────────────────────────────────────────
# Bot Engine → Decision Engine
# ──────────────────────────────────────────────
class SignalEvent(BaseModel):
    """Trade signal produced by a bot after running strategy logic."""
    signal_id:   UUID    = Field(default_factory=uuid4)
    bot_id:      str                                      # matches bots.id in DB
    pair:        str
    action:      Literal["BUY", "SELL", "HOLD"]
    confidence:  float                                    # 0.0 – 1.0
    stop_loss:   float
    take_profit: float
    timeframe:   str
    timestamp:   datetime
    metadata:    dict = Field(default_factory=dict)       # indicators, debug info


# ──────────────────────────────────────────────
# Decision Engine → Execution Engine
# ──────────────────────────────────────────────
class DecisionEvent(BaseModel):
    """
    Output of the Decision Engine.
    Only APPROVED and RESIZED events are forwarded to the Execution Engine.
    REJECTED events are logged but not forwarded.
    """
    decision_id:      UUID    = Field(default_factory=uuid4)
    signal_id:        UUID                                # links back to SignalEvent
    pair:             str
    action:           Literal["BUY", "SELL"]
    status:           Literal["APPROVED", "REJECTED", "RESIZED"]
    lot_size:         float                               # calculated by position sizer
    stop_loss:        float
    take_profit:      float
    rejection_reason: Optional[str] = None               # set only if REJECTED
    timestamp:        datetime


# ──────────────────────────────────────────────
# Execution Engine → Monitoring & Logging
# ──────────────────────────────────────────────
class TradeEvent(BaseModel):
    """
    Emitted by the Execution Engine on every state change of a trade:
      - status="opened"  → trade just entered
      - status="closed"  → trade hit SL, TP, or was manually closed
      - status="failed"  → order could not be placed after retries
    """
    trade_id:        UUID    = Field(default_factory=uuid4)
    decision_id:     UUID
    pair:            str
    direction:       Literal["BUY", "SELL"]
    entry_price:     float
    lot_size:        float
    stop_loss:       float
    take_profit:     float
    mode:            Literal["paper", "live"]
    status:          Literal["opened", "closed", "failed"]
    timestamp:       datetime
    # Set on close:
    exit_price:      Optional[float] = None
    pnl:             Optional[float] = None               # in account currency
    pnl_pips:        Optional[float] = None
    close_reason:    Optional[str]  = None                # sl_hit, tp_hit, manual…
    # Execution metadata:
    fill_latency_ms: Optional[int]   = None
    slippage_pips:   Optional[float] = None


# ──────────────────────────────────────────────
# Any module → Monitoring & Logging
# ──────────────────────────────────────────────
class SystemEvent(BaseModel):
    """Structured log event emitted by any module for observability."""
    component: Literal["mds", "bot", "decision_engine", "execution", "api"]
    level:     Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    message:   str
    metadata:  dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
