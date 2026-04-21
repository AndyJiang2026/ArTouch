# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Update database module to support both SQLite and PostgreSQL
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from app.config import settings

# =============================================================================
# Engine Creation
# =============================================================================

_is_sqlite = settings.DATABASE_URL.startswith("sqlite:")
_is_postgres = settings.DATABASE_URL.startswith("postgresql:")

if _is_sqlite:
    # SQLite: use StaticPool for in-memory or single connection, WAL mode
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        poolclass=StaticPool,
    )
elif _is_postgres:
    # PostgreSQL: use NullPool for connection pooling (Uvicorn/async compatibility)
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )
else:
    # Other databases (MySQL, etc.)
    engine = create_engine(settings.DATABASE_URL)


# =============================================================================
# SQLite-specific: Enable WAL mode
# =============================================================================

@event.listens_for(engine, "connect")
def configure_connection(dbapi_connection, _connection_record):
    """Apply database-specific connection configuration."""
    if _is_sqlite:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

__all__ = ["Base", "SessionLocal", "engine"]
