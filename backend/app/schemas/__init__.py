# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create Pydantic schemas package
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from app.schemas.cultural_product import (
    CulturalProductCreate,
    CulturalProductResponse,
    CulturalProductUpdate,
)
from app.schemas.dashboard import (
    DailyStats,
    DashboardStats,
    MonthlyStats,
    WeeklyStats,
)
from app.schemas.nfc_tag import (
    NFCPlayResponse,
    NFCTagApproveResponse,
    NFCTagCreate,
    NFCTagResponse,
    NFCTagUpdate,
)
from app.schemas.pagination import PaginatedResponse
from app.schemas.sku import (
    SKUCreate,
    SKUDetail,
    SKUListItem,
    SKUMultiCreate,
    SKUUpdate,
)
from app.schemas.sku_instance import (
    SKUInstanceBindRequest,
    SKUInstanceCreate,
    SKUInstanceDetailResponse,
    SKUInstanceResponse,
    SKUInstanceStatus,
    SKUInstanceUpdate,
)
from app.schemas.user import (
    LoginRequest,
    PasswordChangeRequest,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.schemas.video import (
    VideoCreate,
    VideoProcessResponse,
    VideoResponse,
    VideoUpdate,
)

__all__ = [
    "CulturalProductCreate",
    "CulturalProductResponse",
    "CulturalProductUpdate",
    "DailyStats",
    "DashboardStats",
    "LoginRequest",
    "MonthlyStats",
    "NFCPlayResponse",
    "NFCTagApproveResponse",
    "NFCTagCreate",
    "NFCTagResponse",
    "NFCTagUpdate",
    "PaginatedResponse",
    "PasswordChangeRequest",
    "SKUCreate",
    "SKUDetail",
    "SKUInstanceBindRequest",
    "SKUInstanceCreate",
    "SKUInstanceDetailResponse",
    "SKUInstanceResponse",
    "SKUInstanceStatus",
    "SKUInstanceUpdate",
    "SKUListItem",
    "SKUMultiCreate",
    "SKUUpdate",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "VideoCreate",
    "VideoProcessResponse",
    "VideoResponse",
    "VideoUpdate",
    "WeeklyStats",
]
