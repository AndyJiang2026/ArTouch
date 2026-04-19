# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create Pydantic schemas package
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    LoginRequest,
    PasswordChangeRequest,
)
from app.schemas.cultural_product import (
    CulturalProductCreate,
    CulturalProductUpdate,
    CulturalProductResponse,
)
from app.schemas.video import (
    VideoCreate,
    VideoUpdate,
    VideoResponse,
    VideoProcessResponse,
)
from app.schemas.sku import (
    SKUCreate,
    SKUUpdate,
    SKUResponse,
)
from app.schemas.nfc_tag import (
    NFCTagCreate,
    NFCTagUpdate,
    NFCTagResponse,
    NFCTagApproveResponse,
    NFCPlayResponse,
)
from app.schemas.dashboard import (
    DashboardStats,
    DailyStats,
    WeeklyStats,
    MonthlyStats,
)

__all__ = [
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "LoginRequest",
    "PasswordChangeRequest",
    "CulturalProductCreate",
    "CulturalProductUpdate",
    "CulturalProductResponse",
    "VideoCreate",
    "VideoUpdate",
    "VideoResponse",
    "VideoProcessResponse",
    "SKUCreate",
    "SKUUpdate",
    "SKUResponse",
    "NFCTagCreate",
    "NFCTagUpdate",
    "NFCTagResponse",
    "NFCTagApproveResponse",
    "NFCPlayResponse",
    "DashboardStats",
    "DailyStats",
    "WeeklyStats",
    "MonthlyStats",
]
