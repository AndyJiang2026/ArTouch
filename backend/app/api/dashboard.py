# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create dashboard API routes for statistics
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models import TagClick, NFCTag, CulturalProduct, Video, SKU, User
from app.schemas.dashboard import (
    DashboardStats,
    DailyStats,
    WeeklyStats,
    MonthlyStats,
    TopTag,
)

router = APIRouter(prefix="/api/dashboard", tags=["数据看板"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardStats:
    """Get overall dashboard statistics."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # Click counts
    total_clicks = db.query(func.count(TagClick.id)).scalar() or 0
    today_clicks = db.query(func.count(TagClick.id)).filter(
        TagClick.clicked_at >= today_start
    ).scalar() or 0
    week_clicks = db.query(func.count(TagClick.id)).filter(
        TagClick.clicked_at >= week_start
    ).scalar() or 0
    month_clicks = db.query(func.count(TagClick.id)).filter(
        TagClick.clicked_at >= month_start
    ).scalar() or 0

    # Tag counts
    total_tags = db.query(func.count(NFCTag.id)).scalar() or 0
    active_tags = db.query(func.count(NFCTag.id)).filter(
        NFCTag.status == "active"
    ).scalar() or 0
    pending_tags = db.query(func.count(NFCTag.id)).filter(
        NFCTag.approval_status == "pending"
    ).scalar() or 0

    # Other counts
    total_cultural_products = db.query(func.count(CulturalProduct.id)).scalar() or 0
    total_videos = db.query(func.count(Video.id)).scalar() or 0
    total_skus = db.query(func.count(SKU.id)).scalar() or 0

    # Top 10 tags by clicks
    top_tags_query = db.query(
        TagClick.tag_id,
        func.count(TagClick.id).label("click_count"),
    ).group_by(TagClick.tag_id).order_by(
        func.count(TagClick.id).desc()
    ).limit(10).all()

    top_tags = []
    for tag_id, click_count in top_tags_query:
        tag = db.query(NFCTag).filter(NFCTag.id == tag_id).first()
        if tag:
            top_tags.append(TopTag(
                tag_id=tag_id,
                url_code=tag.url_code,
                click_count=click_count,
            ))

    return DashboardStats(
        total_clicks=total_clicks,
        today_clicks=today_clicks,
        week_clicks=week_clicks,
        month_clicks=month_clicks,
        total_tags=total_tags,
        active_tags=active_tags,
        pending_tags=pending_tags,
        total_cultural_products=total_cultural_products,
        total_videos=total_videos,
        total_skus=total_skus,
        top_tags=top_tags,
    )


@router.get("/daily", response_model=DailyStats)
def get_daily_stats(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyStats:
    """Get daily statistics."""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("日期格式错误，请使用YYYY-MM-DD格式")

    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    click_count = db.query(func.count(TagClick.id)).filter(
        and_(
            TagClick.clicked_at >= day_start,
            TagClick.clicked_at < day_end,
        )
    ).scalar() or 0

    new_tags = db.query(func.count(NFCTag.id)).filter(
        func.date(NFCTag.created_at) == target_date
    ).scalar() or 0

    approved_tags = db.query(func.count(NFCTag.id)).filter(
        and_(
            NFCTag.approved_at == target_date,
            NFCTag.approval_status == "approved",
        )
    ).scalar() or 0

    return DailyStats(
        date=date,
        click_count=click_count,
        new_tags=new_tags,
        approved_tags=approved_tags,
    )


@router.get("/weekly", response_model=WeeklyStats)
def get_weekly_stats(
    week: str = Query(..., description="Week in YYYY-Www format (e.g., 2026-W15)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WeeklyStats:
    """Get weekly statistics."""
    try:
        # Parse ISO week format
        year, week_num = week.split("-W")
        year, week_num = int(year), int(week_num)
        jan4 = datetime(year, 1, 4)
        week_start = jan4 + timedelta(weeks=week_num - 1, days=-jan4.weekday())
        week_end = week_start + timedelta(days=7)
    except (ValueError, IndexError):
        raise ValueError("周格式错误，请使用YYYY-Www格式")

    click_count = db.query(func.count(TagClick.id)).filter(
        and_(
            TagClick.clicked_at >= week_start,
            TagClick.clicked_at < week_end,
        )
    ).scalar() or 0

    new_tags = db.query(func.count(NFCTag.id)).filter(
        and_(
            NFCTag.created_at >= week_start,
            NFCTag.created_at < week_end,
        )
    ).scalar() or 0

    approved_tags = db.query(func.count(NFCTag.id)).filter(
        and_(
            NFCTag.approved_at >= week_start.date(),
            NFCTag.approved_at < week_end.date(),
            NFCTag.approval_status == "approved",
        )
    ).scalar() or 0

    return WeeklyStats(
        week=week,
        click_count=click_count,
        new_tags=new_tags,
        approved_tags=approved_tags,
    )


@router.get("/monthly", response_model=MonthlyStats)
def get_monthly_stats(
    month: str = Query(..., description="Month in YYYY-MM format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MonthlyStats:
    """Get monthly statistics."""
    try:
        year, month_num = map(int, month.split("-"))
        if month_num < 1 or month_num > 12:
            raise ValueError()
        month_start = datetime(year, month_num, 1)
        if month_num == 12:
            month_end = datetime(year + 1, 1, 1)
        else:
            month_end = datetime(year, month_num + 1, 1)
    except (ValueError, IndexError):
        raise ValueError("月份格式错误，请使用YYYY-MM格式")

    click_count = db.query(func.count(TagClick.id)).filter(
        and_(
            TagClick.clicked_at >= month_start,
            TagClick.clicked_at < month_end,
        )
    ).scalar() or 0

    new_tags = db.query(func.count(NFCTag.id)).filter(
        and_(
            NFCTag.created_at >= month_start,
            NFCTag.created_at < month_end,
        )
    ).scalar() or 0

    approved_tags = db.query(func.count(NFCTag.id)).filter(
        and_(
            NFCTag.approved_at >= month_start.date(),
            NFCTag.approved_at < month_end.date(),
            NFCTag.approval_status == "approved",
        )
    ).scalar() or 0

    return MonthlyStats(
        month=month,
        click_count=click_count,
        new_tags=new_tags,
        approved_tags=approved_tags,
    )
