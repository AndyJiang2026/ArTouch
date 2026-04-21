# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Rewrite SKUs API for SKU单品 model
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_user, get_db
from app.models import SKU, CulturalProduct, User
from app.schemas.pagination import PaginatedResponse
from app.schemas.sku import (
    SKUBatchCreateResponse,
    SKUCreate,
    SKUDetail,
    SKUListItem,
    SKUMultiCreate,
    SKUUpdate,
)

router = APIRouter(prefix="/api/skus", tags=["SKU管理"])


@router.get("/", response_model=PaginatedResponse[SKUListItem])
def list_skus(
    skip: int = 0,
    limit: int = 100,
    cultural_product_id: int | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> PaginatedResponse[SKUListItem]:
    """列出所有 SKU 单品（分页）。"""
    query = db.query(SKU)
    if cultural_product_id:
        query = query.filter(SKU.cultural_product_id == cultural_product_id)
    total = query.count()
    items = query.order_by(SKU.id.desc()).offset(skip).limit(limit).all()
    return PaginatedResponse(
        items=items,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.post("/", response_model=SKUListItem, status_code=status.HTTP_201_CREATED)
def create_sku(
    sku_data: SKUCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SKU:
    """创建单个 SKU 单品。"""
    # Verify cultural product exists
    product = db.query(CulturalProduct).filter(
        CulturalProduct.id == sku_data.cultural_product_id
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文创产品不存在",
        )

    # Check duplicate name for the same product
    existing = db.query(SKU).filter(
        SKU.name == sku_data.name,
        SKU.cultural_product_id == sku_data.cultural_product_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"名称「{sku_data.name}」已存在",
        )

    # Check duplicate code (code is globally unique)
    existing_code = db.query(SKU).filter(SKU.code == sku_data.code).first()
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"编号「{sku_data.code}」已被使用",
        )

    sku = SKU(**sku_data.model_dump())
    db.add(sku)
    db.commit()
    db.refresh(sku)
    return sku


@router.post("/batch", response_model=SKUBatchCreateResponse, status_code=status.HTTP_201_CREATED)
def create_skus_batch(
    batch_data: SKUMultiCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SKUBatchCreateResponse:
    """批量创建 SKU 单品（一次为文创产品添加多个SKU）。

    系统会自动为每个SKU分配下一个可用的编号(code)。
    示例请求: {"names": ["白色", "黑色"], "cultural_product_id": 1}

    返回包含:
    - created: 成功创建的SKU列表
    - errors: 错误信息列表（如有）
    - total_created: 成功创建的数量
    - total_errors: 错误数量
    """
    product = db.query(CulturalProduct).filter(
        CulturalProduct.id == batch_data.cultural_product_id
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文创产品不存在",
        )

    # Find the max existing code to auto-generate sequential codes
    max_code_row = db.query(SKU.code).order_by(SKU.code.desc()).first()
    if max_code_row:
        last_code = int(max_code_row[0])
    else:
        last_code = 0

    created = []
    errors = []
    for name in batch_data.names:
        name_stripped = name.strip()
        if not name_stripped:
            errors.append("名称为空，已跳过")
            continue
        existing = db.query(SKU).filter(
            SKU.name == name_stripped,
            SKU.cultural_product_id == batch_data.cultural_product_id,
        ).first()
        if existing:
            errors.append(f"「{name_stripped}」已存在，跳过")
            continue
        last_code += 1
        new_code = str(last_code).zfill(3)  # Pad with zeros to 3 digits
        sku = SKU(
            code=new_code,
            name=name_stripped,
            cultural_product_id=batch_data.cultural_product_id,
        )
        db.add(sku)
        created.append(sku)

    db.commit()
    for sku in created:
        db.refresh(sku)

    return SKUBatchCreateResponse(
        created=[SKUDetail.model_validate(s) for s in created],
        errors=errors,
        total_created=len(created),
        total_errors=len(errors),
    )


@router.get("/by-product/{cultural_product_id}", response_model=list[SKUListItem])
def get_skus_by_product(
    cultural_product_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[SKU]:
    """获取指定文创产品的所有 SKU 单品。"""
    product = db.query(CulturalProduct).filter(
        CulturalProduct.id == cultural_product_id
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文创产品不存在",
        )
    return db.query(SKU).filter(SKU.cultural_product_id == cultural_product_id).all()


@router.get("/{sku_id}", response_model=SKUDetail)
def get_sku(
    sku_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SKU:
    """根据ID获取 SKU 详情。"""
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU不存在",
        )
    # Eager-load cultural product name
    result = SKUDetail.model_validate(sku)
    if sku.cultural_product:
        result.cultural_product_name = sku.cultural_product.name
    return result


@router.put("/{sku_id}", response_model=SKUListItem)
def update_sku(
    sku_id: int,
    sku_data: SKUUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SKU:
    """更新 SKU 单品。"""
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU不存在",
        )

    update_data = sku_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有需要更新的字段",
        )

    # Check duplicate if name is being changed
    if "name" in update_data:
        new_name = update_data["name"].strip()
        cid = update_data.get("cultural_product_id", sku.cultural_product_id)
        existing = db.query(SKU).filter(
            SKU.name == new_name,
            SKU.cultural_product_id == cid,
            SKU.id != sku_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"名称「{new_name}」已存在",
            )

    # Check duplicate code if being changed
    if "code" in update_data:
        new_code = update_data["code"].strip()
        existing = db.query(SKU).filter(
            SKU.code == new_code,
            SKU.id != sku_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"编号「{new_code}」已被使用",
            )

    # Verify cultural product if changed
    if "cultural_product_id" in update_data:
        product = db.query(CulturalProduct).filter(
            CulturalProduct.id == update_data["cultural_product_id"]
        ).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文创产品不存在",
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
    _current_user: User = Depends(get_current_admin_user),
) -> None:
    """删除 SKU 模板（admin权限）。"""
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU不存在",
        )
    db.delete(sku)
    db.commit()
