# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create SKU Pydantic schemas
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class SKUCreate(BaseModel):
    """创建 SKU 单品请求。

    code: SKU独立编号，用于NFC URL编码，如"001"、"002"。
    name: SKU名称/关键词，如"白色"、"黑色"。
    cultural_product_id: 关联的文创产品ID。
    default_video_id: SKU默认关联视频（可选）。
    production_date: 生产日期（可选）。
    notes: 备注（可选）。
    """

    code: str = Field(..., min_length=1, max_length=3, description="SKU独立编号，用于URL编码")
    name: str = Field(..., min_length=1, max_length=200, description="SKU名称/关键词，如'白色'、'黑色'")
    cultural_product_id: int = Field(..., gt=0, description="关联的文创产品ID")
    default_video_id: int | None = Field(None, gt=0, description="SKU默认关联视频ID")
    production_date: date | None = Field(None, description="生产日期")
    notes: str | None = Field(None, max_length=2000, description="备注")

    @field_validator("code")
    @classmethod
    def code_format(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("编号不能为空")
        return v

    @field_validator("name")
    @classmethod
    def name_stripped(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("名称不能为空")
        return v


class SKUUpdate(BaseModel):
    """更新 SKU 单品请求。"""

    code: str | None = Field(None, min_length=1, max_length=3)
    name: str | None = Field(None, min_length=1, max_length=200)
    cultural_product_id: int | None = Field(None, gt=0)
    default_video_id: int | None = Field(None, gt=0)
    production_date: date | None = None
    notes: str | None = Field(None, max_length=2000)


class SKUMultiCreate(BaseModel):
    """批量创建 SKU（一个文创产品的多个关键词）。"""

    names: list[str] = Field(
        ..., min_length=1, description="SKU名称列表，如['白色','黑色']"
    )
    cultural_product_id: int = Field(..., gt=0, description="关联的文创产品ID")


class SKUListItem(BaseModel):
    """SKU 列表项（不含关联详情）。"""

    id: int
    code: str
    name: str
    cultural_product_id: int
    default_video_id: int | None = None
    production_date: date | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class SKUDetail(SKUListItem):
    """SKU 完整详情（含关联文创产品名称）。"""

    cultural_product_name: str | None = None

    class Config:
        from_attributes = True


class SKUBatchCreateResponse(BaseModel):
    """批量创建 SKU 的响应，包含成功创建的项目和错误信息。"""

    created: list[SKUListItem]
    errors: list[str]
    total_created: int
    total_errors: int
