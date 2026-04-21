# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create SKU SQLAlchemy model
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class SKU(Base):
    """SKU单品模型 - 代表文创品的具体单品/库存单位。

    业务说明：
    - SKU是文创品的具体单品（如"白色-001"、"黑色-002"）
    - 每个SKU拥有独立的三位编号(code)，用于NFC URL编码
    - SKU的name字段是产品描述关键词（如"白色"、"黑色"）
    - NFC标签通过sku_id关联到具体SKU，实现触碰推送正确视频

    与产品库的关系：
    - 产品库创建文创品时录入SKU关键词（如"白色"、"黑色"）
    - NFC标签编辑时选择具体SKU单品建立关联
    - 手机触碰文创品具体单品时，系统根据sku_id推送对应视频
    """

    __tablename__ = "skus"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), unique=True, nullable=False, index=True)  # 如"001"、"002"，用于URL编码
    name = Column(String(200), nullable=False, index=True)  # SKU名称/关键词，如"白色"、"黑色"
    cultural_product_id = Column(
        Integer, ForeignKey("cultural_products.id"), nullable=False, index=True
    )
    default_video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)  # SKU默认关联视频
    production_date = Column(Date, nullable=True)  # 生产日期
    notes = Column(Text, nullable=True)  # 备注
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cultural_product = relationship("CulturalProduct", back_populates="skus")
    nfc_tags = relationship("NFCTag", back_populates="sku")  # 关联到使用此SKU的NFC标签
    sku_instances = relationship("SKUInstance", back_populates="sku_template")  # 关联到此SKU模板的所有实例
