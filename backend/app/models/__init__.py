# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create SQLAlchemy models for ArtTouch NFC system
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

from sqlalchemy.orm import DeclarativeBase  # noqa: F401

# Import engine and SessionLocal from database module (single source of truth)
from app.database import Base, SessionLocal, engine

# Re-export for convenience
__all__ = [
    "SKU",
    "Base",
    "CulturalProduct",
    "NFCTag",
    "SKUInstance",
    "SessionLocal",
    "TagClick",
    "User",
    "Video",
    "cultural_product_videos",
    "engine",
]


# Import all models after Base is defined
from app.models.cultural_product import CulturalProduct
from app.models.nfc_tag import NFCTag, TagClick
from app.models.sku import SKU
from app.models.sku_instance import SKUInstance
from app.models.user import User
from app.models.video import Video, cultural_product_videos
