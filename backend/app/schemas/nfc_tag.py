# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create NFCTag and NFCPlay Pydantic schemas
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class NFCTagStatus(Enum):
    """NFC tag status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class NFCTagApprovalStatus(Enum):
    """NFC tag approval status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class NFCTagCreate(BaseModel):
    cultural_product_id: int
    video_id: int
    sku_id: int | None = None
    expires_at: date | None = None
    auto_create_sku_instance: bool = Field(False, description="是否自动创建SKU实例并绑定")

    @field_validator("cultural_product_id", "video_id")
    @classmethod
    def validate_ids(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("ID必须为正整数")
        return v


class NFCTagUpdate(BaseModel):
    video_id: int | None = None
    sku_id: int | None = None
    status: str | None = None
    expires_at: date | None = None

    @field_validator("video_id")
    @classmethod
    def validate_video_id(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("视频ID必须为正整数")
        return v


class NFCTagResponse(BaseModel):
    id: int
    url_code: str
    cultural_product_id: int
    video_id: int
    sku_id: int | None
    sku_instance_id: int | None
    status: NFCTagStatus
    approval_status: NFCTagApprovalStatus
    created_by: int
    approved_by: int | None
    approved_at: date | None
    expires_at: date | None
    created_at: datetime

    class Config:
        from_attributes = True


class NFCTagApproveResponse(BaseModel):
    id: int
    url_code: str
    approval_status: NFCTagApprovalStatus
    approved_by: int
    approved_at: date


class NFCPlayResponse(BaseModel):
    video_url: str
    title: str
    cultural_product_name: str
    duration: float | None = None
