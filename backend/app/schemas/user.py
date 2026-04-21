# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create User Pydantic schemas
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_upper and has_lower and has_digit):
            raise ValueError("密码必须包含大小写字母和数字")
        return v


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(default="operator")
    is_active: bool = True

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_upper and has_lower and has_digit):
            raise ValueError("密码必须包含大小写字母和数字")
        return v


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    role: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    is_first_login: bool
    login_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
