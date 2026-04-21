# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create NFC tag tests for Artouch backend
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P2

"""
Tests for NFC tag endpoints.
"""

import pytest
from app.models import SKU, CulturalProduct, NFCTag, Video
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def cultural_product(db_session: Session) -> CulturalProduct:
    """Create a test cultural product."""
    product = CulturalProduct(
        code="CP001",
        name="Test Cultural Product",
        status="active",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def video(db_session: Session) -> Video:
    """Create a test video."""
    video = Video(
        code="VD001",
        name="Test Video",
        status="active",
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    return video


@pytest.fixture
def sku(db_session: Session, cultural_product: CulturalProduct) -> SKU:
    """Create a test SKU."""
    sku = SKU(
        code="001",
        name="Test SKU",
        cultural_product_id=cultural_product.id,
    )
    db_session.add(sku)
    db_session.commit()
    db_session.refresh(sku)
    return sku


class TestNFCTagsList:
    """Tests for GET /api/nfc-tags/."""

    def test_list_nfc_tags_empty(
        self, client: TestClient, auth_headers_operator: dict
    ):
        """Test listing NFC tags when none exist."""
        response = client.get("/api/nfc-tags/", headers=auth_headers_operator)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_nfc_tags_with_data(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """Test listing NFC tags with existing data."""
        tag = NFCTag(
            url_code="TEST001",
            cultural_product_id=cultural_product.id,
            video_id=video.id,
            status="active",
            approval_status="approved",
            created_by=1,
        )
        db_session.add(tag)
        db_session.commit()

        response = client.get("/api/nfc-tags/", headers=auth_headers_operator)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["url_code"] == "TEST001"


class TestNFCTagsCreate:
    """Tests for POST /api/nfc-tags/."""

    def test_create_nfc_tag_requires_operator(
        self,
        client: TestClient,
        auth_headers_user: dict,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """Test creating NFC tag requires operator role."""
        response = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_user,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        assert response.status_code == 403

    def test_create_nfc_tag_success(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """Test creating NFC tag with operator role."""
        response = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["url_code"] is not None
        assert data["cultural_product_id"] == cultural_product.id
        assert data["video_id"] == video.id

    def test_create_nfc_tag_with_sku(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        cultural_product: CulturalProduct,
        video: Video,
        sku: SKU,
    ):
        """Test creating NFC tag with SKU."""
        response = client.post(
            "/api/nfc-tags/",
            headers=auth_headers_operator,
            json={
                "cultural_product_id": cultural_product.id,
                "video_id": video.id,
                "sku_id": sku.id,
                "auto_create_sku_instance": False,  # Disable auto-create for test
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["sku_id"] == sku.id
        # sku_instance_id will be None since auto_create is disabled


class TestNFCTagsApprove:
    """Tests for POST /api/nfc-tags/{id}/approve."""

    def test_approve_requires_admin(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """Test approving NFC tag requires admin role."""
        tag = NFCTag(
            url_code="TEST002",
            cultural_product_id=cultural_product.id,
            video_id=video.id,
            status="active",
            approval_status="pending",
            created_by=1,
        )
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        response = client.post(
            f"/api/nfc-tags/{tag.id}/approve",
            headers=auth_headers_operator,
        )
        assert response.status_code == 403

    def test_approve_success(
        self,
        client: TestClient,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """Test approving NFC tag with admin role."""
        tag = NFCTag(
            url_code="TEST003",
            cultural_product_id=cultural_product.id,
            video_id=video.id,
            status="active",
            approval_status="pending",
            created_by=1,
        )
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        response = client.post(
            f"/api/nfc-tags/{tag.id}/approve",
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"


class TestNFCTagsDelete:
    """Tests for DELETE /api/nfc-tags/{id}."""

    def test_delete_requires_admin(
        self,
        client: TestClient,
        auth_headers_operator: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """Test deleting NFC tag requires admin role."""
        tag = NFCTag(
            url_code="TEST004",
            cultural_product_id=cultural_product.id,
            video_id=video.id,
            status="active",
            approval_status="approved",
            created_by=1,
        )
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        response = client.delete(
            f"/api/nfc-tags/{tag.id}",
            headers=auth_headers_operator,
        )
        assert response.status_code == 403

    def test_delete_success(
        self,
        client: TestClient,
        auth_headers_admin: dict,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """Test deleting NFC tag with admin role."""
        tag = NFCTag(
            url_code="TEST005",
            cultural_product_id=cultural_product.id,
            video_id=video.id,
            status="active",
            approval_status="approved",
            created_by=1,
        )
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        response = client.delete(
            f"/api/nfc-tags/{tag.id}",
            headers=auth_headers_admin,
        )
        assert response.status_code == 204


class TestNFCPlay:
    """Tests for GET /api/nfc/{code}/play (public endpoint)."""

    def test_play_nfc_tag_not_found(self, client: TestClient):
        """Test playing non-existent NFC tag returns 404."""
        response = client.get("/api/nfc/NONEXISTENT/play")
        assert response.status_code == 404

    def test_play_nfc_tag_not_approved(
        self,
        client: TestClient,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """Test playing unapproved NFC tag returns 403 or 404."""
        tag = NFCTag(
            url_code="TEST006",
            cultural_product_id=cultural_product.id,
            video_id=video.id,
            status="active",
            approval_status="pending",
            created_by=1,
        )
        db_session.add(tag)
        db_session.commit()

        response = client.get("/api/nfc/TEST006/play")
        # Returns 403 (forbidden) or 404 (not found) per actual implementation
        assert response.status_code in [403, 404]

    def test_play_nfc_tag_success(
        self,
        client: TestClient,
        db_session: Session,
        cultural_product: CulturalProduct,
        video: Video,
    ):
        """Test playing approved NFC tag returns video info."""
        tag = NFCTag(
            url_code="TEST007",
            cultural_product_id=cultural_product.id,
            video_id=video.id,
            status="active",
            approval_status="approved",
            created_by=1,
        )
        db_session.add(tag)
        db_session.commit()

        response = client.get("/api/nfc/TEST007/play")
        assert response.status_code == 200
        data = response.json()
        assert "video_url" in data or "video" in data
        assert "cultural_product_name" in data
