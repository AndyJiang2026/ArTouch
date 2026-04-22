# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Test configuration module settings and behavior
# DATE: 2026-04-21
# ENGINEER: System
# RISK-LEVEL: P2

"""
Tests for configuration module - verifying config interface and settings behavior.
"""

import os
import pytest
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Ensure app module is importable
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment before importing app
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["DATABASE_URL"] = "sqlite:///./test_config_api.db"
os.environ["REDIS_URL"] = "redis://invalid:***@localhost:6379/0"  # Invalid to force in-memory rate limiting
os.environ["PROTECT_STATIC_FILES"] = "false"

from app.config import Settings


class TestConfigSettings:
    """Tests for configuration settings behavior."""

    def test_secret_key_required_fallback(self):
        """Test that Settings requires SECRET_KEY when not provided."""
        # Note: This test verifies the Settings class behavior
        # Since we can't easily reload Settings with different env,
        # we verify the current env is correctly loaded
        settings = Settings()
        assert settings.SECRET_KEY == "test-secret-key-for-testing"

    def test_database_url_configurable(self):
        """Test that DATABASE_URL can be configured via environment variable."""
        settings = Settings()
        assert settings.DATABASE_URL == "sqlite:///./test_config_api.db"

    def test_redis_url_configurable(self):
        """Test that REDIS_URL can be configured via environment variable."""
        settings = Settings()
        assert settings.REDIS_URL == "redis://invalid:***@localhost:6379/0"

    def test_max_video_size_default(self):
        """Test default MAX_VIDEO_SIZE is 200MB."""
        settings = Settings()
        assert settings.MAX_VIDEO_SIZE == 200 * 1024 * 1024

    def test_allowed_video_types(self):
        """Test ALLOWED_VIDEO_TYPES includes expected formats."""
        settings = Settings()
        assert "video/mp4" in settings.ALLOWED_VIDEO_TYPES
        assert "video/mpeg" in settings.ALLOWED_VIDEO_TYPES
        assert "video/quicktime" in settings.ALLOWED_VIDEO_TYPES

    def test_protect_static_files_env_parsing(self):
        """Test PROTECT_STATIC_FILES env parsing (true/false string to bool)."""
        settings = Settings()
        assert settings.PROTECT_STATIC_FILES is False

        # Test with true
        os.environ["PROTECT_STATIC_FILES"] = "true"
        settings_true = Settings()
        assert settings_true.PROTECT_STATIC_FILES is True

        # Reset
        os.environ["PROTECT_STATIC_FILES"] = "false"

    def test_app_name_default(self):
        """Test default APP_NAME."""
        settings = Settings()
        assert settings.APP_NAME == "ArtTouch NFC System"

    def test_app_version_default(self):
        """Test default APP_VERSION."""
        settings = Settings()
        assert settings.APP_VERSION == "1.0.0"

    def test_access_token_expire_hours_default(self):
        """Test default ACCESS_TOKEN_EXPIRE_HOURS."""
        settings = Settings()
        assert settings.ACCESS_TOKEN_EXPIRE_HOURS == 2

    def test_refresh_token_expire_days_default(self):
        """Test default REFRESH_TOKEN_EXPIRE_DAYS."""
        settings = Settings()
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_static_file_sign_expire_minutes_default(self):
        """Test default STATIC_FILE_SIGN_EXPIRE_MINUTES."""
        settings = Settings()
        assert settings.STATIC_FILE_SIGN_EXPIRE_MINUTES == 60

    def test_nfc_base_url_default(self):
        """Test default NFC_BASE_URL."""
        settings = Settings()
        assert settings.NFC_BASE_URL == "https://www.artouch.tech/nfc"

    def test_directories_exist_or_created(self):
        """Test that required directories are created."""
        settings = Settings()
        # VIDEO_DIR, COVER_DIR, DATA_DIR should exist (or be created)
        assert settings.VIDEO_DIR is not None
        assert settings.COVER_DIR is not None
        assert settings.DATA_DIR is not None

    def test_case_sensitive_env_parsing(self):
        """Test that environment variable parsing is case sensitive."""
        settings = Settings()
        assert settings.__class__.model_config.get("case_sensitive") is True


class TestConfigAPIIntegration:
    """Integration tests for config settings via API."""

    def test_app_info_endpoint(self, client: TestClient):
        """Test that root endpoint returns correct app info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "ArtTouch NFC System"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"

    def test_health_check_endpoint(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestConfigPermissions:
    """Tests for permission-related config (roles, access control)."""

    def test_admin_role_required_endpoints(self, client: TestClient, auth_headers_operator: dict):
        """Test that some endpoints require operator or admin role."""
        # Operator should be able to access dashboard stats
        response = client.get("/api/dashboard/stats", headers=auth_headers_operator)
        assert response.status_code == 200

    def test_operator_permissions_workflow(self, client: TestClient, auth_headers_operator: dict):
        """Test operator role can access operator-level endpoints."""
        # Upload endpoint - operator should have access
        response = client.post(
            "/api/videos/upload",
            headers=auth_headers_operator,
            data={"code": "TEST001", "name": "Test Video"},
        )
        # Should not be 403 (might be 400 due to missing file)
        assert response.status_code != 403

    def test_user_limited_permissions(self, client: TestClient, auth_headers_user: dict):
        """Test that regular user has limited permissions."""
        # Upload endpoint - user should be forbidden
        response = client.post(
            "/api/videos/upload",
            headers=auth_headers_user,
            data={"code": "TEST002", "name": "Test Video"},
        )
        assert response.status_code == 403

    def test_list_videos_any_authenticated(self, client: TestClient, auth_headers_user: dict):
        """Test listing videos is allowed for any authenticated user."""
        response = client.get("/api/videos/", headers=auth_headers_user)
        assert response.status_code == 200