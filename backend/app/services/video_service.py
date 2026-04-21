# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create video processing service for async FFmpeg background tasks
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P2

"""
Video processing service - async background task for FFmpeg processing.

This module contains the background task function for video processing
that runs FFmpeg commands without blocking the API request.
"""

import logging

from app.config import settings
from app.core.video_processor import VideoProcessor
from app.database import SessionLocal
from app.models import Video

logger = logging.getLogger(__name__)


def process_video_task(video_id: int) -> dict[str, any]:
    """
    Background task to process video: extract info and generate cover image.

    This function runs in a background thread and creates its own database session.

    Args:
        video_id: ID of the video to process

    Returns:
        dict with processing results (duration, file_size, resolution, success, message)
    """
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.warning(f"Video {video_id} not found for background processing")
            return {"success": False, "message": "视频不存在"}

        if not video.file_path:
            logger.warning(f"Video {video_id} has no file path")
            return {"success": False, "message": "视频文件路径不存在"}

        import os

        if not os.path.exists(video.file_path):
            logger.warning(f"Video file {video.file_path} does not exist")
            return {"success": False, "message": "视频文件不存在"}

        # Get video info
        info = VideoProcessor.get_video_info(video.file_path)
        if not info:
            logger.error(f"Failed to get video info for video {video_id}")
            video.status = "failed"
            db.commit()
            return {"success": False, "message": "无法读取视频信息"}

        # Auto-generate cover image from first frame
        cover_filename = f"{video.code}_cover.jpg"
        cover_path = settings.COVER_DIR / cover_filename
        cover_generated = VideoProcessor.generate_thumbnail(
            video_path=video.file_path,
            output_path=str(cover_path),
            time_offset=1.0,
        )

        # Update video record
        video.duration = info["duration"]
        video.file_size = info["file_size"]
        video.status = "active"
        if cover_generated and cover_path.exists():
            video.cover_image = f"/covers/{cover_filename}"
        db.commit()

        message = "视频处理成功"
        if cover_generated:
            message += "，封面图已提取"
        else:
            message += "，封面图提取失败(视频可能过短)"

        logger.info(f"Video {video_id} processed successfully")
        return {
            "success": True,
            "duration": info["duration"],
            "file_size": info["file_size"],
            "resolution": info.get("resolution"),
            "message": message,
        }

    except Exception as e:
        logger.exception(f"Error processing video {video_id}: {e}")
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = "failed"
                db.commit()
        except Exception:
            pass
        return {"success": False, "message": f"处理失败: {e!s}"}
    finally:
        db.close()
