# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create NFCTag and TagClick SQLAlchemy models
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    pass


class NFCTag(Base):
    __tablename__ = "nfc_tags"

    id = Column(Integer, primary_key=True, index=True)
    url_code = Column(String(50), unique=True, nullable=False, index=True)  # 001_002_003
    cultural_product_id = Column(Integer, ForeignKey("cultural_products.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    sku_id = Column(Integer, ForeignKey("skus.id"), nullable=True)  # 关联到具体SKU单品（非产品库描述关键词）
    sku_instance_id = Column(Integer, ForeignKey("sku_instances.id"), nullable=True, unique=True)  # 关联到具体SKU实例
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
    sku = relationship("SKU", back_populates="nfc_tags")  # 关联到具体SKU单品
    # 注意: sku_instance通过外键 sku_instance_id 关联, 不使用back_populates避免循环一对一问题
    creator = relationship("User", back_populates="created_tags", foreign_keys=[created_by])
    approver = relationship("User", back_populates="approved_tags", foreign_keys=[approved_by])
    clicks = relationship("TagClick", back_populates="tag", cascade="all, delete-orphan")


class TagClick(Base):
    __tablename__ = "tag_clicks"

    id = Column(Integer, primary_key=True, index=True)
    tag_id = Column(Integer, ForeignKey("nfc_tags.id", ondelete="CASCADE"), nullable=False)
    visitor_id = Column(String(100), nullable=True)
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    referer = Column(String(500), nullable=True)
    clicked_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tag = relationship("NFCTag", back_populates="clicks")
