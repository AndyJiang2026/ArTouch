# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create Dashboard Pydantic schemas
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from pydantic import BaseModel


class TopTag(BaseModel):
    tag_id: int
    url_code: str
    click_count: int


class DashboardStats(BaseModel):
    total_clicks: int
    today_clicks: int
    week_clicks: int
    month_clicks: int
    total_tags: int
    active_tags: int
    pending_tags: int
    total_cultural_products: int
    total_videos: int
    total_skus: int
    top_tags: list[TopTag]
    week_daily_clicks: list[int] = []  # Daily clicks for each day of current week (Mon-Sun)


class DailyStats(BaseModel):
    date: str
    click_count: int
    new_tags: int
    approved_tags: int


class WeeklyStats(BaseModel):
    week: str
    click_count: int
    new_tags: int
    approved_tags: int


class MonthlyStats(BaseModel):
    month: str
    click_count: int
    new_tags: int
    approved_tags: int
