# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create NFCTag and NFCPlay Pydantic schemas
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class NFCTagCreate(BaseModel):
    cultural_product_id: int
    video_id: int
    sku_id: Optional[int] = None
    expires_at: Optional[date] = None

    @field_validator("cultural_product_id", "video_id")
    @classmethod
    def validate_ids(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("ID必须为正整数")
        return v


class NFCTagUpdate(BaseModel):
    video_id: Optional[int] = None
    sku_id: Optional[int] = None
    status: Optional[str] = None
    expires_at: Optional[date] = None


class NFCTagResponse(BaseModel):
    id: int
    url_code: str
    cultural_product_id: int
    video_id: int
    sku_id: Optional[int]
    status: str
    approval_status: str
    created_by: int
    approved_by: Optional[int]
    approved_at: Optional[date]
    expires_at: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


class NFCTagApproveResponse(BaseModel):
    id: int
    url_code: str
    approval_status: str
    approved_by: int
    approved_at: date


class NFCPlayResponse(BaseModel):
    video_url: str
    title: str
    cultural_product_name: str
    duration: Optional[float] = None
