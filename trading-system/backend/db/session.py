"""
Database engine and session factory.
Use get_db() as a FastAPI dependency to get a session in route handlers.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from backend.shared.config import settings

# Create the engine (sync — using psycopg2)
engine = create_engine(
    settings.database_url,
    echo=(settings.env == "development"),   # logs SQL in dev mode
    pool_pre_ping=True,                     # test connection before using from pool
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    Usage in a route:
        @app.get("/example")
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
