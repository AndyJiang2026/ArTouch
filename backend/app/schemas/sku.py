# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create SKU Pydantic schemas
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SKUCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=3, pattern=r"^\d{3}$")
    name: str = Field(..., min_length=1, max_length=200)
    cultural_product_id: int
    default_video_id: Optional[int] = None
    production_date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 3:
            raise ValueError("编号必须是3位数字")
        return v


class SKUUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    default_video_id: Optional[int] = None
    production_date: Optional[date] = None
    notes: Optional[str] = None


class SKUResponse(BaseModel):
    id: int
    code: str
    name: str
    cultural_product_id: int
    default_video_id: Optional[int]
    production_date: Optional[date]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
