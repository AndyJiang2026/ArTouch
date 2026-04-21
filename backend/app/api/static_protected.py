# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create protected static file endpoints with HMAC-signed URLs
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P1

"""
Protected static file endpoints with HMAC-signed URL authentication.

When PROTECT_STATIC_FILES=true:
- Videos: /api/protected/videos/{filename}?expires=ts&signature=sig
- Covers: /api/protected/covers/{filename}?expires=ts&signature=sig

URL format:
  /api/protected/videos/video.mp4?expires=1234567890&signature=hmac_sha256

Signature = HMAC-SHA256(secret_key, f"{filename}:{expires}")
"""

import hashlib
import hmac
import time
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.config import settings

router = APIRouter(prefix="/api/protected", tags=["Protected Files"])


def generate_signature(filename: str, expires: int) -> str:
    """Generate HMAC signature for a file."""
    message = f"{filename}:{expires}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_signature(filename: str, expires: int, signature: str) -> bool:
    """Verify HMAC signature."""
    # Check if expired
    if int(expires) < int(time.time()):
        return False
    # Verify signature
    expected = generate_signature(filename, expires)
    return hmac.compare_digest(expected, signature)


def get_file_from_dir(directory: Path, filename: str) -> Path:
    """Safely resolve file path within directory."""
    # Remove any path traversal attempts
    filename = Path(filename).name
    filepath = directory / filename
    # Ensure the resolved path is within the directory
    filepath = filepath.resolve()
    if not filepath.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return filepath


@router.get("/videos/{filename}")
def get_protected_video(
    filename: str,
    expires: int = Query(..., description="Expiration timestamp"),
    signature: str = Query(..., description="HMAC signature"),
):
    """Get protected video file with signed URL."""
    if not verify_signature(filename, expires, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired signature",
        )
    filepath = get_file_from_dir(settings.VIDEO_DIR, filename)
    return FileResponse(
        filepath,
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@router.get("/covers/{filename}")
def get_protected_cover(
    filename: str,
    expires: int = Query(..., description="Expiration timestamp"),
    signature: str = Query(..., description="HMAC signature"),
):
    """Get protected cover image with signed URL."""
    if not verify_signature(filename, expires, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired signature",
        )
    filepath = get_file_from_dir(settings.COVER_DIR, filename)
    return FileResponse(filepath, filename=filename)


@router.get("/generate-url")
def generate_signed_url(
    path: str = Query(..., description="File path relative to type (e.g., 'video.mp4')"),
    file_type: str = Query(..., description="Type: 'videos' or 'covers'"),
    minutes: int | None = None,
):
    """Generate a signed URL for protected file access.

    This endpoint is for admin use - generate URLs server-side and embed in responses.
    """
    if minutes is None:
        minutes = settings.STATIC_FILE_SIGN_EXPIRE_MINUTES

    expires = int((datetime.utcnow() + timedelta(minutes=minutes)).timestamp())
    signature = generate_signature(path, expires)

    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    if file_type == "videos":
        url = f"{base_url}/api/protected/videos/{path}?expires={expires}&signature={signature}"
    elif file_type == "covers":
        url = f"{base_url}/api/protected/covers/{path}?expires={expires}&signature={signature}"
    else:
        raise HTTPException(status_code=400, detail="Invalid file_type")

    return {
        "url": url,
        "expires": expires,
        "expires_at": datetime.fromtimestamp(expires).isoformat(),
    }


# Import os for generate_signed_url
import os
