# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create JWT and bcrypt security module
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P1

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash of password."""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token. If expires_delta is None, token never expires."""
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + expires_delta if expires_delta else None
    to_encode.update({"iat": now, "type": "access"})
    if expire:
        to_encode["exp"] = expire
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT refresh token. If expires_delta is None, token never expires."""
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + expires_delta if expires_delta else None
    to_encode.update({"iat": now, "type": "refresh"})
    if expire:
        to_encode["exp"] = expire
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str, verify_exp: bool = True) -> dict[str, Any] | None:
    """Decode and verify a JWT token. Set verify_exp=False for tokens without expiration."""
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": verify_exp} if not verify_exp else {},
        )
    except JWTError:
        return None
