# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create tests for cultural products API endpoints
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

"""
文创产品管理API测试模块

测试内容:
- 产品列表 (GET /api/cultural-products/)
- 产品详情 (GET /api/cultural-products/{product_id})
- 产品创建 (POST /api/cultural-products/) - admin only
- 产品更新 (PUT /api/cultural-products/{product_id}) - admin only
- 产品删除 (DELETE /api/cultural-products/{product_id}) - admin only
"""

from app.models import CulturalProduct
from fastapi.testclient import TestClient


class TestCulturalProductList:
    """文创产品列表接口测试"""

    def test_list_products_empty(self, client: TestClient, auth_headers: dict):
        """测试空列表"""
        response = client.get("/api/cultural-products/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_products_with_data(
        self, client: TestClient, auth_headers: dict, test_cultural_product: CulturalProduct
    ):
        """测试有数据列表"""
        response = client.get("/api/cultural-products/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_products_filter_by_status(
        self, client: TestClient, auth_headers: dict, test_cultural_product: CulturalProduct
    ):
        """测试按状态筛选"""
        response = client.get(
            "/api/cultural-products/?status=active", headers=auth_headers
        )
        assert response.status_code == 200
        for item in response.json():
            assert item["status"] == "active"

    def test_list_products_without_auth(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/cultural-products/")
        assert response.status_code == 401


class TestCulturalProductDetail:
    """文创产品详情接口测试"""

    def test_get_product_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_cultural_product: CulturalProduct,
    ):
        """测试获取产品详情"""
        response = client.get(
            f"/api/cultural-products/{test_cultural_product.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_cultural_product.id
        assert data["code"] == "001"

    def test_get_product_not_found(self, client: TestClient, auth_headers: dict):
        """测试产品不存在"""
        response = client.get("/api/cultural-products/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_product_without_auth(
        self, client: TestClient, test_cultural_product: CulturalProduct
    ):
        """测试未授权访问"""
        response = client.get(f"/api/cultural-products/{test_cultural_product.id}")
        assert response.status_code == 401


class TestCulturalProductCreate:
    """Test Cultural Product Create (admin only)"""

    def test_create_product_duplicate_code(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_cultural_product: CulturalProduct,
    ):
        """测试编号重复"""
        response = client.post(
            "/api/cultural-products/",
            headers=admin_auth_headers,
            json={"code": "001", "name": "新产品"},
        )
        assert response.status_code == 400
        assert "已被使用" in response.json()["detail"]

    def test_create_product_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
    ):
        """测试创建产品成功"""
        response = client.post(
            "/api/cultural-products/",
            headers=admin_auth_headers,
            json={"code": "099", "name": "测试产品", "status": "active"},
        )
        assert response.status_code == 201
        assert response.json()["code"] == "099"

    def test_create_product_operator_forbidden(
        self, client: TestClient, auth_headers: dict
    ):
        """测试普通用户无权创建"""
        response = client.post(
            "/api/cultural-products/",
            headers=auth_headers,
            json={"code": "088", "name": "新产品"},
        )
        assert response.status_code == 403

    def test_create_product_without_auth(self, client: TestClient):
        """测试未授权创建"""
        response = client.post(
            "/api/cultural-products/",
            json={"code": "C99", "name": "新产品"},
        )
        assert response.status_code == 401


class TestCulturalProductUpdate:
    """Test Cultural Product Update (admin only)"""

    def test_update_product_not_found(self, client: TestClient, admin_auth_headers: dict):
        """测试更新不存在的产品"""
        response = client.put(
            "/api/cultural-products/99999",
            headers=admin_auth_headers,
            json={"name": "新名称"},
        )
        assert response.status_code == 404

    def test_update_product_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_cultural_product: CulturalProduct,
    ):
        """测试更新产品成功"""
        response = client.put(
            f"/api/cultural-products/{test_cultural_product.id}",
            headers=admin_auth_headers,
            json={"name": "更新后的名称"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "更新后的名称"

    def test_update_product_operator_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        test_cultural_product: CulturalProduct,
    ):
        """测试普通用户无权更新"""
        response = client.put(
            f"/api/cultural-products/{test_cultural_product.id}",
            headers=auth_headers,
            json={"name": "新名称"},
        )
        assert response.status_code == 403

    def test_update_product_without_auth(
        self, client: TestClient, test_cultural_product: CulturalProduct
    ):
        """测试未授权更新"""
        response = client.put(
            f"/api/cultural-products/{test_cultural_product.id}",
            json={"name": "新名称"},
        )
        assert response.status_code == 401


class TestCulturalProductDelete:
    """Test Cultural Product Delete (admin only)"""

    def test_delete_product_success(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        test_cultural_product: CulturalProduct,
    ):
        """测试删除产品成功"""
        response = client.delete(
            f"/api/cultural-products/{test_cultural_product.id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 204

    def test_delete_product_not_found(
        self, client: TestClient, admin_auth_headers: dict
    ):
        """测试删除不存在的产品"""
        response = client.delete(
            "/api/cultural-products/99999", headers=admin_auth_headers
        )
        assert response.status_code == 404

    def test_delete_product_operator_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        test_cultural_product: CulturalProduct,
    ):
        """测试普通用户无权删除"""
        response = client.delete(
            f"/api/cultural-products/{test_cultural_product.id}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_delete_product_without_auth(
        self, client: TestClient, test_cultural_product: CulturalProduct
    ):
        """测试未授权删除"""
        response = client.delete(
            f"/api/cultural-products/{test_cultural_product.id}"
        )
        assert response.status_code == 401
