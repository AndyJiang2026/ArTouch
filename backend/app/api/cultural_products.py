# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create cultural products API routes
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_operator_or_admin
from app.models import CulturalProduct, User
from app.schemas.cultural_product import (
    CulturalProductCreate,
    CulturalProductResponse,
    CulturalProductUpdate,
)
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/api/cultural-products", tags=["文创品"])


@router.get("/", response_model=PaginatedResponse[CulturalProductResponse])
def list_cultural_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict:
    """List all cultural products with pagination."""
    query = db.query(CulturalProduct)
    if status_filter:
        query = query.filter(CulturalProduct.status == status_filter)

    # Get total count
    total = query.count()

    # Get paginated items
    items = query.order_by(CulturalProduct.id.desc()).offset(skip).limit(limit).all()

    page = (skip // limit) + 1 if limit > 0 else 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": limit,
    }


@router.post("/", response_model=CulturalProductResponse, status_code=status.HTTP_201_CREATED)
def create_cultural_product(
    product_data: CulturalProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_or_admin),
) -> CulturalProduct:
    """Create a new cultural product (operator or admin only)."""
    # Check if code already exists
    existing = db.query(CulturalProduct).filter(CulturalProduct.code == product_data.code).first()
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
    _current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(require_operator_or_admin),
) -> CulturalProduct:
    """Update a cultural product (operator or admin only)."""
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
    _current_user: User = Depends(require_operator_or_admin),
) -> None:
    """Delete a cultural product (operator or admin only)."""
    product = db.query(CulturalProduct).filter(CulturalProduct.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文创品不存在",
        )

    db.delete(product)
    db.commit()
