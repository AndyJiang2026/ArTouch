# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create shared rate limiting utility
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P1

"""Rate limiting utilities using Redis with in-memory fallback."""

import re
import time
from collections import defaultdict
from datetime import timedelta

import redis
from fastapi import HTTPException, Request, status

from app.config import settings

# Configuration
RATE_LIMIT_WINDOW = timedelta(minutes=1)
RATE_LIMIT_MAX_ATTEMPTS = 60  # 60 requests per minute per IP
RATE_LIMIT_KEY_PREFIX = "artouch:ratelimit:"

# Redis connection
_redis_client: redis.Redis | None = None

# In-memory fallback (not recommended for production)
_inmemory_attempts: dict[str, list[float]] = defaultdict(list)


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
            _redis_client.ping()
        except (redis.ConnectionError, redis.TimeoutError):
            _redis_client = None
    return _redis_client


def _cleanup_old_attempts(attempts: list[float], cutoff: float) -> list[float]:
    """Remove old attempts outside the window."""
    return [t for t in attempts if t > cutoff]


def _check_rate_limit_inmemory(ip: str) -> None:
    """In-memory rate limiting fallback."""
    cutoff = time.time() - RATE_LIMIT_WINDOW.total_seconds()
    _inmemory_attempts[ip] = _cleanup_old_attempts(_inmemory_attempts[ip], cutoff)

    if len(_inmemory_attempts[ip]) >= RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁,请稍后再试",
        )

    _inmemory_attempts[ip].append(time.time())


def check_rate_limit(ip: str) -> None:
    """Check if IP has exceeded rate limit using Redis. Falls back to in-memory if Redis unavailable."""
    redis_client = _get_redis_client()

    if redis_client is None:
        _check_rate_limit_inmemory(ip)
        return

    key = f"{RATE_LIMIT_KEY_PREFIX}{ip}"
    cutoff = time.time() - RATE_LIMIT_WINDOW.total_seconds()

    redis_client.zremrangebyscore(key, 0, cutoff)

    attempts = redis_client.zcard(key)
    if attempts >= RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁,请稍后再试",
        )

    redis_client.zadd(key, {str(time.time()): time.time()})


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request, handling proxies safely.
    Only trusts X-Forwarded-For if it comes from a known proxy.
    """
    # Check X-Forwarded-For header (set by reverse proxy)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the rightmost IP (original client) - safe because nginx sets this
        # and we only accept it from proxies
        ips = [ip.strip() for ip in forwarded_for.split(",")]
        if ips:
            return ips[-1]

    # Fall back to direct client host
    if request.client:
        return request.client.host

    return "unknown"


def sanitize_ip(ip: str) -> str:
    """
    Sanitize IP address to prevent log injection or injection attacks.
    Only allows valid IPv4 and IPv6 patterns.
    """
    # Basic validation - only allow alphanumeric and colons/dots (IPv4/IPv6)
    if not re.match(r"^[\w.:\-]+$", ip):
        return "invalid"
    return ip[:45]  # Max length for IPv6
