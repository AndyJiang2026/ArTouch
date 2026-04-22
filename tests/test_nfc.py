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


class TestNFCVerify:
    """NFC验伪接口测试"""

    def _derive_key_material(self, uid: str) -> str:
        """Derive key material from UID (matches server logic)."""
        import hashlib
        import hmac
        master_key = b"test_master_key_for_nfc"
        uid_bytes = uid.encode('utf-8')
        mac = hmac.new(master_key, uid_bytes, hashlib.sha256)
        return mac.hexdigest()

    def _compute_signature(self, key_material: str, uid: str, counter: int) -> str:
        import hashlib
        """Compute signature (matches server logic)."""
        import hmac
        key_bytes = key_material.encode('utf-8')
        message = f"{uid.lower()}{counter}".encode('utf-8')
        sig_mac = hmac.new(key_bytes, message, hashlib.sha256)
        return sig_mac.hexdigest()

    def _register_tag(self, test_db, uid: str, counter: int = 1, is_active: int = 1, product_name: str = None):
        """Helper: Register a tag and return it."""
        from app.models import NfcTagSecure
        key_material = self._derive_key_material(uid)
        signature = self._compute_signature(key_material, uid, counter)
        
        tag = NfcTagSecure(
            uid=uid.lower(),
            key_material=key_material,
            signature=signature,
            counter=counter,
            is_active=is_active,
            product_name=product_name,
        )
        test_db.add(tag)
        test_db.commit()
        test_db.refresh(tag)
        return tag

    def test_verify_tag_not_found(self, client: TestClient):
        """测试标签未注册"""
        response = client.post(
            "/api/nfc/verify",
            json={
                "uid": "041234567890AB",
                "signature": "a" * 64,
                "counter": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_authentic"] is False
        assert data["result"] == "tag_not_found"

    def test_verify_success(self, client: TestClient, test_db: Session):
        """测试验伪成功"""
        uid = "041234567890ab"
        tag = self._register_tag(test_db, uid, counter=1, product_name="Test Product")
        
        # Compute signature with counter=1
        signature = self._compute_signature(tag.key_material, uid, counter=1)
        
        response = client.post(
            "/api/nfc/verify",
            json={
                "uid": uid,
                "signature": signature,
                "counter": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_authentic"] is True
        assert data["result"] == "ok"
        assert data["product_name"] == "Test Product"
        assert data["is_first_verify"] is True

    def test_verify_signature_invalid(self, client: TestClient, test_db: Session):
        """测试签名无效 - 提交错误签名"""
        uid = "041234567890ab"
        tag = self._register_tag(test_db, uid, counter=1)
        
        # Submit wrong signature
        wrong_sig = "a" * 64
        response = client.post(
            "/api/nfc/verify",
            json={
                "uid": uid,
                "signature": wrong_sig,
                "counter": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_authentic"] is False
        assert data["result"] == "signature_invalid"

    def test_verify_counter_replay(self, client: TestClient, test_db: Session):
        """测试计数器重放攻击"""
        uid = "041234567890ac"
        # Register with counter=5
        tag = self._register_tag(test_db, uid, counter=5)
        
        # Compute signature with counter=5 (stored counter) so sig check passes
        signature = self._compute_signature(tag.key_material, uid, counter=5)
        
        # Submit counter=3 (lower than stored)
        response = client.post(
            "/api/nfc/verify",
            json={
                "uid": uid,
                "signature": signature,
                "counter": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_authentic"] is False
        assert data["result"] == "counter_replay"

    def test_verify_tag_revoked(self, client: TestClient, test_db: Session):
        """测试标签已吊销"""
        uid = "041234567890ad"
        tag = self._register_tag(test_db, uid, counter=1, is_active=0)
        
        signature = self._compute_signature(tag.key_material, uid, counter=1)
        
        response = client.post(
            "/api/nfc/verify",
            json={
                "uid": uid,
                "signature": signature,
                "counter": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_authentic"] is False
        assert data["result"] == "tag_revoked"

    def test_verify_logs_created(self, client: TestClient, test_db: Session):
        """测试验证日志创建"""
        from app.models import VerificationLog

        uid = "041234567890ae"
        tag = self._register_tag(test_db, uid, counter=1)
        
        signature = self._compute_signature(tag.key_material, uid, counter=1)
        
        response = client.post(
            "/api/nfc/verify",
            json={
                "uid": uid,
                "signature": signature,
                "counter": 1,
            },
        )
        assert response.status_code == 200

        # Check verification log was created
        log = test_db.query(VerificationLog).filter(VerificationLog.uid == uid).first()
        assert log is not None
        assert log.is_success == 1
        assert log.result == "ok"

    def test_verify_uid_case_insensitive(self, client: TestClient, test_db: Session):
        """测试UID大小写不敏感"""
        uid = "041234567890AF"
        tag = self._register_tag(test_db, uid.lower(), counter=1)
        
        signature = self._compute_signature(tag.key_material, uid.lower(), counter=1)
        
        # Submit with uppercase
        response = client.post(
            "/api/nfc/verify",
            json={
                "uid": "041234567890AF",
                "signature": signature,
                "counter": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_authentic"] is True

    def test_verify_invalid_uid_format(self, client: TestClient):
        """测试无效UID格式"""
        response = client.post(
            "/api/nfc/verify",
            json={
                "uid": "invalid",
                "signature": "a" * 64,
                "counter": 1,
            },
        )
        assert response.status_code == 422  # Validation error

    def test_verify_invalid_signature_format(self, client: TestClient):
        """测试无效签名格式"""
        response = client.post(
            "/api/nfc/verify",
            json={
                "uid": "041234567890AB",
                "signature": "not_hex",
                "counter": 1,
            },
        )
        assert response.status_code == 422  # Validation error

    def test_verify_counter_must_be_positive(self, client: TestClient):
        """测试计数器必须为正数"""
        response = client.post(
            "/api/nfc/verify",
            json={
                "uid": "041234567890AB",
                "signature": "a" * 64,
                "counter": 0,
            },
        )
        assert response.status_code == 422  # Validation error
