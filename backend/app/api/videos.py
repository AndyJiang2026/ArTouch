# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create videos API routes with file upload
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

import os
import uuid
from typing import List, Optional

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.core.video_processor import VideoProcessor
from app.models import Video, User
from app.schemas.video import (
    VideoCreate,
    VideoUpdate,
    VideoResponse,
    VideoProcessResponse,
)

router = APIRouter(prefix="/api/videos", tags=["视频"])


@router.get("/", response_model=List[VideoResponse])
def list_videos(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Video]:
    """List all videos."""
    query = db.query(Video)
    if status:
        query = query.filter(Video.status == status)
    return query.offset(skip).limit(limit).all()


@router.post("/upload", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    code: str = "",
    name: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
            detail=f"文件保存失败: {str(e)}",
        )

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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
        from app.models.cultural_product import CulturalProduct
        product_ids = update_data.pop("cultural_product_ids")
        video.cultural_products = db.query(CulturalProduct).filter(
            CulturalProduct.id.in_(product_ids)
        ).all()

    for key, value in update_data.items():
        setattr(video, key, value)

    db.commit()
    db.refresh(video)
    return video


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
        except OSError:
            pass

    db.delete(video)
    db.commit()


@router.post("/{video_id}/process", response_model=VideoProcessResponse)
def process_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoProcessResponse:
    """Process video with FFmpeg to get duration and info."""
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

    # Get video info
    info = VideoProcessor.get_video_info(video.file_path)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="无法读取视频信息",
        )

    # Update video record
    video.duration = info["duration"]
    video.file_size = info["file_size"]
    video.status = "active"
    db.commit()
    db.refresh(video)

    return VideoProcessResponse(
        duration=info["duration"],
        file_size=info["file_size"],
        resolution=info.get("resolution"),
        message="视频处理成功",
    )
