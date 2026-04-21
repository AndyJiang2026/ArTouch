# AI-ASSISTED: Yes
# AI-TOOL: Hermes Agent
# PROMPT: Create comprehensive NFC tag full workflow test
# DATE: 2026-04-21
# ENGINEER: Hermes Agent
# RISK-LEVEL: P2

"""
完整NFC标签流程测试：
- 创建标签
- 编辑标签
- 审批流程（批准/驳回）
- 审批后状态变更检查
- 删除标签
- NFC触碰播放接口
"""

import pytest
from app.models import SKU, CulturalProduct, NFCTag, TagClick, Video
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def cultural_product(db_session: Session) -> CulturalProduct:
    """创建测试文创品。"""
    product = CulturalProduct(
        code="WF001",
        name="测试文创品",
        status="active",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def video(db_session: Session) -> Video:
    """创建测试视频。"""
    video = Video(
        code="VD001",
        name="测试视频",
        status="active",
        file_path="/videos/test.mp4",
        duration=120.5,
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    return video


@pytest.fixture
def video2(db_session: Session) -> Video:
    """创建第二个测试视频用于编辑测试。"""
    video = Video(
        code="VD002",
        name="测试视频2",
        status="active",
        file_path="/videos/test2.mp4",
        duration=90.0,
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    return video


@pytest.fixture
def sku(db_session: Session, cultural_product: CulturalProduct) -> SKU:
    """创建测试SKU。"""
    sku = SKU(
        code="001",
        name="测试SKU",
        cultural_product_id=cultural_product.id,
    )
    db_session.add(sku)
    db_session.commit()
    db_session.refresh(sku)
    return sku


# ============================================================
# 1. 创建 + 编辑完整流程测试
# ============================================================
class TestNFCTagEditWorkflow:
    """NFC标签编辑流程测试。"""

    def test_create_then_update_video(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
        video2: Video,
    ):
        """测试：创建标签 -> 审批 -> 编辑视频关联 -> 验证URL码更新。"""
        # Step 1: 创建标签
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        assert create_resp.status_code == 201
        tag_data = create_resp.json()
        tag_id = tag_data["id"]
        original_url_code = tag_data["url_code"]
        assert tag_data["approval_status"] == "pending"
        assert "WF001_VD001" == original_url_code

        # Step 2: 审批通过
        approve_resp = client.post(
            f"/api/nfc-tags/{tag_id}/approve",
            headers=auth_headers_admin,
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["approval_status"] == "approved"

        # Step 3: 编辑视频关联
        update_resp = client.put(
            f"/api/nfc-tags/{tag_id}",
            headers=auth_headers_operator,
            json={"video_id": video2.id},
        )
        assert update_resp.status_code == 200
        updated_data = update_resp.json()
        assert updated_data["video_id"] == video2.id
        # URL码应该更新为新的视频code
        assert "WF001_VD002" == updated_data["url_code"]
        assert updated_data["url_code"] != original_url_code

    def test_update_status_toggle(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：编辑标签状态（active <-> inactive）。"""
        # 创建标签
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]
        assert create_resp.json()["status"] == "active"

        # 设置为 inactive
        update_resp = client.put(
            f"/api/nfc-tags/{tag_id}",
            headers=auth_headers_operator,
            json={"status": "inactive"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "inactive"

        # 恢复为 active
        update_resp2 = client.put(
            f"/api/nfc-tags/{tag_id}",
            headers=auth_headers_operator,
            json={"status": "active"},
        )
        assert update_resp2.status_code == 200
        assert update_resp2.json()["status"] == "active"

    def test_update_nonexistent_tag(
        self,
        client: TestClient,
        auth_headers_operator: dict,
    ):
        """测试：编辑不存在的标签返回404。"""
        resp = client.put(
            "/api/nfc-tags/99999",
            headers=auth_headers_operator,
            json={"status": "inactive"},
        )
        assert resp.status_code == 404


# ============================================================
# 2. 审批流程完整测试
# ============================================================
class TestNFCTagApprovalWorkflow:
    """NFC标签审批流程测试。"""

    def test_full_approval_lifecycle(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试完整审批生命周期：创建(pending) -> 审批(approved) -> 验证状态。"""
        # 创建标签，初始状态为 pending
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        assert create_resp.status_code == 201
        tag_id = create_resp.json()["id"]
        assert create_resp.json()["approval_status"] == "pending"
        assert create_resp.json()["approved_by"] is None
        assert create_resp.json()["approved_at"] is None

        # 审批通过
        approve_resp = client.post(
            f"/api/nfc-tags/{tag_id}/approve",
            headers=auth_headers_admin,
        )
        assert approve_resp.status_code == 200
        data = approve_resp.json()
        assert data["approval_status"] == "approved"
        assert data["approved_by"] is not None
        assert data["approved_at"] is not None

        # 验证数据库中的状态
        tag = db_session.query(NFCTag).filter(NFCTag.id == tag_id).first()
        assert tag.approval_status == "approved"
        assert tag.approved_by is not None
        assert tag.approved_at is not None

    def test_reject_workflow(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试驳回流程：创建(pending) -> 驳回(rejected) -> 验证状态。"""
        # 创建标签
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]

        # 驳回
        reject_resp = client.post(
            f"/api/nfc-tags/{tag_id}/reject",
            headers=auth_headers_admin,
        )
        assert reject_resp.status_code == 200
        data = reject_resp.json()
        assert data["approval_status"] == "rejected"
        assert data["approved_by"] is not None
        assert data["approved_at"] is not None

        # 验证数据库状态
        tag = db_session.query(NFCTag).filter(NFCTag.id == tag_id).first()
        assert tag.approval_status == "rejected"

    def test_double_approve_rejected(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：重复审批已审批的标签应返回400。"""
        # 创建并审批
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]

        # 第一次审批
        resp1 = client.post(
            f"/api/nfc-tags/{tag_id}/approve",
            headers=auth_headers_admin,
        )
        assert resp1.status_code == 200

        # 第二次审批应失败
        resp2 = client.post(
            f"/api/nfc-tags/{tag_id}/approve",
            headers=auth_headers_admin,
        )
        assert resp2.status_code == 400
        assert "已审批" in resp2.json()["detail"]

    def test_double_reject_rejected(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：重复驳回已驳回的标签应返回400。"""
        # 创建并驳回
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]

        # 第一次驳回
        resp1 = client.post(
            f"/api/nfc-tags/{tag_id}/reject",
            headers=auth_headers_admin,
        )
        assert resp1.status_code == 200

        # 第二次驳回应失败
        resp2 = client.post(
            f"/api/nfc-tags/{tag_id}/reject",
            headers=auth_headers_admin,
        )
        assert resp2.status_code == 400
        assert "已驳回" in resp2.json()["detail"]

    def test_approve_requires_admin_not_operator(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：operator不能审批标签。"""
        # 创建标签（用operator）
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]

        # operator尝试审批应被拒绝
        resp = client.post(
            f"/api/nfc-tags/{tag_id}/approve",
            headers=auth_headers_operator,
        )
        assert resp.status_code == 403

    def test_approve_nonexistent_tag(
        self,
        client: TestClient,
        auth_headers_admin: dict,
    ):
        """测试：审批不存在的标签返回404。"""
        resp = client.post(
            "/api/nfc-tags/99999/approve",
            headers=auth_headers_admin,
        )
        assert resp.status_code == 404


# ============================================================
# 3. 审批后状态变更对播放的影响
# ============================================================
class TestApprovalStatusPlayImpact:
    """审批状态对NFC播放的影响测试。"""

    def test_pending_tag_cannot_play(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：pending状态的标签不能播放。"""
        # 创建标签（pending状态）
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        url_code = create_resp.json()["url_code"]

        # 尝试播放应返回403
        play_resp = client.get(f"/api/nfc/{url_code}/play")
        assert play_resp.status_code == 403
        assert "待审批" in play_resp.json()["detail"] or "审批" in play_resp.json()["detail"]

    def test_rejected_tag_cannot_play(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：rejected状态的标签不能播放。"""
        # 创建并驳回
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]
        url_code = create_resp.json()["url_code"]

        # 驳回
        client.post(f"/api/nfc-tags/{tag_id}/reject", headers=auth_headers_admin)

        # 尝试播放应返回403
        play_resp = client.get(f"/api/nfc/{url_code}/play")
        assert play_resp.status_code == 403

    def test_approved_tag_can_play(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：approved状态的标签可以正常播放。"""
        # 创建并审批
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]
        url_code = create_resp.json()["url_code"]

        # 审批
        client.post(f"/api/nfc-tags/{tag_id}/approve", headers=auth_headers_admin)

        # 播放应成功
        play_resp = client.get(f"/api/nfc/{url_code}/play")
        assert play_resp.status_code == 200
        data = play_resp.json()
        assert "video_url" in data
        assert "title" in data
        assert "cultural_product_name" in data
        assert data["cultural_product_name"] == cultural_product.name

    def test_play_records_click(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：播放时记录点击数据。"""
        # 创建并审批
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]
        url_code = create_resp.json()["url_code"]
        client.post(f"/api/nfc-tags/{tag_id}/approve", headers=auth_headers_admin)

        # 播放前点击数为0
        clicks_before = db_session.query(TagClick).filter(TagClick.tag_id == tag_id).count()
        assert clicks_before == 0

        # 播放
        play_resp = client.get(f"/api/nfc/{url_code}/play?visitor_id=test_visitor_123")
        assert play_resp.status_code == 200

        # 播放后点击数应为1
        clicks_after = db_session.query(TagClick).filter(TagClick.tag_id == tag_id).count()
        assert clicks_after == 1

        # 验证点击记录内容
        click = db_session.query(TagClick).filter(TagClick.tag_id == tag_id).first()
        assert click.visitor_id == "test_visitor_123"
        assert click.tag_id == tag_id

    def test_multiple_plays_increment_clicks(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：多次播放递增点击数。"""
        # 创建并审批
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]
        url_code = create_resp.json()["url_code"]
        client.post(f"/api/nfc-tags/{tag_id}/approve", headers=auth_headers_admin)

        # 播放3次
        for i in range(3):
            resp = client.get(f"/api/nfc/{url_code}/play?visitor_id=visitor_{i}")
            assert resp.status_code == 200

        # 验证点击数
        clicks = db_session.query(TagClick).filter(TagClick.tag_id == tag_id).count()
        assert clicks == 3


# ============================================================
# 4. 删除流程测试
# ============================================================
class TestNFCTagDeleteWorkflow:
    """NFC标签删除流程测试。"""

    def test_delete_approved_tag(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：删除已审批的标签。"""
        # 创建并审批
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]
        url_code = create_resp.json()["url_code"]
        client.post(f"/api/nfc-tags/{tag_id}/approve", headers=auth_headers_admin)

        # 删除（需要admin）
        delete_resp = client.delete(
            f"/api/nfc-tags/{tag_id}",
            headers=auth_headers_admin,
        )
        assert delete_resp.status_code == 204

        # 验证标签已被删除
        tag = db_session.query(NFCTag).filter(NFCTag.id == tag_id).first()
        assert tag is None

        # 播放已删除的标签应返回404
        play_resp = client.get(f"/api/nfc/{url_code}/play")
        assert play_resp.status_code == 404

    def test_delete_pending_tag(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：删除pending状态的标签。"""
        # 创建（pending状态）
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]

        # 删除
        delete_resp = client.delete(
            f"/api/nfc-tags/{tag_id}",
            headers=auth_headers_admin,
        )
        assert delete_resp.status_code == 204

        # 验证已删除
        tag = db_session.query(NFCTag).filter(NFCTag.id == tag_id).first()
        assert tag is None

    def test_delete_operator_forbidden(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：operator不能删除标签。"""
        # 创建标签
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]

        # operator尝试删除应被拒绝
        delete_resp = client.delete(
            f"/api/nfc-tags/{tag_id}",
            headers=auth_headers_operator,
        )
        assert delete_resp.status_code == 403

    def test_delete_nonexistent_tag(
        self,
        client: TestClient,
        auth_headers_admin: dict,
    ):
        """测试：删除不存在的标签返回404。"""
        resp = client.delete(
            "/api/nfc-tags/99999",
            headers=auth_headers_admin,
        )
        assert resp.status_code == 404


# ============================================================
# 5. NFC触碰播放接口完整测试
# ============================================================
class TestNFCPlayEndpoint:
    """NFC触碰播放接口测试。"""

    def test_play_nonexistent_code(
        self,
        client: TestClient,
    ):
        """测试：播放不存在的URL码返回404。"""
        resp = client.get("/api/nfc/NONEXISTENT_CODE/play")
        assert resp.status_code == 404
        assert "不存在" in resp.json()["detail"]

    def test_play_returns_correct_video_info(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：播放返回正确的视频信息。"""
        # 创建并审批
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]
        url_code = create_resp.json()["url_code"]
        client.post(f"/api/nfc-tags/{tag_id}/approve", headers=auth_headers_admin)

        # 播放
        play_resp = client.get(f"/api/nfc/{url_code}/play")
        assert play_resp.status_code == 200
        data = play_resp.json()

        # 验证返回字段
        assert "video_url" in data
        assert "title" in data
        assert "cultural_product_name" in data
        assert data["title"] == video.name
        assert data["cultural_product_name"] == cultural_product.name
        assert data["duration"] == video.duration

    def test_play_no_auth_required(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """测试：播放接口不需要认证（公开接口）。"""
        # 创建并审批
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]
        url_code = create_resp.json()["url_code"]
        client.post(f"/api/nfc-tags/{tag_id}/approve", headers=auth_headers_admin)

        # 不带认证头访问应成功
        play_resp = client.get(f"/api/nfc/{url_code}/play")
        assert play_resp.status_code == 200


# ============================================================
# 6. 端到端完整流程测试
# ============================================================
class TestEndToEndWorkflow:
    """端到端完整流程测试。"""

    def test_full_lifecycle_create_approve_play_update_play_delete(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        auth_headers_user: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
        video2: Video,
    ):
        """
        完整生命周期测试：
        1. Operator创建标签（pending）
        2. 验证pending状态不能播放
        3. Admin审批通过
        4. 验证approved状态可以播放
        5. Operator编辑标签（更换视频）
        6. 验证编辑后仍可播放
        7. 验证普通用户不能创建标签
        8. Admin删除标签
        9. 验证删除后不能播放
        """
        # Step 1: Operator创建标签
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        assert create_resp.status_code == 201
        tag_id = create_resp.json()["id"]
        url_code = create_resp.json()["url_code"]
        assert create_resp.json()["approval_status"] == "pending"

        # Step 2: 普通用户不能创建标签
        user_create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_user,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        assert user_create_resp.status_code == 403

        # Step 3: pending状态不能播放
        play_pending = client.get(f"/api/nfc/{url_code}/play")
        assert play_pending.status_code == 403

        # Step 4: Admin审批通过
        approve_resp = client.post(
            f"/api/nfc-tags/{tag_id}/approve",
            headers=auth_headers_admin,
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["approval_status"] == "approved"

        # Step 5: approved状态可以播放
        play_approved = client.get(f"/api/nfc/{url_code}/play")
        assert play_approved.status_code == 200
        assert play_approved.json()["title"] == video.name

        # Step 6: Operator编辑标签
        update_resp = client.put(
            f"/api/nfc-tags/{tag_id}",
            headers=auth_headers_operator,
            json={"video_id": video2.id},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["video_id"] == video2.id

        # Step 7: 编辑后仍可播放，且视频信息已更新
        play_updated = client.get(f"/api/nfc/{update_resp.json()['url_code']}/play")
        assert play_updated.status_code == 200
        assert play_updated.json()["title"] == video2.name

        # Step 8: Operator不能删除标签
        operator_delete = client.delete(
            f"/api/nfc-tags/{tag_id}",
            headers=auth_headers_operator,
        )
        assert operator_delete.status_code == 403

        # Step 9: Admin删除标签
        delete_resp = client.delete(
            f"/api/nfc-tags/{tag_id}",
            headers=auth_headers_admin,
        )
        assert delete_resp.status_code == 204

        # Step 10: 删除后不能播放
        play_deleted = client.get(f"/api/nfc/{url_code}/play")
        assert play_deleted.status_code == 404

    def test_reject_then_cannot_play(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """
        测试驳回流程：
        1. 创建标签
        2. Admin驳回
        3. 验证驳回后不能播放
        """
        # 创建
        create_resp = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        tag_id = create_resp.json()["id"]
        url_code = create_resp.json()["url_code"]

        # 驳回
        reject_resp = client.post(
            f"/api/nfc-tags/{tag_id}/reject",
            headers=auth_headers_admin,
        )
        assert reject_resp.status_code == 200
        assert reject_resp.json()["approval_status"] == "rejected"

        # 驳回后不能播放
        play_resp = client.get(f"/api/nfc/{url_code}/play")
        assert play_resp.status_code == 403
