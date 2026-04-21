# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create User SQLAlchemy model
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="operator")  # admin, operator
    is_active = Column(Boolean, default=True)
    is_first_login = Column(Boolean, default=True)
    login_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    created_tags = relationship("NFCTag", back_populates="creator", foreign_keys="NFCTag.created_by")
    approved_tags = relationship("NFCTag", back_populates="approver", foreign_keys="NFCTag.approved_by")
