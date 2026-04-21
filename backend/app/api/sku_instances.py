# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create SKUInstances API routes
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P1

"""SKUInstances API routes for managing physical SKU instances bound to NFC tags."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_user, get_db
from app.models import SKU, NFCTag, SKUInstance, User
from app.schemas.sku_instance import (
    SKUInstanceBindRequest,
    SKUInstanceCreate,
    SKUInstanceDetailResponse,
    SKUInstanceResponse,
    SKUInstanceStatus,
    SKUInstanceUpdate,
)

router = APIRouter(prefix="/api/sku-instances", tags=["SKU实例管理"])


def get_sku_instance_or_404(db: Session, instance_id: int) -> "SKUInstance":
    """Get SKU instance by ID or raise 404."""
    instance = db.query(SKUInstance).filter(SKUInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU实例不存在",
        )
    return instance


@router.get("/", response_model=list[SKUInstanceResponse])
def list_sku_instances(
    skip: int = 0,
    limit: int = 100,
    sku_template_id: int | None = None,
    status_filter: SKUInstanceStatus | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[SKUInstance]:
    """列出所有 SKU 实例。

    - 若传入 sku_template_id，仅返回该SKU模板下的实例。
    - 若传入 status_filter，按状态过滤。
    """
    query = db.query(SKUInstance)
    if sku_template_id:
        query = query.filter(SKUInstance.sku_template_id == sku_template_id)
    if status_filter:
        query = query.filter(SKUInstance.status == status_filter.value)
    return query.order_by(SKUInstance.id.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=SKUInstanceResponse, status_code=status.HTTP_201_CREATED)
def create_sku_instance(
    instance_data: SKUInstanceCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SKUInstance:
    """创建 SKU 实例。

    SKU实例代表物理单品，可选绑定到NFC标签。
    """
    # Verify SKU template exists
    sku_template = db.query(SKU).filter(SKU.id == instance_data.sku_template_id).first()
    if not sku_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU模板不存在",
        )

    # Check duplicate code for the same SKU template
    existing = db.query(SKUInstance).filter(
        SKUInstance.sku_template_id == instance_data.sku_template_id,
        SKUInstance.code == instance_data.code,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"编号「{instance_data.code}」已存在",
        )

    # Check duplicate name
    existing_name = db.query(SKUInstance).filter(
        SKUInstance.name == instance_data.name,
    ).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"名称「{instance_data.name}」已存在",
        )

    # Verify NFC tag if provided
    if instance_data.nfc_tag_id:
        nfc_tag = db.query(NFCTag).filter(NFCTag.id == instance_data.nfc_tag_id).first()
        if not nfc_tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NFC标签不存在",
            )
        # Check if NFC tag is already bound to another instance
        if nfc_tag.sku_instance_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该NFC标签已绑定到其他实例",
            )

    instance = SKUInstance(**instance_data.model_dump())
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


@router.get("/{instance_id}", response_model=SKUInstanceDetailResponse)
def get_sku_instance(
    instance_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SKUInstance:
    """获取 SKU 实例详情。"""
    instance = get_sku_instance_or_404(db, instance_id)

    # Build detailed response
    response = SKUInstanceDetailResponse(
        id=instance.id,
        sku_template_id=instance.sku_template_id,
        code=instance.code,
        name=instance.name,
        nfc_tag_id=instance.nfc_tag_id,
        status=SKUInstanceStatus(instance.status),
        created_at=instance.created_at,
        updated_at=instance.updated_at,
        sku_template_name=instance.sku_template.name if instance.sku_template else None,
        sku_template_code=instance.sku_template.code if instance.sku_template else None,
        nfc_tag_url_code=instance.nfc_tag.url_code if instance.nfc_tag else None,
    )
    return response


@router.put("/{instance_id}", response_model=SKUInstanceResponse)
def update_sku_instance(
    instance_id: int,
    instance_data: SKUInstanceUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SKUInstance:
    """更新 SKU 实例。"""
    instance = get_sku_instance_or_404(db, instance_id)

    update_data = instance_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有需要更新的字段",
        )

    # Check duplicate name if being changed
    if "name" in update_data:
        new_name = update_data["name"].strip()
        existing = db.query(SKUInstance).filter(
            SKUInstance.name == new_name,
            SKUInstance.id != instance_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"名称「{new_name}」已存在",
            )

    # Check NFC tag binding
    if "nfc_tag_id" in update_data:
        new_nfc_tag_id = update_data["nfc_tag_id"]
        if new_nfc_tag_id:
            nfc_tag = db.query(NFCTag).filter(NFCTag.id == new_nfc_tag_id).first()
            if not nfc_tag:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="NFC标签不存在",
                )
            # Check if NFC tag is already bound to another instance
            if nfc_tag.sku_instance_id and nfc_tag.sku_instance_id != instance_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该NFC标签已绑定到其他实例",
                )

    for key, value in update_data.items():
        setattr(instance, key, value)

    db.commit()
    db.refresh(instance)
    return instance


@router.delete("/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sku_instance(
    instance_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> None:
    """删除 SKU 实例（admin权限）。"""
    instance = get_sku_instance_or_404(db, instance_id)

    # Check if bound to active NFC tag
    if instance.nfc_tag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该实例已绑定NFC标签，请先解绑",
        )

    db.delete(instance)
    db.commit()


@router.post("/{instance_id}/bind", response_model=SKUInstanceResponse)
def bind_nfc_tag(
    instance_id: int,
    bind_data: SKUInstanceBindRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SKUInstance:
    """绑定 NFC 标签到 SKU 实例。

    将NFC标签与SKU实例关联，并更新状态为bound。
    """
    instance = get_sku_instance_or_404(db, instance_id)

    # Check if already bound
    if instance.nfc_tag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该实例已绑定NFC标签",
        )

    # Get NFC tag
    nfc_tag = db.query(NFCTag).filter(NFCTag.id == bind_data.nfc_tag_id).first()
    if not nfc_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NFC标签不存在",
        )

    # Check if NFC tag is already bound to another instance
    if nfc_tag.sku_instance_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该NFC标签已绑定到其他实例",
        )

    # Bind NFC tag to instance
    instance.nfc_tag_id = bind_data.nfc_tag_id
    instance.status = SKUInstanceStatus.BOUND.value
    # Also update the NFC tag's sku_instance_id for bidirectional binding
    nfc_tag.sku_instance_id = instance.id
    db.commit()
    db.refresh(instance)
    return instance


@router.post("/{instance_id}/unbind", response_model=SKUInstanceResponse)
def unbind_nfc_tag(
    instance_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SKUInstance:
    """解除 NFC 标签绑定。

    将NFC标签与SKU实例解除关联，并更新状态为unbound。
    """
    instance = get_sku_instance_or_404(db, instance_id)

    # Check if not bound
    if not instance.nfc_tag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该实例未绑定NFC标签",
        )

    # Unbind NFC tag
    nfc_tag = db.query(NFCTag).filter(NFCTag.id == instance.nfc_tag_id).first()
    instance.nfc_tag_id = None
    instance.status = SKUInstanceStatus.UNBOUND.value
    # Also clear the NFC tag's sku_instance_id for bidirectional binding
    if nfc_tag:
        nfc_tag.sku_instance_id = None
    db.commit()
    db.refresh(instance)
    return instance


@router.post("/{instance_id}/activate", response_model=SKUInstanceResponse)
def activate_sku_instance(
    instance_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SKUInstance:
    """激活 SKU 实例。

    将状态从bound更新为active，表示NFC标签已激活使用。
    """
    instance = get_sku_instance_or_404(db, instance_id)

    if instance.status != SKUInstanceStatus.BOUND.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="实例状态必须是bound才能激活",
        )

    if not instance.nfc_tag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="实例未绑定NFC标签",
        )

    instance.status = SKUInstanceStatus.ACTIVE.value
    db.commit()
    db.refresh(instance)
    return instance
