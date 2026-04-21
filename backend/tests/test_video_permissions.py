# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create video permission tests for Artouch backend
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P2

"""
Tests for video module permissions (verifying operator/admin requirement).
"""

from app.models import Video
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestVideoPermissions:
    """Tests for video module RBAC - verifying operator/admin requirement."""

    def test_upload_requires_operator_or_admin(
        self, client: TestClient, auth_headers_user: dict
    ):
        """Test that video upload requires operator or admin role."""
        response = client.post(
            "/api/videos/upload",
            headers=auth_headers_user,
            data={"code": "V001", "name": "Test Video"},
        )
        # Should be forbidden for regular user
        assert response.status_code == 403

    def test_upload_allows_operator(
        self, client: TestClient, auth_headers_operator: dict
    ):
        """Test that video upload allows operator role."""
        # Note: This will fail at file validation, but should pass auth
        response = client.post(
            "/api/videos/upload",
            headers=auth_headers_operator,
            data={"code": "V001", "name": "Test Video"},
        )
        # Should not be 403 - either 400 (bad request - no file) or actual upload attempt
        assert response.status_code != 403

    def test_upload_allows_admin(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Test that video upload allows admin role."""
        response = client.post(
            "/api/videos/upload",
            headers=auth_headers_admin,
            data={"code": "V002", "name": "Test Video"},
        )
        # Should not be 403
        assert response.status_code != 403

    def test_update_requires_operator_or_admin(
        self,
        client: TestClient,
        auth_headers_user: dict,
        db_session: Session,
    ):
        """Test that video update requires operator or admin role."""
        # Create a video first (using direct DB)
        video = Video(code="V003", name="Test Video", status="active")
        db_session.add(video)
        db_session.commit()
        db_session.refresh(video)

        response = client.put(
            f"/api/videos/{video.id}",
            headers=auth_headers_user,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 403

    def test_delete_requires_operator_or_admin(
        self,
        client: TestClient,
        auth_headers_user: dict,
        db_session: Session,
    ):
        """Test that video delete requires operator or admin role."""
        video = Video(code="V004", name="Test Video", status="active")
        db_session.add(video)
        db_session.commit()
        db_session.refresh(video)

        response = client.delete(
            f"/api/videos/{video.id}",
            headers=auth_headers_user,
        )
        assert response.status_code == 403

    def test_process_requires_operator_or_admin(
        self,
        client: TestClient,
        auth_headers_user: dict,
        db_session: Session,
    ):
        """Test that video process requires operator or admin role."""
        video = Video(code="V005", name="Test Video", status="active")
        db_session.add(video)
        db_session.commit()
        db_session.refresh(video)

        response = client.post(
            f"/api/videos/{video.id}/process",
            headers=auth_headers_user,
        )
        assert response.status_code == 403


class TestVideoListPermissions:
    """Tests for video list - any authenticated user can view."""

    def test_list_allows_any_authenticated_user(
        self,
        client: TestClient,
        auth_headers_user: dict,
    ):
        """Test that listing videos is allowed for any authenticated user."""
        response = client.get("/api/videos/", headers=auth_headers_user)
        assert response.status_code == 200

    def test_list_allows_operator(
        self,
        client: TestClient,
        auth_headers_operator: dict,
    ):
        """Test that listing videos is allowed for operator."""
        response = client.get("/api/videos/", headers=auth_headers_operator)
        assert response.status_code == 200

    def test_list_allows_admin(
        self,
        client: TestClient,
        auth_headers_admin: dict,
    ):
        """Test that listing videos is allowed for admin."""
        response = client.get("/api/videos/", headers=auth_headers_admin)
        assert response.status_code == 200
