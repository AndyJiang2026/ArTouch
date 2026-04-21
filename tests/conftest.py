# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create pytest fixtures for FastAPI testing with SQLite test database
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

import os
import sys
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.api.deps import get_db
from app.api.nfc import get_db_public
from app.core.security import get_password_hash
from app.database import Base
from app.main import app
from app.models import CulturalProduct, NFCTag, User, Video

# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = testing_session_local()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(test_db) -> Generator[TestClient, None, None]:
    """Create a test client with test database."""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_public] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def _test_user(test_db: Session) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        password_hash=get_password_hash("Test1234"),
        role="operator",
        is_active=True,
        is_first_login=False,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_admin(test_db: Session) -> User:
    """Create a test admin user."""
    admin = User(
        username="admin",
        password_hash=get_password_hash("Admin1234"),
        role="admin",
        is_active=True,
        is_first_login=True,
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin


@pytest.fixture
def test_video(test_db: Session) -> Video:
    """Create a test video."""
    video = Video(
        code="T01",
        name="测试视频",
        file_path="/videos/test.mp4",
        duration=120.5,
        file_size=1024000,
        status="ready",
    )
    test_db.add(video)
    test_db.commit()
    test_db.refresh(video)
    return video


@pytest.fixture
def test_cultural_product(test_db: Session) -> CulturalProduct:
    """Create a test cultural product."""
    product = CulturalProduct(
        code="001",
        name="测试文创品",
        description="这是一个测试文创品",
        status="active",
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product


@pytest.fixture
def test_nfc_tag(
    test_db: Session, test_video: Video, test_cultural_product: CulturalProduct, _test_user: User
) -> NFCTag:
    """Create a test NFC tag."""
    tag = NFCTag(
        url_code="TEST123456",
        video_id=test_video.id,
        cultural_product_id=test_cultural_product.id,
        status="active",
        approval_status="approved",
        created_by=_test_user.id,
        approved_by=_test_user.id,
    )
    test_db.add(tag)
    test_db.commit()
    test_db.refresh(tag)
    return tag


@pytest.fixture
def auth_headers(client: TestClient, _test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "Test1234"},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client: TestClient, test_admin: User) -> dict:
    """Get authentication headers for admin user."""
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "Admin1234"},
    )
    assert response.status_code == 200, f"Admin login failed: {response.json()}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
