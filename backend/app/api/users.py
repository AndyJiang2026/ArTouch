# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create user management API routes with RBAC (admin-only user creation)
# DATE: 2026-04-21
# ENGINEER: System
# RISK-LEVEL: P1

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db, get_current_user
from app.core.security import get_password_hash
from app.models import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/api/users", tags=["用户管理"])


def get_user_or_404(db: Session, user_id: int) -> User:
    """Get user by ID or raise 404."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return user


@router.get("/", response_model=PaginatedResponse[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    role: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> PaginatedResponse[UserResponse]:
    """List all users (admin only)."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)

    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return PaginatedResponse(
        items=items,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> User:
    """Create a new user (admin only).

    RBAC: Only administrators can create new users.
    Operators attempting to access this endpoint will receive 403 Forbidden.
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    # Validate role is valid
    if user_data.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户角色",
        )

    # Create new user
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=user_data.is_active,
        is_first_login=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> User:
    """Get a specific user by ID (admin only)."""
    return get_user_or_404(db, user_id)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> User:
    """Update a user (admin only)."""
    user = get_user_or_404(db, user_id)

    # Prevent modifying the last admin
    if user_data.role == "operator" and user.role == "admin":
        admin_count = db.query(User).filter(User.role == "admin", User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能将最后一个管理员降为操作员",
            )

    if user_data.username is not None:
        # Check if new username is taken by another user
        existing = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用",
            )
        user.username = user_data.username

    if user_data.role is not None:
        if user_data.role not in ["admin", "operator"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的用户角色",
            )
        user.role = user_data.role

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> None:
    """Delete a user (admin only)."""
    user = get_user_or_404(db, user_id)

    # Prevent deleting the last admin
    if user.role == "admin":
        admin_count = db.query(User).filter(User.role == "admin", User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除最后一个管理员",
            )

    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除当前登录用户",
        )

    db.delete(user)
    db.commit()
