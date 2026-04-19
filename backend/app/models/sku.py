# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create SKU SQLAlchemy model
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.cultural_product import CulturalProduct
    from app.models.video import Video
    from app.models.nfc_tag import NFCTag


class SKU(Base):
    __tablename__ = "skus"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), unique=True, nullable=False, index=True)  # 001, 002, etc.
    name = Column(String(200), nullable=False)
    cultural_product_id = Column(Integer, ForeignKey("cultural_products.id"), nullable=False)
    default_video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    production_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cultural_product = relationship("CulturalProduct", back_populates="skus")
    default_video = relationship("Video", back_populates="default_for_skus")
    nfc_tags = relationship("NFCTag", back_populates="sku")
