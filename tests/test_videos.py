# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create tests for videos API endpoints
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

"""
视频管理API测试模块

测试内容:
- 视频列表 (GET /api/videos/)
- 视频详情 (GET /api/videos/{video_id})
- 视频上传 (POST /api/videos/upload)
- 视频更新 (PUT /api/videos/{video_id})
- 视频删除 (DELETE /api/videos/{video_id})
"""

from app.models import Video
from fastapi.testclient import TestClient


class TestVideoList:
    """视频列表接口测试"""

    def test_list_videos_empty(self, client: TestClient, auth_headers: dict):
        """测试空列表"""
        response = client.get("/api/videos/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_videos_with_data(
        self, client: TestClient, auth_headers: dict, test_video: Video
    ):
        """测试有数据列表"""
        response = client.get("/api/videos/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_videos_filter_by_status(
        self, client: TestClient, auth_headers: dict, test_video: Video
    ):
        """测试按状态筛选"""
        response = client.get("/api/videos/?status=ready", headers=auth_headers)
        assert response.status_code == 200
        for item in response.json():
            assert item["status"] == "ready"

    def test_list_videos_without_auth(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/videos/")
        assert response.status_code == 401


class TestVideoDetail:
    """视频详情接口测试"""

    def test_get_video_success(
        self, client: TestClient, auth_headers: dict, test_video: Video
    ):
        """测试获取视频详情"""
        response = client.get(f"/api/videos/{test_video.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_video.id
        assert data["code"] == "T01"

    def test_get_video_not_found(self, client: TestClient, auth_headers: dict):
        """测试视频不存在"""
        response = client.get("/api/videos/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_video_without_auth(self, client: TestClient, test_video: Video):
        """测试未授权访问"""
        response = client.get(f"/api/videos/{test_video.id}")
        assert response.status_code == 401


class TestVideoUpdate:
    """视频更新接口测试"""

    def test_update_video_not_found(self, client: TestClient, auth_headers: dict):
        """测试更新不存在的视频"""
        response = client.put(
            "/api/videos/99999",
            headers=auth_headers,
            json={"name": "新名称"},
        )
        assert response.status_code == 404

    def test_update_video_success(
        self, client: TestClient, auth_headers: dict, test_video: Video
    ):
        """测试更新视频成功"""
        response = client.put(
            f"/api/videos/{test_video.id}",
            headers=auth_headers,
            json={"name": "更新后的名称"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "更新后的名称"

    def test_update_video_associate_product(
        self,
        client: TestClient,
        auth_headers: dict,
        test_video: Video,
        test_cultural_product,
    ):
        """测试关联文创产品"""
        response = client.put(
            f"/api/videos/{test_video.id}",
            headers=auth_headers,
            json={"cultural_product_ids": [test_cultural_product.id]},
        )
        assert response.status_code == 200

    def test_update_video_invalid_product(
        self,
        client: TestClient,
        auth_headers: dict,
        test_video: Video,
    ):
        """测试关联无效产品ID"""
        response = client.put(
            f"/api/videos/{test_video.id}",
            headers=auth_headers,
            json={"cultural_product_ids": [99999]},
        )
        assert response.status_code == 400
        assert "无效" in response.json()["detail"]

    def test_update_video_without_auth(self, client: TestClient, test_video: Video):
        """测试未授权更新"""
        response = client.put(
            f"/api/videos/{test_video.id}",
            json={"name": "新名称"},
        )
        assert response.status_code == 401


class TestVideoDelete:
    """视频删除接口测试"""

    def test_delete_video_success(
        self, client: TestClient, auth_headers: dict, test_video: Video
    ):
        """测试删除视频成功"""
        response = client.delete(
            f"/api/videos/{test_video.id}", headers=auth_headers
        )
        assert response.status_code == 204

    def test_delete_video_not_found(self, client: TestClient, auth_headers: dict):
        """测试删除不存在的视频"""
        response = client.delete("/api/videos/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_video_without_auth(self, client: TestClient, test_video: Video):
        """测试未授权删除"""
        response = client.delete(f"/api/videos/{test_video.id}")
        assert response.status_code == 401
