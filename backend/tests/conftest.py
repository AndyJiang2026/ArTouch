# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create pytest fixtures for Artouch backend testing
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P2

"""
Pytest fixtures for Artouch NFC system testing.
"""

import os
import sys
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Ensure app module is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment before importing app
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["DATABASE_URL"] = "sqlite:///./test_db_temp.db"
# Use invalid Redis URL to force in-memory rate limiting (avoid Redis rate limit)
os.environ["REDIS_URL"] = "redis://invalid:6379/0"


from app.api import auth as auth_module
from app.api.deps import get_db
from app.core.security import get_password_hash
from app.database import Base
from app.main import app
from app.models import User


def _clear_rate_limiter():
    """Clear the in-memory rate limiter before each test."""
    auth_module._inmemory_attempts = {}


@pytest.fixture(autouse=True)
def clear_rate_limit():
    """Clear rate limiter before each test."""
    auth_module._inmemory_attempts = {}


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///./test_db_temp.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Create a test client with database session override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """Create a test user with 'user' role."""
    user = User(
        username="testuser",
        password_hash=get_password_hash("TestPass123"),
        role="user",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_operator(db_session: Session) -> User:
    """Create a test user with 'operator' role."""
    user = User(
        username="testoperator",
        password_hash=get_password_hash("TestPass123"),
        role="operator",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_admin(db_session: Session) -> User:
    """Create a test user with 'admin' role."""
    user = User(
        username="testadmin",
        password_hash=get_password_hash("TestPass123"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers_user(client: TestClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "TestPass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_operator(client: TestClient, test_operator: User) -> dict:
    """Get authentication headers for test operator."""
    response = client.post(
        "/api/auth/login",
        data={"username": "testoperator", "password": "TestPass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_admin(client: TestClient, test_admin: User) -> dict:
    """Get authentication headers for test admin."""
    response = client.post(
        "/api/auth/login",
        data={"username": "testadmin", "password": "TestPass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
