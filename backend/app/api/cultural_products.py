# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create cultural products API routes
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_user, get_db
from app.models import CulturalProduct, User
from app.schemas.cultural_product import (
    CulturalProductCreate,
    CulturalProductUpdate,
    CulturalProductResponse,
)

router = APIRouter(prefix="/api/cultural-products", tags=["文创品"])


@router.get("/", response_model=List[CulturalProductResponse])
def list_cultural_products(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CulturalProduct]:
    """List all cultural products."""
    query = db.query(CulturalProduct)
    if status:
        query = query.filter(CulturalProduct.status == status)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=CulturalProductResponse, status_code=status.HTTP_201_CREATED)
def create_cultural_product(
    product_data: CulturalProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CulturalProduct:
    """Create a new cultural product (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建文创品",
        )

    # Check if code already exists
    existing = db.query(CulturalProduct).filter(
        CulturalProduct.code == product_data.code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该编号已被使用",
        )

    product = CulturalProduct(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=CulturalProductResponse)
def get_cultural_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CulturalProduct:
    """Get cultural product by ID."""
    product = db.query(CulturalProduct).filter(CulturalProduct.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文创品不存在",
        )
    return product


@router.put("/{product_id}", response_model=CulturalProductResponse)
def update_cultural_product(
    product_id: int,
    product_data: CulturalProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CulturalProduct:
    """Update a cultural product."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新文创品",
        )

    product = db.query(CulturalProduct).filter(CulturalProduct.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文创品不存在",
        )

    update_data = product_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cultural_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a cultural product (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除文创品",
        )

    product = db.query(CulturalProduct).filter(CulturalProduct.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文创品不存在",
        )

    db.delete(product)
    db.commit()
