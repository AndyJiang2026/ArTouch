# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create SQLAlchemy models for ArtTouch NFC system
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings

# Create engine with WAL mode for SQLite
connect_args = {"check_same_thread": False}
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    poolclass=StaticPool,
)


# Enable WAL mode for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# Import all models
from app.models.user import User
from app.models.cultural_product import CulturalProduct
from app.models.video import Video, cultural_product_videos
from app.models.sku import SKU
from app.models.nfc_tag import NFCTag, TagClick

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "User",
    "CulturalProduct",
    "Video",
    "SKU",
    "NFCTag",
    "TagClick",
    "cultural_product_videos",
]
