# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create NFC tags API routes
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_admin_user, get_current_user, get_db, require_operator_or_admin
from app.models import SKU, CulturalProduct, NFCTag, SKUInstance, User, Video
from app.schemas.nfc_tag import (
    NFCTagApproveResponse,
    NFCTagCreate,
    NFCTagResponse,
    NFCTagUpdate,
)
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/api/nfc-tags", tags=["NFC标签"])


def generate_url_code(
    cultural_product_code: str,
    video_code: str,
    sku_code: str | None = None,
) -> str:
    """Generate URL code in format 001_002_003."""
    if sku_code:
        return f"{cultural_product_code}_{video_code}_{sku_code}"
    return f"{cultural_product_code}_{video_code}"


def get_nfc_tag_or_404(db: Session, tag_id: int) -> "NFCTag":
    """Get NFC tag by ID or raise 404."""
    tag = db.query(NFCTag).filter(NFCTag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NFC标签不存在",
        )
    return tag


@router.get("/", response_model=PaginatedResponse[NFCTagResponse])
def list_nfc_tags(
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    approval_status: str | None = None,
    cultural_product_id: int | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> PaginatedResponse[NFCTagResponse]:
    """List all NFC tags with pagination."""
    query = db.query(NFCTag)
    if status:
        query = query.filter(NFCTag.status == status)
    if approval_status:
        query = query.filter(NFCTag.approval_status == approval_status)
    if cultural_product_id:
        query = query.filter(NFCTag.cultural_product_id == cultural_product_id)

    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return PaginatedResponse(
        items=items,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.post("/", response_model=NFCTagResponse, status_code=status.HTTP_201_CREATED)
def create_nfc_tag(
    tag_data: NFCTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_or_admin),
) -> NFCTag:
    """Create a new NFC tag (operator can create, pending approval)."""
    # Verify cultural product exists and get code
    product = db.query(CulturalProduct).filter(CulturalProduct.id == tag_data.cultural_product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文创品不存在",
        )

    # Verify video exists and get code
    video = db.query(Video).filter(Video.id == tag_data.video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在",
        )

    # Get SKU code if provided
    sku_code = None
    if tag_data.sku_id:
        sku = db.query(SKU).filter(SKU.id == tag_data.sku_id).first()
        if not sku:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SKU不存在",
            )
        sku_code = sku.code

    # Generate URL code
    url_code = generate_url_code(product.code, video.code, sku_code)

    # Check if URL code already exists
    existing = db.query(NFCTag).filter(NFCTag.url_code == url_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该URL码已存在",
        )

    tag = NFCTag(
        url_code=url_code,
        cultural_product_id=tag_data.cultural_product_id,
        video_id=tag_data.video_id,
        sku_id=tag_data.sku_id,
        status="active",
        approval_status="pending",
        created_by=current_user.id,
        expires_at=tag_data.expires_at,
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)

    # Auto-create SKU instance if requested
    if tag_data.auto_create_sku_instance and tag_data.sku_id:
        # Find next available code for this SKU template
        max_code_row = db.query(SKUInstance.code).filter(
            SKUInstance.sku_template_id == tag_data.sku_id
        ).order_by(SKUInstance.code.desc()).first()
        if max_code_row:
            next_code = str(int(max_code_row[0]) + 1).zfill(3)
        else:
            next_code = "001"

        # Get SKU template and cultural product for name generation (with eager loading)
        sku_template = db.query(SKU).options(
            joinedload(SKU.cultural_product)
        ).filter(SKU.id == tag_data.sku_id).first()
        if not sku_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SKU不存在",
            )
        instance_name = f"{sku_template.cultural_product.name}-{sku_template.name}-{next_code}"

        # Create SKU instance
        sku_instance = SKUInstance(
            sku_template_id=tag_data.sku_id,
            code=next_code,
            name=instance_name,
            nfc_tag_id=tag.id,
            status="bound",
        )
        db.add(sku_instance)
        db.commit()
        db.refresh(sku_instance)
        # Update NFC tag's sku_instance_id for bidirectional binding
        tag.sku_instance_id = sku_instance.id
        db.add(tag)
        db.commit()
        db.refresh(tag)

    return tag


@router.get("/{tag_id}", response_model=NFCTagResponse)
def get_nfc_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> NFCTag:
    """Get NFC tag by ID."""
    return get_nfc_tag_or_404(db, tag_id)


@router.put("/{tag_id}", response_model=NFCTagResponse)
def update_nfc_tag(
    tag_id: int,
    tag_data: NFCTagUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_operator_or_admin),
) -> NFCTag:
    """Update a NFC tag."""
    tag = get_nfc_tag_or_404(db, tag_id)

    update_data = tag_data.model_dump(exclude_unset=True)

    # Regenerate URL if video or SKU changed
    new_video_id = tag_data.video_id if tag_data.video_id else tag.video_id
    new_sku_id = tag_data.sku_id  # Can be None to clear SKU

    if tag_data.video_id or tag_data.sku_id is not None:
        # Verify video if changing
        video = db.query(Video).filter(Video.id == new_video_id).first()
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="视频不存在",
            )

        # Get product for URL generation
        product = db.query(CulturalProduct).filter(CulturalProduct.id == tag.cultural_product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文创品不存在",
            )

        # Get SKU code if SKU set
        sku_code = None
        if new_sku_id:
            sku = db.query(SKU).filter(SKU.id == new_sku_id).first()
            if not sku:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="SKU不存在",
                )
            sku_code = sku.code
        elif tag.sku_id:
            # Keep existing SKU if not changing
            existing_sku = db.query(SKU).filter(SKU.id == tag.sku_id).first()
            if existing_sku:
                sku_code = existing_sku.code

        # Generate new URL code
        new_url_code = generate_url_code(product.code, video.code, sku_code)

        # Check if new URL code conflicts with existing tag
        existing = db.query(NFCTag).filter(
            NFCTag.url_code == new_url_code,
            NFCTag.id != tag_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该URL码已存在",
            )

        update_data["url_code"] = new_url_code

    for key, value in update_data.items():
        setattr(tag, key, value)

    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_nfc_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> None:
    """Delete a NFC tag (admin only)."""
    tag = get_nfc_tag_or_404(db, tag_id)

    db.delete(tag)
    db.commit()


@router.post("/{tag_id}/approve", response_model=NFCTagApproveResponse)
def approve_nfc_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> NFCTag:
    """Approve a NFC tag (admin only)."""
    tag = get_nfc_tag_or_404(db, tag_id)

    if tag.approval_status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该标签已审批通过",
        )

    tag.approval_status = "approved"
    tag.approved_by = current_user.id
    tag.approved_at = datetime.utcnow().date()
    db.commit()
    db.refresh(tag)

    return NFCTagApproveResponse(
        id=tag.id,
        url_code=tag.url_code,
        approval_status=tag.approval_status,
        approved_by=tag.approved_by,
        approved_at=tag.approved_at,
    )


@router.post("/{tag_id}/reject", response_model=NFCTagApproveResponse)
def reject_nfc_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> NFCTag:
    """Reject a NFC tag (admin only)."""
    tag = get_nfc_tag_or_404(db, tag_id)

    if tag.approval_status == "rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该标签已驳回",
        )

    tag.approval_status = "rejected"
    tag.approved_by = current_user.id
    tag.approved_at = datetime.utcnow().date()
    db.commit()
    db.refresh(tag)

    return NFCTagApproveResponse(
        id=tag.id,
        url_code=tag.url_code,
        approval_status=tag.approval_status,
        approved_by=tag.approved_by,
        approved_at=tag.approved_at,
    )
