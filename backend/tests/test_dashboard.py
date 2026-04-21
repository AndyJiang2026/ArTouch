# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create dashboard tests for Artouch backend
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P2

"""
Tests for dashboard endpoints.
"""

from fastapi.testclient import TestClient


class TestDashboardStats:
    """Tests for GET /api/dashboard/stats."""

    def test_stats_requires_auth(self, client: TestClient):
        """Test that stats endpoint requires authentication."""
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 401

    def test_stats_success(
        self, client: TestClient, auth_headers_operator: dict
    ):
        """Test getting dashboard stats."""
        response = client.get(
            "/api/dashboard/stats",
            headers=auth_headers_operator,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_clicks" in data
        assert "today_clicks" in data
        assert "total_tags" in data


class TestDashboardDaily:
    """Tests for GET /api/dashboard/daily."""

    def test_daily_requires_auth(self, client: TestClient):
        """Test that daily endpoint requires authentication."""
        response = client.get("/api/dashboard/daily?date=2026-04-20")
        assert response.status_code == 401

    def test_daily_requires_date_param(
        self, client: TestClient, auth_headers_operator: dict
    ):
        """Test that daily endpoint requires date parameter."""
        response = client.get(
            "/api/dashboard/daily",
            headers=auth_headers_operator,
        )
        assert response.status_code == 422  # Validation error

    def test_daily_success(
        self, client: TestClient, auth_headers_operator: dict
    ):
        """Test getting daily stats."""
        response = client.get(
            "/api/dashboard/daily",
            headers=auth_headers_operator,
            params={"date_str": "2026-04-20"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "click_count" in data


class TestDashboardWeekly:
    """Tests for GET /api/dashboard/weekly."""

    def test_weekly_requires_auth(self, client: TestClient):
        """Test that weekly endpoint requires authentication."""
        response = client.get("/api/dashboard/weekly?week=2026-W16")
        assert response.status_code == 401

    def test_weekly_requires_week_param(
        self, client: TestClient, auth_headers_operator: dict
    ):
        """Test that weekly endpoint requires week parameter."""
        response = client.get(
            "/api/dashboard/weekly",
            headers=auth_headers_operator,
        )
        assert response.status_code == 422

    def test_weekly_success(
        self, client: TestClient, auth_headers_operator: dict
    ):
        """Test getting weekly stats."""
        response = client.get(
            "/api/dashboard/weekly?week=2026-W16",
            headers=auth_headers_operator,
        )
        assert response.status_code == 200
        data = response.json()
        assert "week" in data
        assert "click_count" in data


class TestDashboardMonthly:
    """Tests for GET /api/dashboard/monthly."""

    def test_monthly_requires_auth(self, client: TestClient):
        """Test that monthly endpoint requires authentication."""
        response = client.get("/api/dashboard/monthly?month=2026-04")
        assert response.status_code == 401

    def test_monthly_requires_month_param(
        self, client: TestClient, auth_headers_operator: dict
    ):
        """Test that monthly endpoint requires month parameter."""
        response = client.get(
            "/api/dashboard/monthly",
            headers=auth_headers_operator,
        )
        assert response.status_code == 422

    def test_monthly_success(
        self, client: TestClient, auth_headers_operator: dict
    ):
        """Test getting monthly stats."""
        response = client.get(
            "/api/dashboard/monthly?month=2026-04",
            headers=auth_headers_operator,
        )
        assert response.status_code == 200
        data = response.json()
        assert "month" in data
        assert "click_count" in data
