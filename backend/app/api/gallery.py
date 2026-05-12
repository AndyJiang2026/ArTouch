# AI-ASSISTED: Yes
# AI-TOOL: Hermes Agent
# PROMPT: 创建画卷管理API路由（GET/POST/DELETE）
# DATE: 2026-04-28
# ENGINEER: System
# RISK-LEVEL: P2

"""
画卷管理API路由。

画卷数据存储在 /static/game/gallery.json 中，
图片文件存储在 /static/game/ 目录。
管理员可上传新画卷图片 -> 自动裁剪600x600 -> 更新gallery.json。
"""

import json
import os
import shutil
import threading
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image

from app.api.deps import get_current_admin_user
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/api/gallery", tags=["画卷管理"])

GALLERY_DIR = settings.BASE_DIR.parent / "static" / "game"
GALLERY_JSON = GALLERY_DIR / "gallery.json"

_gallery_lock = threading.Lock()

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


def _load_gallery() -> list[dict]:
    """加载画卷JSON数据。"""
    if not GALLERY_JSON.exists():
        return []
    with _gallery_lock:
        with open(GALLERY_JSON, "r", encoding="utf-8") as f:
            return json.load(f)


def _save_gallery(gallery: list[dict]) -> None:
    """保存画卷JSON数据。"""
    with _gallery_lock:
        with open(GALLERY_JSON, "w", encoding="utf-8") as f:
            json.dump(gallery, f, ensure_ascii=False, indent=2)


@router.get("/")
def list_gallery():
    """获取所有画卷列表（公开接口，无需登录）。"""
    gallery = _load_gallery()
    return gallery


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_gallery(
    title: str = Form(...),
    has_horse: bool = Form(False),
    story: str = Form(""),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
):
    """上传新画卷（仅admin）。自动裁剪图片为600x600正方形。"""
    # 验证文件类型
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片文件")

    # 验证文件大小（不超过10MB）
    image.file.seek(0, os.SEEK_END)
    file_size = image.file.tell()
    image.file.seek(0)
    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="图片大小超过10MB限制")

    # 读取图片
    try:
        img = Image.open(image.file)
        img = img.convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="无法解析图片文件")

    # 居中裁剪为正方形
    w, h = img.size
    size = min(w, h)
    left = (w - size) // 2
    top = (h - size) // 2
    cropped = img.crop((left, top, left + size, top + size))

    # 缩放至600x600
    resized = cropped.resize((600, 600), Image.LANCZOS)

    # 生成唯一id和文件名
    album_id = str(uuid.uuid4())[:8]
    filename = f"{album_id}_600.jpg"
    filepath = GALLERY_DIR / filename

    resized.save(filepath, quality=85)
    image.file.close()

    # 解析故事段落（按空行或换行分割）
    story_paragraphs = [s.strip() for s in story.split("\n") if s.strip()]
    if not story_paragraphs:
        story_paragraphs = [title]

    # 构建画卷条目
    entry = {
        "id": album_id,
        "title": title,
        "image": filename,
        "enabled": True,
        "hasHorse": has_horse,
        "story": story_paragraphs,
    }

    # 加载现有数据并追加
    gallery = _load_gallery()
    gallery.append(entry)
    _save_gallery(gallery)

    return entry


@router.patch("/{album_id}/toggle", description="互斥启用：启用当前画卷时自动禁用其他所有画卷")
def toggle_gallery(
    album_id: str,
    current_user: User = Depends(get_current_admin_user),
):
    """切换画卷启用/停用状态（仅admin）。互斥启用：启用一个时自动禁用其他。"""
    gallery = _load_gallery()
    entry = next((e for e in gallery if e["id"] == album_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="画卷未找到")

    # 如果当前已启用，则停用（允许全部停用）
    if entry.get("enabled", True):
        entry["enabled"] = False
    else:
        # 互斥启用：启用当前，禁用其他所有
        for e in gallery:
            e["enabled"] = False
        entry["enabled"] = True

    _save_gallery(gallery)

    return {"id": album_id, "enabled": entry["enabled"]}


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gallery(
    album_id: str,
    current_user: User = Depends(get_current_admin_user),
):
    """删除画卷（仅admin）。"""
    gallery = _load_gallery()
    entry = next((e for e in gallery if e["id"] == album_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="画卷未找到")

    # 删除图片文件
    image_path = GALLERY_DIR / entry["image"]
    if image_path.exists():
        os.remove(image_path)

    # 也尝试删除对应的tiles目录（如果存在）
    tiles_dir = GALLERY_DIR / "tiles" / album_id
    if tiles_dir.exists():
        shutil.rmtree(tiles_dir)

    # 从列表移除
    gallery = [e for e in gallery if e["id"] != album_id]
    _save_gallery(gallery)

    return None
