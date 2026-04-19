# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create SKUs API routes
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_user, get_db
from app.models import SKU, User, CulturalProduct, Video
from app.schemas.sku import SKUCreate, SKUUpdate, SKUResponse

router = APIRouter(prefix="/api/skus", tags=["SKU"])


@router.get("/", response_model=List[SKUResponse])
def list_skus(
    skip: int = 0,
    limit: int = 100,
    cultural_product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[SKU]:
    """List all SKUs."""
    query = db.query(SKU)
    if cultural_product_id:
        query = query.filter(SKU.cultural_product_id == cultural_product_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=SKUResponse, status_code=status.HTTP_201_CREATED)
def create_sku(
    sku_data: SKUCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SKU:
    """Create a new SKU."""
    # Check if code already exists
    existing = db.query(SKU).filter(SKU.code == sku_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该编号已被使用",
        )

    # Verify cultural product exists
    product = db.query(CulturalProduct).filter(
        CulturalProduct.id == sku_data.cultural_product_id
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文创品不存在",
        )

    # Verify video exists if provided
    if sku_data.default_video_id:
        video = db.query(Video).filter(Video.id == sku_data.default_video_id).first()
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="默认视频不存在",
            )

    sku = SKU(**sku_data.model_dump())
    db.add(sku)
    db.commit()
    db.refresh(sku)
    return sku


@router.get("/{sku_id}", response_model=SKUResponse)
def get_sku(
    sku_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SKU:
    """Get SKU by ID."""
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU不存在",
        )
    return sku


@router.put("/{sku_id}", response_model=SKUResponse)
def update_sku(
    sku_id: int,
    sku_data: SKUUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SKU:
    """Update a SKU."""
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU不存在",
        )

    update_data = sku_data.model_dump(exclude_unset=True)

    # Verify video exists if provided
    if sku_data.default_video_id:
        video = db.query(Video).filter(Video.id == sku_data.default_video_id).first()
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="默认视频不存在",
            )

    for key, value in update_data.items():
        setattr(sku, key, value)

    db.commit()
    db.refresh(sku)
    return sku


@router.delete("/{sku_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sku(
    sku_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a SKU (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除SKU",
        )

    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU不存在",
        )

    db.delete(sku)
    db.commit()
