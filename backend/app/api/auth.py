# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create authentication API routes
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

import time
from collections import defaultdict
from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models import User
from app.schemas.user import LoginRequest, PasswordChangeRequest, UserResponse

router = APIRouter(prefix="/api/auth", tags=["认证"])

# Rate limiting storage: {ip: [(timestamp, count), ...]}
_login_attempts: Dict[str, list] = defaultdict(list)
RATE_LIMIT_WINDOW = timedelta(minutes=5)
RATE_LIMIT_MAX_ATTEMPTS = 5


def _clean_old_attempts(ip: str) -> None:
    """Remove attempts older than the rate limit window."""
    cutoff = time.time() - RATE_LIMIT_WINDOW.total_seconds()
    _login_attempts[ip] = [t for t in _login_attempts[ip] if t > cutoff]


def _check_rate_limit(ip: str) -> None:
    """Check if IP has exceeded rate limit. Raises HTTPException if exceeded."""
    _clean_old_attempts(ip)
    attempts = _login_attempts[ip]
    if len(attempts) >= RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="登录尝试次数过多，请5分钟后再试",
        )


def _record_attempt(ip: str) -> None:
    """Record a failed login attempt."""
    _login_attempts[ip].append(time.time())


@router.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """User login, returns JWT token."""
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit
    _check_rate_limit(client_ip)

    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        _record_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not verify_password(form_data.password, user.password_hash):
        _record_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    access_token_expires = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_first_login": user.is_first_login,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    }


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    """User logout (client should discard token)."""
    return {"message": "登出成功"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Get current user information."""
    return current_user


@router.post("/change-password")
def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Change user password (required on first login or voluntarily)."""
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误",
        )

    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.is_first_login = False
    db.commit()

    return {"message": "密码修改成功"}
