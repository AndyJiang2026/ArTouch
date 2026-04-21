# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create tests for dashboard API endpoints
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

"""
数据看板API测试模块

测试内容:
- 总体统计 (GET /api/dashboard/stats)
- 日统计 (GET /api/dashboard/daily?date_str=YYYY-MM-DD)
- 周统计 (GET /api/dashboard/weekly?week=YYYY-Www)
- 月统计 (GET /api/dashboard/monthly?month=YYYY-MM)
"""

from fastapi.testclient import TestClient


class TestDashboardOverall:
    """总体统计接口测试"""

    def test_overall_stats_success(self, client: TestClient, auth_headers: dict):
        """测试获取总体统计"""
        response = client.get("/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_clicks" in data
        assert "today_clicks" in data
        assert "week_clicks" in data
        assert "month_clicks" in data
        assert "total_tags" in data
        assert "active_tags" in data

    def test_overall_stats_without_auth(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 401


class TestDashboardDaily:
    """日统计接口测试"""

    def test_daily_stats_success(self, client: TestClient, auth_headers: dict):
        """测试获取日统计"""
        response = client.get(
            "/api/dashboard/daily?date_str=2026-04-19", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2026-04-19"
        assert "click_count" in data
        assert "new_tags" in data
        assert "approved_tags" in data

    def test_daily_stats_invalid_date(self, client: TestClient, auth_headers: dict):
        """Test invalid date format triggers ValueError -> 400"""
        response = client.get(
            "/api/dashboard/daily?date_str=not-a-date", headers=auth_headers
        )
        assert response.status_code == 400

    def test_daily_stats_missing_date(self, client: TestClient, auth_headers: dict):
        """测试缺少日期参数"""
        response = client.get("/api/dashboard/daily", headers=auth_headers)
        assert response.status_code == 422

    def test_daily_stats_without_auth(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/dashboard/daily?date_str=2026-04-19")
        assert response.status_code == 401


class TestDashboardWeekly:
    """周统计接口测试"""

    def test_weekly_stats_success(self, client: TestClient, auth_headers: dict):
        """测试获取周统计"""
        response = client.get(
            "/api/dashboard/weekly?week=2026-W16", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "week" in data
        assert "click_count" in data

    def test_weekly_stats_invalid_format(self, client: TestClient, auth_headers: dict):
        """测试无效周格式"""
        response = client.get(
            "/api/dashboard/weekly?week=invalid", headers=auth_headers
        )
        assert response.status_code == 400

    def test_weekly_stats_invalid_week_number(
        self, client: TestClient, auth_headers: dict
    ):
        """测试无效周数"""
        response = client.get(
            "/api/dashboard/weekly?week=2026-W99", headers=auth_headers
        )
        assert response.status_code == 400

    def test_weekly_stats_missing_week(self, client: TestClient, auth_headers: dict):
        """测试缺少周参数"""
        response = client.get("/api/dashboard/weekly", headers=auth_headers)
        assert response.status_code == 422

    def test_weekly_stats_without_auth(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/dashboard/weekly?week=2026-W16")
        assert response.status_code == 401


class TestDashboardMonthly:
    """月统计接口测试"""

    def test_monthly_stats_success(self, client: TestClient, auth_headers: dict):
        """测试获取月统计"""
        response = client.get(
            "/api/dashboard/monthly?month=2026-04", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "month" in data
        assert "click_count" in data

    def test_monthly_stats_invalid_format(self, client: TestClient, auth_headers: dict):
        """测试无效月格式"""
        response = client.get(
            "/api/dashboard/monthly?month=invalid", headers=auth_headers
        )
        assert response.status_code == 400

    def test_monthly_stats_invalid_month(
        self, client: TestClient, auth_headers: dict
    ):
        """测试无效月份"""
        response = client.get(
            "/api/dashboard/monthly?month=2026-99", headers=auth_headers
        )
        assert response.status_code == 400

    def test_monthly_stats_missing_param(self, client: TestClient, auth_headers: dict):
        """测试缺少月参数"""
        response = client.get("/api/dashboard/monthly", headers=auth_headers)
        assert response.status_code == 422

    def test_monthly_stats_without_auth(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/dashboard/monthly?month=2026-04")
        assert response.status_code == 401
