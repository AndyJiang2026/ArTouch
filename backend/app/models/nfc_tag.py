# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create NFCTag and TagClick SQLAlchemy models
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
    from app.models.sku import SKU
    from app.models.user import User


class NFCTag(Base):
    __tablename__ = "nfc_tags"

    id = Column(Integer, primary_key=True, index=True)
    url_code = Column(String(50), unique=True, nullable=False, index=True)  # 001_002_003
    cultural_product_id = Column(Integer, ForeignKey("cultural_products.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    sku_id = Column(Integer, ForeignKey("skus.id"), nullable=True)
    status = Column(String(20), default="active")  # active, inactive
    approval_status = Column(String(20), default="pending")  # pending, approved, rejected
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(Date, nullable=True)
    expires_at = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cultural_product = relationship("CulturalProduct", back_populates="nfc_tags")
    video = relationship("Video", back_populates="nfc_tags")
    sku = relationship("SKU", back_populates="nfc_tags")
    creator = relationship("User", back_populates="created_tags", foreign_keys=[created_by])
    approver = relationship("User", back_populates="approved_tags", foreign_keys=[approved_by])
    clicks = relationship("TagClick", back_populates="tag")


class TagClick(Base):
    __tablename__ = "tag_clicks"

    id = Column(Integer, primary_key=True, index=True)
    tag_id = Column(Integer, ForeignKey("nfc_tags.id"), nullable=False)
    visitor_id = Column(String(100), nullable=True)
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    referer = Column(String(500), nullable=True)
    clicked_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tag = relationship("NFCTag", back_populates="clicks")
