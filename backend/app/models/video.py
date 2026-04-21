# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create Video SQLAlchemy model with many-to-many to CulturalProduct
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    pass


# Many-to-many relationship table
cultural_product_videos = Table(
    "cultural_product_videos",
    Base.metadata,
    Column("cultural_product_id", Integer, ForeignKey("cultural_products.id"), primary_key=True),
    Column("video_id", Integer, ForeignKey("videos.id"), primary_key=True),
)


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), unique=True, nullable=False, index=True)  # 001, 002, etc.
    name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=True)
    cover_image = Column(String(500), nullable=True)  # /covers/xxx.jpg, auto-extracted from first frame
    duration = Column(Float, nullable=True)  # seconds
    file_size = Column(Integer, nullable=True)  # bytes
    status = Column(String(20), default="active")  # active, inactive, processing
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cultural_products = relationship(
        "CulturalProduct",
        secondary=cultural_product_videos,
        back_populates="videos",
    )
    nfc_tags = relationship("NFCTag", back_populates="video")
