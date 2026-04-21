# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create NFC API tests
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

"""
NFC公开接口API测试模块

测试内容:
- NFC标签播放 (GET /api/nfc/{code}/play)
"""

from datetime import UTC, datetime, timedelta

from app.models import CulturalProduct, NFCTag, User, Video
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestNFCPlay:
    """NFC播放接口测试"""

    def test_nfc_play_success(
        self,
        client: TestClient,
        test_nfc_tag: NFCTag,
        test_video: Video,
        test_cultural_product: CulturalProduct,
    ):
        """测试NFC播放成功"""
        response = client.get(f"/api/nfc/{test_nfc_tag.url_code}/play")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == test_video.name
        assert data["cultural_product_name"] == test_cultural_product.name
        assert data["duration"] == test_video.duration
        assert "video_url" in data

    def test_nfc_play_tag_not_found(self, client: TestClient):
        """测试NFC标签不存在"""
        response = client.get("/api/nfc/NONEXISTENT/play")
        assert response.status_code == 404
        assert "NFC标签不存在" in response.json()["detail"]

    def test_nfc_play_tag_pending_approval(
        self,
        client: TestClient,
        test_db: Session,
        test_video: Video,
        test_cultural_product: CulturalProduct,
        _test_user: User,
    ):
        """测试NFC标签待审批状态"""
        # Create pending tag
        pending_tag = NFCTag(
            url_code="PENDING123",
            video_id=test_video.id,
            cultural_product_id=test_cultural_product.id,
            status="active",
            approval_status="pending",
            created_by=_test_user.id,
        )
        test_db.add(pending_tag)
        test_db.commit()

        response = client.get("/api/nfc/PENDING123/play")
        assert response.status_code == 403
        assert "待审批或已驳回" in response.json()["detail"]

    def test_nfc_play_tag_rejected(
        self,
        client: TestClient,
        test_db: Session,
        test_video: Video,
        test_cultural_product: CulturalProduct,
        _test_user: User,
    ):
        """测试NFC标签已驳回状态"""
        # Create rejected tag
        rejected_tag = NFCTag(
            url_code="REJECTED123",
            video_id=test_video.id,
            cultural_product_id=test_cultural_product.id,
            status="active",
            approval_status="rejected",
            created_by=_test_user.id,
        )
        test_db.add(rejected_tag)
        test_db.commit()

        response = client.get("/api/nfc/REJECTED123/play")
        assert response.status_code == 403
        assert "待审批或已驳回" in response.json()["detail"]

    def test_nfc_play_tag_expired(
        self,
        client: TestClient,
        test_db: Session,
        test_video: Video,
        test_cultural_product: CulturalProduct,
        _test_user: User,
    ):
        """测试NFC标签已过期"""
        # Create expired tag
        expired_tag = NFCTag(
            url_code="EXPIRED123",
            video_id=test_video.id,
            cultural_product_id=test_cultural_product.id,
            status="active",
            approval_status="approved",
            created_by=_test_user.id,
            expires_at=datetime.now(UTC).date() - timedelta(days=1),  # Yesterday
        )
        test_db.add(expired_tag)
        test_db.commit()

        response = client.get("/api/nfc/EXPIRED123/play")
        assert response.status_code == 403
        assert "已过期" in response.json()["detail"]

    def test_nfc_play_video_not_found(
        self,
        client: TestClient,
        test_db: Session,
        test_cultural_product: CulturalProduct,
        _test_user: User,
    ):
        """测试关联视频不存在"""
        # Create tag with non-existent video (video_id=9999)
        orphan_tag = NFCTag(
            url_code="ORPHAN123",
            video_id=9999,  # Non-existent
            cultural_product_id=test_cultural_product.id,
            status="active",
            approval_status="approved",
            created_by=_test_user.id,
        )
        test_db.add(orphan_tag)
        test_db.commit()

        response = client.get("/api/nfc/ORPHAN123/play")
        assert response.status_code == 404
        assert "关联视频不存在" in response.json()["detail"]

    def test_nfc_play_cultural_product_not_found(
        self,
        client: TestClient,
        test_db: Session,
        test_video: Video,
        _test_user: User,
    ):
        """测试关联文创品不存在"""
        # Create tag with non-existent cultural product
        orphan_tag = NFCTag(
            url_code="ORPHAN456",
            video_id=test_video.id,
            cultural_product_id=9999,  # Non-existent
            status="active",
            approval_status="approved",
            created_by=_test_user.id,
        )
        test_db.add(orphan_tag)
        test_db.commit()

        response = client.get("/api/nfc/ORPHAN456/play")
        assert response.status_code == 404
        assert "关联文创品不存在" in response.json()["detail"]

    def test_nfc_play_records_click(
        self,
        client: TestClient,
        test_nfc_tag: NFCTag,
        test_db: Session,
    ):
        """测试NFC播放记录点击"""
        # Get initial click count
        initial_clicks = test_db.query(NFCTag).filter(NFCTag.id == test_nfc_tag.id).first().clicks  # noqa: F841

        response = client.get(f"/api/nfc/{test_nfc_tag.url_code}/play")
        assert response.status_code == 200

        # Verify click was recorded
        updated_clicks = test_db.query(NFCTag).filter(NFCTag.id == test_nfc_tag.id).first().clicks
        assert len(updated_clicks) == 1

    def test_nfc_play_with_visitor_id(
        self,
        client: TestClient,
        test_nfc_tag: NFCTag,
    ):
        """测试带visitor_id参数的NFC播放"""
        response = client.get(
            f"/api/nfc/{test_nfc_tag.url_code}/play",
            params={"visitor_id": "test_visitor_123"},
        )
        assert response.status_code == 200
