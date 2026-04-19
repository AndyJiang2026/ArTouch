# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create CulturalProduct Pydantic schemas
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CulturalProductCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=3, pattern=r"^\d{3}$")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = "active"

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 3:
            raise ValueError("编号必须是3位数字")
        return v


class CulturalProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None


class CulturalProductResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
