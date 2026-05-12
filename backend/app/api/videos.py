# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create videos API routes with file upload
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

import os
import uuid
import logging
from contextlib import suppress

logger = logging.getLogger(__name__)

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_current_user, get_db, require_operator_or_admin
from app.config import settings
from app.core.video_processor import VideoProcessor
from app.models import CulturalProduct, User, Video
from app.schemas.video import (
    VideoProcessResponse,
    VideoResponse,
    VideoUpdate,
)
from app.schemas.pagination import PaginatedResponse
from app.services.video_service import process_video_task

router = APIRouter(prefix="/api/videos", tags=["视频"])


@router.get("/", response_model=PaginatedResponse[VideoResponse])
def list_videos(
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> PaginatedResponse[VideoResponse]:
    """List all videos (paginated)."""
    query = db.query(Video)
    if status:
        query = query.filter(Video.status == status)
    total = query.count()
    items = query.order_by(Video.id.asc()).offset(skip).limit(limit).all()
    return PaginatedResponse(
        items=items,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.post("/upload", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    code: str = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_operator_or_admin),
) -> Video:
    """Upload a video file (MP4, max 200MB)."""
    if not code or not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="编号和名称不能为空",
        )

    # Validate file type
    if file.content_type not in settings.ALLOWED_VIDEO_TYPES and not file.filename.endswith(".mp4"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持MP4格式视频",
        )

    # Check if code already exists
    existing = db.query(Video).filter(Video.code == code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该编号已被使用",
        )

    # Generate unique filename
    file_ext = os.path.splitext(file.filename or ".mp4")[1] or ".mp4"
    unique_filename = f"{code}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = settings.VIDEO_DIR / unique_filename

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_VIDEO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制 ({settings.MAX_VIDEO_SIZE // (1024*1024)}MB)",
        )

    # Save file asynchronously
    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {e!s}",
        ) from e

    # Create video record
    video = Video(
        code=code,
        name=name,
        file_path=str(file_path),
        file_size=file_size,
        status="processing",
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    return video


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Video:
    """Get video by ID."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在",
        )
    return video


@router.put("/{video_id}", response_model=VideoResponse)
def update_video(
    video_id: int,
    video_data: VideoUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_operator_or_admin),
) -> Video:
    """Update video metadata."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在",
        )

    update_data = video_data.model_dump(exclude_unset=True)

    # Handle cultural product associations
    if "cultural_product_ids" in update_data:
        product_ids = update_data.pop("cultural_product_ids")
        products = db.query(CulturalProduct).filter(CulturalProduct.id.in_(product_ids)).all()
        if len(products) != len(product_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="部分文创产品ID无效或不存在",
            )
        video.cultural_products = products

    for key, value in update_data.items():
        setattr(video, key, value)

    db.commit()
    db.refresh(video)
    return video


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_operator_or_admin),
) -> None:
    """Delete a video."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在",
        )

    # Delete file if exists
    if video.file_path and os.path.exists(video.file_path):
        try:
            os.remove(video.file_path)
        except OSError as e:
            logger.warning(f"删除视频文件失败 (id={video_id}, path={video.file_path}): {e}")

    db.delete(video)
    db.commit()


@router.post("/{video_id}/process", response_model=VideoProcessResponse)
def process_video(
    video_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_operator_or_admin),
) -> VideoProcessResponse:
    """Process video with FFmpeg (async): extract info and generate cover image from first frame."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在",
        )

    if not video.file_path or not os.path.exists(video.file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="视频文件不存在",
        )

    # Mark as processing and schedule background task
    video.status = "processing"
    db.commit()

    # Run FFmpeg processing in background (non-blocking)
    background_tasks.add_task(process_video_task, video_id)

    return VideoProcessResponse(
        duration=0.0,
        file_size=0,
        resolution=None,
        message="视频处理已启动，请在视频详情页查看处理结果",
    )
