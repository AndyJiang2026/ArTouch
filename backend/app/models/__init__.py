# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create SQLAlchemy models for ArtTouch NFC system
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

from sqlalchemy.orm import DeclarativeBase

# Import engine and SessionLocal from database module (single source of truth)
from app.database import engine, SessionLocal

# Re-export for convenience
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


# Import all models after Base is defined
from app.models.user import User
from app.models.cultural_product import CulturalProduct
from app.models.video import Video, cultural_product_videos
from app.models.sku import SKU
from app.models.nfc_tag import NFCTag, TagClick
