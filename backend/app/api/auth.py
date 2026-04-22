# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create authentication API routes
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

import time
from datetime import timedelta
from typing import Any

import redis
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models import User
from app.schemas.user import PasswordChangeRequest, UserResponse

router = APIRouter(prefix="/api/auth", tags=["认证"])

# Rate limiting configuration
RATE_LIMIT_WINDOW = timedelta(minutes=5)
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_KEY_PREFIX = "artouch:login_attempts:"

# Redis connection for distributed rate limiting
_redis_client: redis.Redis | None = None


def _get_redis_client() -> redis.Redis | None:
    """Get or create Redis client with connection pooling."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            # Test connection
            _redis_client.ping()
        except (redis.ConnectionError, redis.TimeoutError):
            _redis_client = None
    return _redis_client


def _check_rate_limit(ip: str) -> None:
    """Check if IP has exceeded rate limit using Redis. Falls back to in-memory if Redis unavailable."""
    redis_client = _get_redis_client()

    if redis_client is None:
        # Fallback to in-memory (not recommended for production)
        _check_rate_limit_inmemory(ip)
        return

    key = f"{RATE_LIMIT_KEY_PREFIX}{ip}"
    cutoff = time.time() - RATE_LIMIT_WINDOW.total_seconds()

    # Use Redis sorted set with timestamp as score
    # Remove old entries outside the window
    redis_client.zremrangebyscore(key, 0, cutoff)

    # Count remaining attempts
    attempts = redis_client.zcard(key)
    if attempts >= RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="登录尝试次数过多,请5分钟后再试",
        )


def _record_attempt(ip: str) -> None:
    """Record a failed login attempt using Redis."""
    redis_client = _get_redis_client()

    if redis_client is None:
        # Fallback to in-memory (not recommended for production)
        _record_attempt_inmemory(ip)
        return

    key = f"{RATE_LIMIT_KEY_PREFIX}{ip}"
    now = time.time()

    # Add attempt with current timestamp as score
    redis_client.zadd(key, {f"{now}": now})

    # Set expiration on the key (window + 1 minute buffer)
    redis_client.expire(key, int(RATE_LIMIT_WINDOW.total_seconds()) + 60)


# In-memory fallback for when Redis is unavailable
_inmemory_attempts: dict[str, list] = {}


def _check_rate_limit_inmemory(ip: str) -> None:
    """In-memory fallback for rate limiting."""
    global _inmemory_attempts
    cutoff = time.time() - RATE_LIMIT_WINDOW.total_seconds()
    _inmemory_attempts[ip] = [t for t in _inmemory_attempts.get(ip, []) if t > cutoff]
    if len(_inmemory_attempts.get(ip, [])) >= RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="登录尝试次数过多,请5分钟后再试",
        )


def _record_attempt_inmemory(ip: str) -> None:
    """In-memory fallback for recording attempts."""
    global _inmemory_attempts
    if ip not in _inmemory_attempts:
        _inmemory_attempts[ip] = []
    _inmemory_attempts[ip].append(time.time())


@router.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
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

    # Increment login count and mark as not first login
    user.login_count = (user.login_count or 0) + 1
    user.is_first_login = False
    db.commit()

    access_token_expires = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=access_token_expires,
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id), "role": user.role})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "is_first_login": user.is_first_login,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "is_first_login": user.is_first_login,
            "login_count": user.login_count,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }


@router.post("/refresh-token")
def refresh_token(
    refresh_token: str = Form(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Refresh access token using refresh token."""
    token_data = decode_token(refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
        )

    if token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌类型",
        )

    user_id = int(token_data.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
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
    new_refresh_token = create_refresh_token(data={"sub": str(user.id), "role": user.role})

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    }


@router.post("/logout")
def logout(_current_user: User = Depends(get_current_user)) -> dict[str, str]:
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
) -> dict[str, str]:
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
