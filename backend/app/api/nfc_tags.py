# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create NFC tags API routes
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_user, get_db
from app.models import NFCTag, User, CulturalProduct, Video, SKU
from app.schemas.nfc_tag import (
    NFCTagCreate,
    NFCTagUpdate,
    NFCTagResponse,
    NFCTagApproveResponse,
)

router = APIRouter(prefix="/api/nfc-tags", tags=["NFC标签"])


def generate_url_code(
    cultural_product_code: str,
    video_code: str,
    sku_code: Optional[str] = None,
) -> str:
    """Generate URL code in format 001_002_003."""
    if sku_code:
        return f"{cultural_product_code}_{video_code}_{sku_code}"
    return f"{cultural_product_code}_{video_code}"


@router.get("/", response_model=List[NFCTagResponse])
def list_nfc_tags(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    approval_status: Optional[str] = None,
    cultural_product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[NFCTag]:
    """List all NFC tags."""
    query = db.query(NFCTag)
    if status:
        query = query.filter(NFCTag.status == status)
    if approval_status:
        query = query.filter(NFCTag.approval_status == approval_status)
    if cultural_product_id:
        query = query.filter(NFCTag.cultural_product_id == cultural_product_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=NFCTagResponse, status_code=status.HTTP_201_CREATED)
def create_nfc_tag(
    tag_data: NFCTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NFCTag:
    """Create a new NFC tag (operator can create, pending approval)."""
    # Verify cultural product exists and get code
    product = db.query(CulturalProduct).filter(
        CulturalProduct.id == tag_data.cultural_product_id
    ).first()
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
    return tag


@router.get("/{tag_id}", response_model=NFCTagResponse)
def get_nfc_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NFCTag:
    """Get NFC tag by ID."""
    tag = db.query(NFCTag).filter(NFCTag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NFC标签不存在",
        )
    return tag


@router.put("/{tag_id}", response_model=NFCTagResponse)
def update_nfc_tag(
    tag_id: int,
    tag_data: NFCTagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NFCTag:
    """Update a NFC tag."""
    tag = db.query(NFCTag).filter(NFCTag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NFC标签不存在",
        )

    update_data = tag_data.model_dump(exclude_unset=True)

    # Verify video if changing
    if tag_data.video_id:
        video = db.query(Video).filter(Video.id == tag_data.video_id).first()
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="视频不存在",
            )

    for key, value in update_data.items():
        setattr(tag, key, value)

    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_nfc_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> None:
    """Delete a NFC tag (admin only)."""
    tag = db.query(NFCTag).filter(NFCTag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NFC标签不存在",
        )

    db.delete(tag)
    db.commit()


@router.post("/{tag_id}/approve", response_model=NFCTagApproveResponse)
def approve_nfc_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> NFCTag:
    """Approve a NFC tag (admin only)."""
    tag = db.query(NFCTag).filter(NFCTag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NFC标签不存在",
        )

    if tag.approval_status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该标签已审批通过",
        )

    tag.approval_status = "approved"
    tag.approved_by = current_user.id
    tag.approved_at = date.today()
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
    tag = db.query(NFCTag).filter(NFCTag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NFC标签不存在",
        )

    if tag.approval_status == "rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该标签已驳回",
        )

    tag.approval_status = "rejected"
    tag.approved_by = current_user.id
    tag.approved_at = date.today()
    db.commit()
    db.refresh(tag)

    return NFCTagApproveResponse(
        id=tag.id,
        url_code=tag.url_code,
        approval_status=tag.approval_status,
        approved_by=tag.approved_by,
        approved_at=tag.approved_at,
    )
