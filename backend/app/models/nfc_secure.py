# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create NfcTagSecure and VerificationLog SQLAlchemy models for NFC anti-counterfeiting
# DATE: 2026-04-22
# ENGINEER: AI Assistant
# RISK-LEVEL: P1

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    pass


class NfcTagSecure(Base):
    """
    NFC tag cryptographic security data.
    Stores anti-counterfeiting verification material for each physical NTAG 216 tag.

    The actual NFC tag (NTAG 216) stores:
    - NDEF URL Record (pages 4-17, publicly readable)
    - Protected pages (pages 18-20, password-protected or locked):
        - Key material (32B): HMAC-SHA256 derived from master_key + uid
        - Signature (32B): HMAC-SHA256(key_material, uid || ctr)
        - Counter (4B): incremented on each verification

    This model mirrors the protected data server-side for verification.
    """
    __tablename__ = "nfc_tags_secure"

    id = Column(Integer, primary_key=True, index=True)
    # Physical NFC tag UID (7 bytes / 14 hex chars, e.g. "041234567890AB")
    uid = Column(String(16), unique=True, nullable=False, index=True)
    # Reference to existing NFCTag record (url_code management)
    nfc_tag_id = Column(Integer, ForeignKey("nfc_tags.id"), nullable=True)
    # Server-side derived key material (hex string, 64 chars = 32 bytes)
    key_material = Column(Text, nullable=False)
    # Signature (hex string, 64 chars = 32 bytes)
    signature = Column(Text, nullable=False)
    # Verification counter (starts at 1)
    counter = Column(Integer, nullable=False, default=1)
    # Master key identifier (for multi-key rotation support)
    master_key_id = Column(String(50), nullable=True)
    # Product/instance info (optional, for quick lookup)
    product_name = Column(String(200), nullable=True)
    # Timestamps
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_verified_at = Column(DateTime, nullable=True)
    # Metadata
    is_active = Column(Integer, default=1)  # 1=active, 0=revoked
    note = Column(Text, nullable=True)

    # Relationships
    nfc_tag = relationship("NFCTag", foreign_keys=[nfc_tag_id])
    verification_logs = relationship("VerificationLog", back_populates="tag_secure")

    def __repr__(self) -> str:
        return f"<NfcTagSecure uid={self.uid} ctr={self.counter}>"


class VerificationLog(Base):
    """
    Log of all NFC tag verification attempts.
    Used for analytics, fraud detection, and audit trail.
    """
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    # Reference to NfcTagSecure
    tag_secure_id = Column(Integer, ForeignKey("nfc_tags_secure.id"), nullable=False, index=True)
    # NFC tag UID (denormalized for quick log scanning)
    uid = Column(String(16), nullable=False, index=True)
    # Verification result
    result = Column(String(20), nullable=False)  # ok, signature_invalid, counter_replay, tag_not_found, error
    # Details
    detail = Column(Text, nullable=True)
    # Client info
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    # Signature submitted by client (hex, for debugging)
    submitted_signature = Column(Text, nullable=True)
    # Counter submitted by client
    submitted_counter = Column(Integer, nullable=True)
    # Whether verification was successful
    is_success = Column(Integer, default=0)  # 0=failed, 1=success
    # Timestamp
    verified_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    tag_secure = relationship("NfcTagSecure", back_populates="verification_logs")

    def __repr__(self) -> str:
        return f"<VerificationLog uid={self.uid} result={self.result}>"
