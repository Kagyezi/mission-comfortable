"""
Shared constants used across all modules.
Never hardcode these strings elsewhere — always import from here.
"""

# --- Signal actions ---
ACTION_BUY  = "BUY"
ACTION_SELL = "SELL"
ACTION_HOLD = "HOLD"

# --- Decision statuses ---
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"
STATUS_RESIZED  = "RESIZED"

# --- Trade statuses ---
TRADE_OPEN      = "open"
TRADE_CLOSED    = "closed"
TRADE_CANCELLED = "cancelled"

# --- Close reasons ---
CLOSE_SL_HIT         = "sl_hit"
CLOSE_TP_HIT         = "tp_hit"
CLOSE_MANUAL         = "manual"
CLOSE_KILL_SWITCH    = "kill_switch"
CLOSE_SIGNAL_REVERSE = "signal_reversal"

# --- Execution modes ---
MODE_PAPER = "paper"
MODE_LIVE  = "live"

# --- Component names (for system logs) ---
COMPONENT_MDS      = "mds"
COMPONENT_BOT      = "bot"
COMPONENT_DECISION = "decision_engine"
COMPONENT_EXECUTION = "execution"
COMPONENT_API      = "api"

# --- Log levels ---
LOG_DEBUG    = "DEBUG"
LOG_INFO     = "INFO"
LOG_WARNING  = "WARNING"
LOG_ERROR    = "ERROR"
LOG_CRITICAL = "CRITICAL"

# --- Risk event types ---
RISK_DRAWDOWN_LIMIT   = "drawdown_limit"
RISK_DAILY_LOSS_LIMIT = "daily_loss_limit"
RISK_MAX_POSITIONS    = "max_positions"
RISK_PAIR_OPEN        = "pair_already_open"
RISK_SIGNAL_REJECTED  = "signal_rejected"
RISK_POSITION_RESIZED = "position_resized"
RISK_KILL_SWITCH      = "kill_switch"

# --- MT5 Timeframe constants ---
TIMEFRAMES = {
    "M1":  1,
    "M5":  5,
    "M15": 15,
    "M30": 30,
    "H1":  60,
    "H4":  240,
    "D1":  1440,
}

# --- Supported currency pairs ---
SUPPORTED_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY",
    "USDCHF", "AUDUSD", "USDCAD",
]
