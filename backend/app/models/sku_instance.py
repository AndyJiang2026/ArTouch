# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create SKUInstance SQLAlchemy model
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P1

"""
SKUInstance Model - Physical item instances bound to NFC tags

This model represents specific physical instances of SKU templates that can be
bound to NFC tags for tracking and authentication purposes.

Lifecycle:
- unbound: New instance, not yet bound to any NFC tag
- bound: Bound to an NFC tag but tag not yet activated
- active: NFC tag is active and in use
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class SKUInstance(Base):
    """SKU实例模型 - 代表实际物理单品，绑定到NFC标签。

    业务说明：
    - SKUInstance是SKU模板的具体物理实例（如"大白兔-白色-001"）
    - 每个SKUInstance拥有独立的三位编号(code)，用于物理物品识别
    - SKUInstance通过nfc_tag_id关联到具体NFC标签
    - 状态流转：unbound -> bound -> active

    与SKU模板的关系：
    - sku_template_id 关联到 SKU (模板)
    - SKU模板的name字段是产品描述关键词（如"白色"）
    - SKUInstance的name是完整实例名称（如"大白兔-白色-001"）

    与NFC标签的关系：
    - nfc_tag_id 关联到 NFCTag (可选)
    - 绑定后可通过NFC标签识别物理物品
    """

    __tablename__ = "sku_instances"
    __table_args__ = (
        UniqueConstraint("sku_template_id", "code", name="uq_sku_instance_template_code"),
        UniqueConstraint("nfc_tag_id", name="uq_sku_instance_nfc_tag"),
    )

    id = Column(Integer, primary_key=True, index=True)
    sku_template_id = Column(
        Integer, ForeignKey("skus.id"), nullable=False, index=True
    )
    code = Column(String(3), nullable=False, index=True)  # 如"001"、"002"
    name = Column(String(200), nullable=False)  # 完整实例名称，如"大白兔-白色-001"
    nfc_tag_id = Column(
        Integer, ForeignKey("nfc_tags.id"), nullable=True, unique=True
    )
    status = Column(
        String(20), nullable=False, server_default="unbound"
    )  # unbound, bound, active
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    sku_template = relationship("SKU", back_populates="sku_instances")
    # 注意: nfc_tag通过外键 nfc_tag_id 关联, 不使用back_populates避免循环一对一问题
