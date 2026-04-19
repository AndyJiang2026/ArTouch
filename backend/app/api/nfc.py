# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create public NFC play API routes
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import NFCTag, TagClick, CulturalProduct, Video
from app.schemas.nfc_tag import NFCPlayResponse

router = APIRouter(prefix="/api/nfc", tags=["NFC公开接口"])


def get_db_public():
    """Database session for public endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{code}/play", response_model=NFCPlayResponse)
def nfc_play(
    code: str,
    request: Request,
    visitor_id: Optional[str] = Query(None),
    db: Session = Depends(get_db_public),
) -> NFCPlayResponse:
    """
    Public endpoint for NFC tag playback.
    Records click and returns video information.
    """
    # Find the NFC tag
    tag = db.query(NFCTag).filter(NFCTag.url_code == code).first()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NFC标签不存在",
        )

    # Check approval status
    if tag.approval_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NFC标签待审批或已驳回",
        )

    # Check if expired
    if tag.expires_at and tag.expires_at < datetime.utcnow().date():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NFC标签已过期",
        )

    # Get video and cultural product
    video = db.query(Video).filter(Video.id == tag.video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关联视频不存在",
        )

    cultural_product = db.query(CulturalProduct).filter(
        CulturalProduct.id == tag.cultural_product_id
    ).first()
    if not cultural_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关联文创品不存在",
        )

    # Record the click
    client_ip = request.client.host if request.client else None
    referer = request.headers.get("referer")

    tag_click = TagClick(
        tag_id=tag.id,
        visitor_id=visitor_id,
        device_info=request.headers.get("user-agent"),
        ip_address=client_ip,
        referer=referer,
        clicked_at=datetime.utcnow(),
    )
    db.add(tag_click)
    db.commit()

    # Generate video URL
    if video.file_path and os.path.exists(video.file_path):
        video_url = f"/videos/{os.path.basename(video.file_path)}"
    else:
        video_url = video.file_path or ""

    return NFCPlayResponse(
        video_url=video_url,
        title=video.name,
        cultural_product_name=cultural_product.name,
        duration=video.duration,
    )
