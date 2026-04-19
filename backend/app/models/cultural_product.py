# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create CulturalProduct SQLAlchemy model
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.video import Video
    from app.models.sku import SKU
    from app.models.nfc_tag import NFCTag


class CulturalProduct(Base):
    __tablename__ = "cultural_products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), unique=True, nullable=False, index=True)  # 001, 002, etc.
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)  # Rich text
    status = Column(String(20), default="active")  # active, inactive
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    videos = relationship(
        "Video",
        secondary="cultural_product_videos",
        back_populates="cultural_products",
    )
    skus = relationship("SKU", back_populates="cultural_product")
    nfc_tags = relationship("NFCTag", back_populates="cultural_product")
