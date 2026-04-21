# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create Pydantic schemas for cultural product management
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

CODE_LENGTH = 3  # 文创产品编号固定长度


class CulturalProductCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=3, pattern=r"^\d{3}$")
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    status: str = "active"

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isdigit() or len(v) != CODE_LENGTH:
            raise ValueError("编号必须是3位数字")
        return v


class CulturalProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = None


class CulturalProductResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
