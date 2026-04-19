# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create Video Pydantic schemas
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class VideoCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=3, pattern=r"^\d{3}$")
    name: str = Field(..., min_length=1, max_length=200)
    status: str = "active"

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 3:
            raise ValueError("编号必须是3位数字")
        return v


class VideoUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[str] = None
    cultural_product_ids: Optional[list[int]] = None


class VideoResponse(BaseModel):
    id: int
    code: str
    name: str
    file_path: Optional[str]
    duration: Optional[float]
    file_size: Optional[int]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class VideoProcessResponse(BaseModel):
    duration: float
    file_size: int
    resolution: Optional[str] = None
    message: str
