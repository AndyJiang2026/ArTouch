# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create SKUInstance Pydantic schemas
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P2

"""
Pydantic schemas for SKUInstance model.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SKUInstanceStatus(Enum):
    """SKU实例状态枚举。"""
    UNBOUND = "unbound"  # 未绑定
    BOUND = "bound"  # 已绑定
    ACTIVE = "active"  # 已激活


class SKUInstanceCreate(BaseModel):
    """创建SKU实例的请求模式。"""
    sku_template_id: int = Field(..., description="SKU模板ID")
    code: str = Field(..., max_length=3, description="实例编号，如'001'")
    name: str = Field(..., max_length=200, description="实例名称")
    nfc_tag_id: int | None = Field(None, description="关联的NFC标签ID（可选）")


class SKUInstanceUpdate(BaseModel):
    """更新SKU实例的请求模式。"""
    name: str | None = Field(None, max_length=200, description="实例名称")
    status: SKUInstanceStatus | None = Field(None, description="实例状态")


class SKUInstanceBindRequest(BaseModel):
    """绑定NFC标签的请求模式。"""
    nfc_tag_id: int = Field(..., description="NFC标签ID")


class SKUInstanceResponse(BaseModel):
    """SKU实例的响应模式。"""
    id: int
    sku_template_id: int
    code: str
    name: str
    nfc_tag_id: int | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SKUInstanceDetailResponse(BaseModel):
    """SKU实例的详细响应模式。"""
    id: int
    sku_template_id: int
    code: str
    name: str
    nfc_tag_id: int | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    # 关联信息
    sku_template_code: str | None = None
    sku_template_name: str | None = None
    cultural_product_id: int | None = None
    cultural_product_name: str | None = None

    model_config = {"from_attributes": True}
