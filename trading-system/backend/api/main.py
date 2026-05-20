"""
FastAPI application entry point.
Run with: uvicorn backend.api.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from backend.db.session import engine
from backend.db.schemas import HealthResponse

app = FastAPI(
    title="Trading System API",
    description="Backend for the algorithmic trading dashboard",
    version="0.1.0",
    docs_url="/docs",       # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",
)

# Allow the React dev server (Vite runs on port 5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route stubs (implemented in later phases) ──────────────────
# from backend.api.routes import portfolio, trades, signals, bots, risk, system
# app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
# app.include_router(trades.router,    prefix="/trades",    tags=["Trades"])
# app.include_router(signals.router,   prefix="/signals",   tags=["Signals"])
# app.include_router(bots.router,      prefix="/bots",      tags=["Bots"])
# app.include_router(risk.router,      prefix="/risk",      tags=["Risk"])
# app.include_router(system.router,    prefix="/system",    tags=["System"])


# ── Phase 1 endpoints ─────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {"message": "Trading System API is running", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Returns the status of the API and its database connection.
    The frontend calls this on the Dashboard page to show system health.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="ok",
        database=db_status,
        version="0.1.0",
    )
