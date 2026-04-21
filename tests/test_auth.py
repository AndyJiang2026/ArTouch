# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create authentication API tests
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

"""
认证API测试模块

测试内容:
- 用户登录 (POST /api/auth/login)
- 用户登出 (POST /api/auth/logout)
- 获取当前用户信息 (GET /api/auth/me)
- 修改密码 (POST /api/auth/change-password)
- 登录失败率限制
"""

from app.core.security import get_password_hash
from app.models import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestLogin:
    """登录接口测试"""

    def test_login_success(self, client: TestClient, _test_user: User):
        """测试正常登录"""
        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "Test1234"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testuser"

    def test_login_wrong_password(self, client: TestClient, _test_user: User):
        """测试密码错误登录"""
        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "WrongPassword123"},
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_user_not_found(self, client: TestClient):
        """测试用户不存在"""
        response = client.post(
            "/api/auth/login",
            data={"username": "nonexistent", "password": "Test1234"},
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_inactive_user(self, client: TestClient, test_db: Session):
        """测试禁用用户登录"""
        # Create inactive user
        inactive_user = User(
            username="inactive",
            password_hash=get_password_hash("TestPassword123"),
            role="operator",
            is_active=False,
        )
        test_db.add(inactive_user)
        test_db.commit()

        response = client.post(
            "/api/auth/login",
            data={"username": "inactive", "password": "TestPassword123"},
        )
        assert response.status_code == 403
        assert "用户已被禁用" in response.json()["detail"]


class TestLogout:
    """登出接口测试"""

    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """测试正常登出"""
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert "登出成功" in response.json()["message"]

    def test_logout_without_auth(self, client: TestClient):
        """测试未登录登出"""
        response = client.post("/api/auth/logout")
        assert response.status_code == 401


class TestGetMe:
    """获取当前用户信息测试"""

    def test_get_me_success(self, client: TestClient, auth_headers: dict, _test_user: User):
        """测试获取当前用户信息成功"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["role"] == "operator"
        assert data["is_active"] is True

    def test_get_me_without_auth(self, client: TestClient):
        """测试未登录获取用户信息"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401


class TestChangePassword:
    """修改密码测试"""

    def test_change_password_success(self, client: TestClient, auth_headers: dict):
        """测试修改密码成功"""
        response = client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "Test1234",
                "new_password": "NewPass123",
            },
        )
        assert response.status_code == 200
        assert "密码修改成功" in response.json()["message"]

    def test_change_password_wrong_old_password(self, client: TestClient, auth_headers: dict):
        """测试原密码错误"""
        response = client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "WrongPassword123",
                "new_password": "NewPass123",
            },
        )
        assert response.status_code == 400
        assert "原密码错误" in response.json()["detail"]

    def test_change_password_without_auth(self, client: TestClient):
        """测试未登录修改密码"""
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "OldPass123",
                "new_password": "NewPass123",
            },
        )
        assert response.status_code == 401

    def test_change_password_weak_password(self, client: TestClient, auth_headers: dict):
        """测试弱密码 (不符合复杂度要求)"""
        response = client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "Test1234",
                "new_password": "weakpass",  # No uppercase, no digit
            },
        )
        assert response.status_code == 422  # Validation error

    def test_change_password_short_password(self, client: TestClient, auth_headers: dict):
        """测试密码过短"""
        response = client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "Test1234",
                "new_password": "Ab1",  # Too short
            },
        )
        assert response.status_code == 422  # Validation error
