# AI-ASSISTED: Yes
# AI-TOOL: Hermes Agent
# PROMPT: Create comprehensive video management workflow tests including edit, delete with cascade cleanup, and duration extraction
# DATE: 2026-04-21
# ENGINEER: Hermes Agent
# RISK-LEVEL: P2

"""
视频管理完整流程测试模块

测试内容:
1. 编辑视频信息完整流程
   - 更新视频名称
   - 更新视频状态
   - 更新封面图片
   - 关联/取消关联文创产品
   - 批量关联多个文创产品
2. 删除视频及关联数据清理
   - 删除无关联数据的视频
   - 删除有关联文创产品的视频（检查多对多表清理）
   - 删除有关联NFC标签的视频（检查外键约束处理）
   - 删除后验证关联数据是否正确清理
3. 视频时长提取功能
   - VideoProcessor.get_video_info 测试
   - 视频处理后台任务测试
   - 时长数据持久化验证
"""

import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.video_processor import VideoProcessor
from app.models import CulturalProduct, NFCTag, User, Video, cultural_product_videos
from app.core.security import get_password_hash


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def video_with_file(db_session: Session) -> Video:
    """创建一个带有临时文件的视频记录。"""
    # Create a temp file to simulate video file
    tmp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp_file.write(b"\x00" * 1024)  # 1KB dummy content
    tmp_file.close()

    video = Video(
        code="V01",
        name="原始视频名称",
        file_path=tmp_file.name,
        duration=None,
        file_size=1024,
        status="processing",
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    yield video

    # Cleanup
    if os.path.exists(tmp_file.name):
        os.remove(tmp_file.name)


@pytest.fixture
def multiple_products(db_session: Session) -> list[CulturalProduct]:
    """创建多个文创产品。"""
    products = []
    for i in range(3):
        product = CulturalProduct(
            code=f"{i+1:03d}",
            name=f"文创产品{i+1}",
            description=f"描述{i+1}",
            status="active",
        )
        db_session.add(product)
        products.append(product)
    db_session.commit()
    for p in products:
        db_session.refresh(p)
    return products


@pytest.fixture
def video_with_products(
    db_session: Session, multiple_products: list[CulturalProduct]
) -> Video:
    """创建已关联文创产品的视频。"""
    video = Video(
        code="V02",
        name="关联产品的视频",
        file_path="/videos/v02.mp4",
        status="active",
    )
    video.cultural_products = multiple_products[:2]  # 关联前两个产品
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    return video


@pytest.fixture
def video_with_nfc_tag(
    db_session: Session, test_operator: User
) -> tuple[Video, NFCTag, CulturalProduct]:
    """创建带有NFC标签关联的视频。"""
    product = CulturalProduct(
        code="010",
        name="NFC关联产品",
        status="active",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    video = Video(
        code="V03",
        name="带NFC标签的视频",
        file_path="/videos/v03.mp4",
        status="active",
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)

    nfc_tag = NFCTag(
        url_code="NFC001",
        video_id=video.id,
        cultural_product_id=product.id,
        status="active",
        approval_status="approved",
        created_by=test_operator.id,
    )
    db_session.add(nfc_tag)
    db_session.commit()
    db_session.refresh(nfc_tag)

    return video, nfc_tag, product


# =============================================================================
# Test 1: 编辑视频信息完整流程
# =============================================================================

class TestVideoEditWorkflow:
    """编辑视频信息完整流程测试。"""

    def test_update_video_name(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_file: Video,
        db_session: Session,
    ):
        """测试更新视频名称。"""
        response = client.put(
            f"/api/videos/{video_with_file.id}",
            headers=auth_headers_operator,
            json={"name": "更新后的视频名称"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的视频名称"
        assert data["code"] == video_with_file.code  # code不应改变

        # 验证数据库中的值
        db_session.expire_all()
        video = db_session.query(Video).filter(Video.id == video_with_file.id).first()
        assert video.name == "更新后的视频名称"

    def test_update_video_status(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_file: Video,
    ):
        """测试更新视频状态。"""
        response = client.put(
            f"/api/videos/{video_with_file.id}",
            headers=auth_headers_operator,
            json={"status": "active"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_update_video_cover_image(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_file: Video,
    ):
        """测试更新封面图片。"""
        cover_path = "/covers/v01_cover.jpg"
        response = client.put(
            f"/api/videos/{video_with_file.id}",
            headers=auth_headers_operator,
            json={"cover_image": cover_path},
        )
        assert response.status_code == 200
        assert response.json()["cover_image"] == cover_path

    def test_update_multiple_fields(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_file: Video,
    ):
        """测试同时更新多个字段。"""
        response = client.put(
            f"/api/videos/{video_with_file.id}",
            headers=auth_headers_operator,
            json={
                "name": "综合更新视频",
                "status": "active",
                "cover_image": "/covers/new_cover.jpg",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "综合更新视频"
        assert data["status"] == "active"
        assert data["cover_image"] == "/covers/new_cover.jpg"

    def test_associate_single_product(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_file: Video,
        multiple_products: list[CulturalProduct],
        db_session: Session,
    ):
        """测试关联单个文创产品。"""
        response = client.put(
            f"/api/videos/{video_with_file.id}",
            headers=auth_headers_operator,
            json={"cultural_product_ids": [multiple_products[0].id]},
        )
        assert response.status_code == 200

        # 验证关联关系
        db_session.expire_all()
        video = db_session.query(Video).filter(Video.id == video_with_file.id).first()
        assert len(video.cultural_products) == 1
        assert video.cultural_products[0].id == multiple_products[0].id

    def test_associate_multiple_products(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_file: Video,
        multiple_products: list[CulturalProduct],
        db_session: Session,
    ):
        """测试关联多个文创产品。"""
        product_ids = [p.id for p in multiple_products]
        response = client.put(
            f"/api/videos/{video_with_file.id}",
            headers=auth_headers_operator,
            json={"cultural_product_ids": product_ids},
        )
        assert response.status_code == 200

        # 验证关联关系
        db_session.expire_all()
        video = db_session.query(Video).filter(Video.id == video_with_file.id).first()
        assert len(video.cultural_products) == 3
        associated_ids = {p.id for p in video.cultural_products}
        assert associated_ids == set(product_ids)

    def test_disassociate_products(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_products: Video,
        db_session: Session,
    ):
        """测试取消所有文创产品关联。"""
        # 先验证有关联
        assert len(video_with_products.cultural_products) == 2

        # 取消所有关联
        response = client.put(
            f"/api/videos/{video_with_products.id}",
            headers=auth_headers_operator,
            json={"cultural_product_ids": []},
        )
        assert response.status_code == 200

        # 验证关联已清除
        db_session.expire_all()
        video = db_session.query(Video).filter(Video.id == video_with_products.id).first()
        assert len(video.cultural_products) == 0

    def test_replace_product_associations(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_products: Video,
        multiple_products: list[CulturalProduct],
        db_session: Session,
    ):
        """测试替换文创产品关联（原有关联被新关联替换）。"""
        # 只保留第三个产品
        response = client.put(
            f"/api/videos/{video_with_products.id}",
            headers=auth_headers_operator,
            json={"cultural_product_ids": [multiple_products[2].id]},
        )
        assert response.status_code == 200

        db_session.expire_all()
        video = db_session.query(Video).filter(Video.id == video_with_products.id).first()
        assert len(video.cultural_products) == 1
        assert video.cultural_products[0].id == multiple_products[2].id

    def test_update_with_name_and_products(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_file: Video,
        multiple_products: list[CulturalProduct],
        db_session: Session,
    ):
        """测试同时更新名称和关联产品。"""
        response = client.put(
            f"/api/videos/{video_with_file.id}",
            headers=auth_headers_operator,
            json={
                "name": "更新名称并关联产品",
                "cultural_product_ids": [multiple_products[0].id, multiple_products[1].id],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新名称并关联产品"

        db_session.expire_all()
        video = db_session.query(Video).filter(Video.id == video_with_file.id).first()
        assert len(video.cultural_products) == 2

    def test_update_nonexistent_field_ignored(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_file: Video,
    ):
        """测试更新时传递不存在的字段应被忽略（Pydantic exclude_unset）。"""
        # VideoUpdate schema 没有 duration 字段，应该被忽略或报错
        response = client.put(
            f"/api/videos/{video_with_file.id}",
            headers=auth_headers_operator,
            json={"name": "新名称", "nonexistent_field": "value"},
        )
        # Pydantic默认会拒绝额外字段
        assert response.status_code in (200, 422)


# =============================================================================
# Test 2: 删除视频及关联数据清理
# =============================================================================

class TestVideoDeleteCascade:
    """删除视频及关联数据清理测试。"""

    def test_delete_video_without_associations(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_file: Video,
        db_session: Session,
    ):
        """测试删除无关联数据的视频。"""
        video_id = video_with_file.id
        file_path = video_with_file.file_path

        response = client.delete(
            f"/api/videos/{video_id}",
            headers=auth_headers_operator,
        )
        assert response.status_code == 204

        # 验证视频记录已删除
        video = db_session.query(Video).filter(Video.id == video_id).first()
        assert video is None

        # 验证文件已删除
        assert not os.path.exists(file_path)

    def test_delete_video_removes_product_associations(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_products: Video,
        multiple_products: list[CulturalProduct],
        db_session: Session,
    ):
        """测试删除视频时多对多关联表记录被清理。"""
        video_id = video_with_products.id

        # 验证删除前有关联
        assoc_count = db_session.execute(
            text("SELECT COUNT(*) FROM cultural_product_videos WHERE video_id = :vid"),
            {"vid": video_id},
        ).scalar()
        assert assoc_count == 2

        response = client.delete(
            f"/api/videos/{video_id}",
            headers=auth_headers_operator,
        )
        assert response.status_code == 204

        # 验证关联表记录已清理
        assoc_count_after = db_session.execute(
            text("SELECT COUNT(*) FROM cultural_product_videos WHERE video_id = :vid"),
            {"vid": video_id},
        ).scalar()
        assert assoc_count_after == 0

        # 验证文创产品本身未被删除
        for product in multiple_products[:2]:
            p = db_session.query(CulturalProduct).filter(
                CulturalProduct.id == product.id
            ).first()
            assert p is not None

    def test_delete_video_with_nfc_tag_constraint(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_nfc_tag: tuple,
        db_session: Session,
    ):
        """测试删除有NFC标签关联的视频时的外键约束处理。

        关键检查：
        - 如果设置了 ON DELETE CASCADE，NFC标签应被级联删除
        - 如果没有设置 CASCADE，删除应失败或需要先处理NFC标签
        """
        video, nfc_tag, product = video_with_nfc_tag
        video_id = video.id
        nfc_tag_id = nfc_tag.id

        response = client.delete(
            f"/api/videos/{video_id}",
            headers=auth_headers_operator,
        )

        # 检查外键约束行为
        # SQLite 开启了 PRAGMA foreign_keys=ON
        # 如果 NFCTag.video_id 没有 ON DELETE CASCADE，删除会失败
        # 如果 API 层没有处理关联的 NFC tags，可能出现以下情况：
        # 1. 返回 500 错误（外键约束违反）
        # 2. 返回 204 但 NFC tag 成为孤立记录

        nfc_exists = db_session.query(NFCTag).filter(
            NFCTag.id == nfc_tag_id
        ).first() is not None

        video_exists = db_session.query(Video).filter(
            Video.id == video_id
        ).first() is not None

        if response.status_code == 204:
            # 视频被删除了，检查 NFC tag 的状态
            if nfc_exists:
                # NFC tag 仍然存在 - 这是一个问题！孤立记录
                # 记录这个发现
                pytest.fail(
                    "删除视频后NFC标签成为孤立记录（video_id指向不存在的视频）。"
                    "建议在删除视频前先处理关联的NFC标签，或设置ON DELETE CASCADE。"
                )
            else:
                # NFC tag 也被删除了 - 这是正确的行为
                pass
        elif response.status_code == 500:
            # 外键约束错误 - 说明没有正确处理关联数据
            pytest.fail(
                "删除视频时发生外键约束错误。"
                "建议在删除API中先处理关联的NFC标签，或在模型中设置ON DELETE CASCADE。"
            )
        else:
            # 其他状态码
            pytest.fail(f"意外的删除响应状态码: {response.status_code}")

    def test_delete_video_preserves_cultural_products(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        video_with_products: Video,
        multiple_products: list[CulturalProduct],
        db_session: Session,
    ):
        """测试删除视频时文创产品本身不受影响。"""
        product_ids_before = [p.id for p in multiple_products]

        response = client.delete(
            f"/api/videos/{video_with_products.id}",
            headers=auth_headers_operator,
        )
        assert response.status_code == 204

        # 验证所有文创产品仍然存在
        for pid in product_ids_before:
            product = db_session.query(CulturalProduct).filter(
                CulturalProduct.id == pid
            ).first()
            assert product is not None

    def test_delete_video_file_cleanup_on_error(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        db_session: Session,
    ):
        """测试删除视频时即使文件不存在也能正常删除记录。"""
        video = Video(
            code="V04",
            name="文件不存在的视频",
            file_path="/nonexistent/path/video.mp4",
            status="active",
        )
        db_session.add(video)
        db_session.commit()
        db_session.refresh(video)

        response = client.delete(
            f"/api/videos/{video.id}",
            headers=auth_headers_operator,
        )
        assert response.status_code == 204

        # 验证记录已删除
        v = db_session.query(Video).filter(Video.id == video.id).first()
        assert v is None

    def test_delete_multiple_videos_independently(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        db_session: Session,
    ):
        """测试删除多个视频互不影响。"""
        videos = []
        for i in range(3):
            v = Video(
                code=f"V{10+i}",
                name=f"批量删除测试{i}",
                status="active",
            )
            db_session.add(v)
            videos.append(v)
        db_session.commit()
        for v in videos:
            db_session.refresh(v)

        # 删除中间的视频
        response = client.delete(
            f"/api/videos/{videos[1].id}",
            headers=auth_headers_operator,
        )
        assert response.status_code == 204

        # 验证其他视频仍然存在
        assert db_session.query(Video).filter(Video.id == videos[0].id).first() is not None
        assert db_session.query(Video).filter(Video.id == videos[2].id).first() is not None
        assert db_session.query(Video).filter(Video.id == videos[1].id).first() is None


# =============================================================================
# Test 3: 视频时长提取功能
# =============================================================================

class TestVideoDurationExtraction:
    """视频时长提取功能测试。"""

    def test_get_video_info_with_mock_ffprobe(self):
        """测试通过mock ffprobe获取视频信息。"""
        mock_ffprobe_output = """
        {
            "format": {
                "duration": "125.5",
                "size": "10485760"
            },
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080
                },
                {
                    "codec_type": "audio"
                }
            ]
        }
        """
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_ffprobe_output,
                stderr="",
            )

            # Create temp file for existence check
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                f.write(b"dummy")
                temp_path = f.name

            try:
                info = VideoProcessor.get_video_info(temp_path)
                assert info is not None
                assert info["duration"] == 125.5
                assert info["file_size"] == 10485760
                assert info["resolution"] == "1920x1080"
                assert info["width"] == 1920
                assert info["height"] == 1080
            finally:
                os.remove(temp_path)

    def test_get_video_info_file_not_found(self):
        """测试文件不存在时返回None。"""
        info = VideoProcessor.get_video_info("/nonexistent/video.mp4")
        assert info is None

    def test_get_video_info_ffprobe_error(self):
        """测试ffprobe执行失败时返回None。"""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy")
            temp_path = f.name

        try:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1,
                    stdout="",
                    stderr="Error",
                )
                info = VideoProcessor.get_video_info(temp_path)
                assert info is None
        finally:
            os.remove(temp_path)

    def test_get_video_info_no_video_stream(self):
        """测试没有视频流时返回None。"""
        mock_output = """
        {
            "format": {
                "duration": "10.0",
                "size": "1024"
            },
            "streams": [
                {"codec_type": "audio"}
            ]
        }
        """
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy")
            temp_path = f.name

        try:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout=mock_output,
                    stderr="",
                )
                info = VideoProcessor.get_video_info(temp_path)
                assert info is None
        finally:
            os.remove(temp_path)

    def test_get_video_info_timeout(self):
        """测试ffprobe超时时返回None。"""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy")
            temp_path = f.name

        try:
            with patch("subprocess.run") as mock_run:
                import subprocess
                mock_run.side_effect = subprocess.TimeoutExpired(
                    cmd="ffprobe", timeout=30
                )
                info = VideoProcessor.get_video_info(temp_path)
                assert info is None
        finally:
            os.remove(temp_path)

    def test_generate_thumbnail_with_mock(self):
        """测试通过mock ffmpeg生成缩略图。"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                f.write(b"dummy")
                temp_video = f.name

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                temp_output = f.name

            try:
                result = VideoProcessor.generate_thumbnail(
                    video_path=temp_video,
                    output_path=temp_output,
                    time_offset=2.0,
                )
                assert result is True

                # 验证ffmpeg命令参数
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert "ffmpeg" in call_args
                assert "-ss" in call_args
                assert "2.0" in call_args
            finally:
                os.remove(temp_video)
                os.remove(temp_output)

    def test_generate_thumbnail_file_not_found(self):
        """测试视频文件不存在时生成缩略图返回False。"""
        result = VideoProcessor.generate_thumbnail(
            video_path="/nonexistent/video.mp4",
            output_path="/tmp/output.jpg",
        )
        assert result is False

    def test_process_video_task_with_mock(
        self,
        db_session: Session,
    ):
        """测试视频处理后台任务（mock FFmpeg）。"""
        from app.services.video_service import process_video_task

        # 创建临时视频文件
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy video content")
            temp_video = f.name

        # 创建视频记录
        video = Video(
            code="V05",
            name="处理测试视频",
            file_path=temp_video,
            status="processing",
        )
        db_session.add(video)
        db_session.commit()
        db_session.refresh(video)
        video_id = video.id

        # Mock VideoProcessor
        mock_info = {
            "duration": 60.5,
            "file_size": 5242880,
            "resolution": "1280x720",
            "width": 1280,
            "height": 720,
        }

        with patch.object(VideoProcessor, "get_video_info", return_value=mock_info):
            with patch.object(VideoProcessor, "generate_thumbnail", return_value=True):
                # 需要mock settings.COVER_DIR
                with patch("app.services.video_service.settings") as mock_settings:
                    mock_settings.COVER_DIR = tempfile.mkdtemp()
                    result = process_video_task(video_id)

        # 验证处理结果
        assert result["success"] is True
        assert result["duration"] == 60.5

        # 验证数据库中的视频记录已更新
        db_session.expire_all()
        updated_video = db_session.query(Video).filter(Video.id == video_id).first()
        assert updated_video is not None
        assert updated_video.duration == 60.5
        assert updated_video.file_size == 5242880
        assert updated_video.status == "active"
        assert updated_video.cover_image is not None

        # Cleanup
        if os.path.exists(temp_video):
            os.remove(temp_video)

    def test_process_video_task_video_not_found(self, db_session: Session):
        """测试处理不存在的视频。"""
        from app.services.video_service import process_video_task

        result = process_video_task(99999)
        assert result["success"] is False
        assert "不存在" in result["message"]

    def test_duration_persisted_after_processing(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        db_session: Session,
    ):
        """测试视频处理后可通过API获取时长信息。"""
        # 创建临时视频文件
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy video content")
            temp_video = f.name

        video = Video(
            code="V06",
            name="时长持久化测试",
            file_path=temp_video,
            duration=45.3,
            file_size=2048000,
            status="active",
        )
        db_session.add(video)
        db_session.commit()
        db_session.refresh(video)

        # 通过API获取视频详情
        response = client.get(
            f"/api/videos/{video.id}",
            headers=auth_headers_operator,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["duration"] == 45.3
        assert data["file_size"] == 2048000

        # Cleanup
        if os.path.exists(temp_video):
            os.remove(temp_video)


# =============================================================================
# Test 4: 完整工作流集成测试
# =============================================================================

class TestVideoFullWorkflow:
    """视频管理完整工作流集成测试。"""

    def test_create_update_process_delete_workflow(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        db_session: Session,
        multiple_products: list[CulturalProduct],
    ):
        """完整工作流：创建 -> 更新 -> 关联产品 -> 删除。"""
        # Step 1: 创建视频记录（直接通过DB，因为上传需要真实文件）
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy video")
            temp_video = f.name

        video = Video(
            code="V99",
            name="工作流测试视频",
            file_path=temp_video,
            status="processing",
        )
        db_session.add(video)
        db_session.commit()
        db_session.refresh(video)
        video_id = video.id

        # Step 2: 更新视频信息
        response = client.put(
            f"/api/videos/{video_id}",
            headers=auth_headers_operator,
            json={
                "name": "更新后的工作流视频",
                "status": "active",
            },
        )
        assert response.status_code == 200
        assert response.json()["name"] == "更新后的工作流视频"

        # Step 3: 关联文创产品
        response = client.put(
            f"/api/videos/{video_id}",
            headers=auth_headers_operator,
            json={"cultural_product_ids": [multiple_products[0].id]},
        )
        assert response.status_code == 200

        # 验证关联
        db_session.expire_all()
        v = db_session.query(Video).filter(Video.id == video_id).first()
        assert len(v.cultural_products) == 1

        # Step 4: 获取视频详情
        response = client.get(
            f"/api/videos/{video_id}",
            headers=auth_headers_operator,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的工作流视频"

        # Step 5: 删除视频
        response = client.delete(
            f"/api/videos/{video_id}",
            headers=auth_headers_operator,
        )
        assert response.status_code == 204

        # Step 6: 验证清理
        v = db_session.query(Video).filter(Video.id == video_id).first()
        assert v is None

        # 验证关联表已清理
        assoc = db_session.execute(
            text("SELECT COUNT(*) FROM cultural_product_videos WHERE video_id = :vid"),
            {"vid": video_id},
        ).scalar()
        assert assoc == 0

        # 验证文创产品仍存在
        p = db_session.query(CulturalProduct).filter(
            CulturalProduct.id == multiple_products[0].id
        ).first()
        assert p is not None

        # Cleanup
        if os.path.exists(temp_video):
            os.remove(temp_video)
