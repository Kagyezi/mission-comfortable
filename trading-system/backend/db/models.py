"""
SQLAlchemy ORM models — one class per database table.
All tables defined in the blueprint are implemented here.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    String, Float, Integer, Boolean, Text,
    ForeignKey, DateTime, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base


# ─────────────────────────────────────────────────────────────
# Bot registry
# ─────────────────────────────────────────────────────────────
class Bot(Base):
    __tablename__ = "bots"

    id:             Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name:           Mapped[str]        = mapped_column(String(100), nullable=False)
    version:        Mapped[str]        = mapped_column(String(20), nullable=False, default="1.0.0")
    strategy_type:  Mapped[str]        = mapped_column(String(50), nullable=False)   # 'technical', 'fundamental'
    timeframe:      Mapped[str]        = mapped_column(String(10), nullable=False)   # 'M15', 'H1', etc.
    status:         Mapped[str]        = mapped_column(String(20), nullable=False, default="stopped")  # active, paused, stopped
    mode:           Mapped[str]        = mapped_column(String(10), nullable=False, default="paper")    # paper, live
    config:         Mapped[dict]       = mapped_column(JSONB, nullable=False, default=dict)
    created_at:     Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:     Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    signals:        Mapped[list["Signal"]]     = relationship("Signal", back_populates="bot")
    trades:         Mapped[list["Trade"]]      = relationship("Trade", back_populates="bot")
    metrics:        Mapped[list["BotMetric"]]  = relationship("BotMetric", back_populates="bot")


# ─────────────────────────────────────────────────────────────
# Every signal the bot generates (approved or not)
# ─────────────────────────────────────────────────────────────
class Signal(Base):
    __tablename__ = "signals"

    id:               Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id:           Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False)
    pair:             Mapped[str]             = mapped_column(String(10), nullable=False)
    action:           Mapped[str]             = mapped_column(String(10), nullable=False)   # BUY, SELL, HOLD
    confidence:       Mapped[float]           = mapped_column(Float, nullable=False)
    stop_loss:        Mapped[float]           = mapped_column(Float, nullable=False)
    take_profit:      Mapped[float]           = mapped_column(Float, nullable=False)
    timeframe:        Mapped[str]             = mapped_column(String(10), nullable=False)
    status:           Mapped[str]             = mapped_column(String(20), nullable=False, default="pending")  # pending, approved, rejected, resized
    rejection_reason: Mapped[str | None]      = mapped_column(Text, nullable=True)
    created_at:       Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    bot:         Mapped["Bot"]          = relationship("Bot", back_populates="signals")
    trades:      Mapped[list["Trade"]]  = relationship("Trade", back_populates="signal")
    risk_events: Mapped[list["RiskEvent"]] = relationship("RiskEvent", back_populates="signal")


# ─────────────────────────────────────────────────────────────
# Every executed trade (paper and live)
# ─────────────────────────────────────────────────────────────
class Trade(Base):
    __tablename__ = "trades"

    id:           Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id:    Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id"), nullable=False)
    bot_id:       Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False)
    pair:         Mapped[str]           = mapped_column(String(10), nullable=False)
    direction:    Mapped[str]           = mapped_column(String(10), nullable=False)   # BUY, SELL
    entry_price:  Mapped[float]         = mapped_column(Float, nullable=False)
    exit_price:   Mapped[float | None]  = mapped_column(Float, nullable=True)
    lot_size:     Mapped[float]         = mapped_column(Float, nullable=False)
    stop_loss:    Mapped[float]         = mapped_column(Float, nullable=False)
    take_profit:  Mapped[float]         = mapped_column(Float, nullable=False)
    opened_at:    Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at:    Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pnl:          Mapped[float | None]  = mapped_column(Float, nullable=True)         # account currency
    pnl_pips:     Mapped[float | None]  = mapped_column(Float, nullable=True)
    status:       Mapped[str]           = mapped_column(String(20), nullable=False, default="open")  # open, closed, cancelled
    close_reason: Mapped[str | None]    = mapped_column(String(50), nullable=True)    # sl_hit, tp_hit, manual…
    mode:         Mapped[str]           = mapped_column(String(10), nullable=False)   # paper, live

    # Relationships
    signal:         Mapped["Signal"]              = relationship("Signal", back_populates="trades")
    bot:            Mapped["Bot"]                 = relationship("Bot", back_populates="trades")
    execution_logs: Mapped[list["ExecutionLog"]]  = relationship("ExecutionLog", back_populates="trade")


# ─────────────────────────────────────────────────────────────
# Risk engine decisions and violations
# ─────────────────────────────────────────────────────────────
class RiskEvent(Base):
    __tablename__ = "risk_events"

    id:         Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id:  Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id"), nullable=True)
    event_type: Mapped[str]             = mapped_column(String(50), nullable=False)
    # Examples: drawdown_limit, daily_loss_limit, max_positions,
    #           signal_rejected, position_resized, kill_switch
    details:    Mapped[dict]            = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    signal: Mapped["Signal | None"] = relationship("Signal", back_populates="risk_events")


# ─────────────────────────────────────────────────────────────
# Execution fill details (confirms, slippage, retries)
# ─────────────────────────────────────────────────────────────
class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id:            Mapped[uuid.UUID]    = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id:      Mapped[uuid.UUID]    = mapped_column(UUID(as_uuid=True), ForeignKey("trades.id"), nullable=False)
    action:        Mapped[str]          = mapped_column(String(20), nullable=False)   # open, close, modify, retry
    price:         Mapped[float]        = mapped_column(Float, nullable=False)
    volume:        Mapped[float]        = mapped_column(Float, nullable=False)
    slippage_pips: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms:    Mapped[int | None]   = mapped_column(Integer, nullable=True)
    status:        Mapped[str]          = mapped_column(String(20), nullable=False)   # success, failed
    error_message: Mapped[str | None]   = mapped_column(Text, nullable=True)
    created_at:    Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    trade: Mapped["Trade"] = relationship("Trade", back_populates="execution_logs")


# ─────────────────────────────────────────────────────────────
# System-wide structured logs (all components)
# ─────────────────────────────────────────────────────────────
class SystemLog(Base):
    __tablename__ = "system_logs"

    id:         Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component:  Mapped[str]        = mapped_column(String(50), nullable=False)   # mds, bot, decision_engine…
    level:      Mapped[str]        = mapped_column(String(20), nullable=False)   # DEBUG, INFO, WARNING, ERROR
    message:    Mapped[str]        = mapped_column(Text, nullable=False)
    metadata:   Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())


# ─────────────────────────────────────────────────────────────
# Portfolio balance/equity snapshots over time (equity curve)
# ─────────────────────────────────────────────────────────────
class PortfolioHistory(Base):
    __tablename__ = "portfolio_history"

    id:           Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp:    Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    balance:      Mapped[float]     = mapped_column(Float, nullable=False)
    equity:       Mapped[float]     = mapped_column(Float, nullable=False)
    open_pnl:     Mapped[float]     = mapped_column(Float, nullable=False, default=0.0)
    drawdown_pct: Mapped[float]     = mapped_column(Float, nullable=False, default=0.0)
    mode:         Mapped[str]       = mapped_column(String(10), nullable=False)   # paper, live


# ─────────────────────────────────────────────────────────────
# Live-editable risk configuration (one active row at a time)
# ─────────────────────────────────────────────────────────────
class RiskConfig(Base):
    __tablename__ = "risk_config"

    id:                   Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    max_drawdown_pct:     Mapped[float]     = mapped_column(Float, nullable=False, default=10.0)
    max_open_trades:      Mapped[int]       = mapped_column(Integer, nullable=False, default=3)
    daily_loss_limit_pct: Mapped[float]     = mapped_column(Float, nullable=False, default=5.0)
    risk_per_trade_pct:   Mapped[float]     = mapped_column(Float, nullable=False, default=1.0)
    max_lot_size:         Mapped[float]     = mapped_column(Float, nullable=False, default=0.10)
    is_active:            Mapped[bool]      = mapped_column(Boolean, nullable=False, default=True)
    created_at:           Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:           Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─────────────────────────────────────────────────────────────
# Bot performance metrics (recalculated on every trade close)
# ─────────────────────────────────────────────────────────────
class BotMetric(Base):
    __tablename__ = "bot_metrics"

    id:               Mapped[uuid.UUID]    = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id:           Mapped[uuid.UUID]    = mapped_column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False)
    timestamp:        Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now())
    total_trades:     Mapped[int]          = mapped_column(Integer, nullable=False, default=0)
    win_rate:         Mapped[float | None] = mapped_column(Float, nullable=True)   # % of winning trades
    profit_factor:    Mapped[float | None] = mapped_column(Float, nullable=True)   # gross profit / gross loss
    sharpe_ratio:     Mapped[float | None] = mapped_column(Float, nullable=True)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    expectancy:       Mapped[float | None] = mapped_column(Float, nullable=True)   # avg profit per trade

    # Relationships
    bot: Mapped["Bot"] = relationship("Bot", back_populates="metrics")
