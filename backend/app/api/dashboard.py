# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create dashboard API routes for statistics
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_operator_or_admin
from app.models import SKU, CulturalProduct, NFCTag, TagClick, User, Video
from app.schemas.dashboard import (
    DailyStats,
    DashboardStats,
    MonthlyStats,
    TopTag,
    WeeklyStats,
)

router = APIRouter(prefix="/api/dashboard", tags=["数据看板"])

MONTHS_PER_YEAR = 12
MAX_WEEKS_PER_YEAR = 53


def parse_date(date_str: str) -> "datetime.date":
    """Parse date string in YYYY-MM-DD format and return date object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("日期格式错误,请使用YYYY-MM-DD格式")


def parse_week(week_str: str) -> tuple["datetime", "datetime"]:
    """
    Parse ISO week string (YYYY-Www) and return (week_start, week_end) datetimes.
    Raises ValueError if format is invalid.
    """
    try:
        year, week_num = week_str.split("-W")
        year, week_num = int(year), int(week_num)
        if year < 1 or week_num < 1 or week_num > MAX_WEEKS_PER_YEAR:
            raise ValueError("周格式错误")
        # ISO week 1 is the week containing the first Thursday (Mon-Sun)
        jan4 = datetime(year, 1, 4, tzinfo=UTC)
        # Monday of week 1 is the Monday of the week containing Jan 4
        week1_monday = jan4 - timedelta(days=jan4.weekday())
        week_start = week1_monday + timedelta(weeks=week_num - 1)
        week_end = week_start + timedelta(days=7)
        return week_start, week_end
    except (ValueError, IndexError):
        raise ValueError("周格式错误,请使用YYYY-Www格式")


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_operator_or_admin),
) -> DashboardStats:
    """Get overall dashboard statistics (operator or admin only)."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # Click counts
    total_clicks = db.query(func.count(TagClick.id)).scalar() or 0
    today_clicks = db.query(func.count(TagClick.id)).filter(TagClick.clicked_at >= today_start).scalar() or 0
    week_clicks = db.query(func.count(TagClick.id)).filter(TagClick.clicked_at >= week_start).scalar() or 0
    month_clicks = db.query(func.count(TagClick.id)).filter(TagClick.clicked_at >= month_start).scalar() or 0

    # Tag counts
    total_tags = db.query(func.count(NFCTag.id)).scalar() or 0
    active_tags = db.query(func.count(NFCTag.id)).filter(NFCTag.status == "active").scalar() or 0
    pending_tags = db.query(func.count(NFCTag.id)).filter(NFCTag.approval_status == "pending").scalar() or 0

    # Other counts
    total_cultural_products = db.query(func.count(CulturalProduct.id)).scalar() or 0
    total_videos = db.query(func.count(Video.id)).scalar() or 0
    total_skus = db.query(func.count(SKU.id)).scalar() or 0

    # Top 10 tags by clicks (fixed: use JOIN to avoid N+1 query)
    top_tags_query = (
        db.query(
            TagClick.tag_id,
            NFCTag.url_code,
            func.count(TagClick.id).label("click_count"),
        )
        .join(NFCTag, TagClick.tag_id == NFCTag.id)
        .group_by(TagClick.tag_id, NFCTag.url_code)
        .order_by(func.count(TagClick.id).desc())
        .limit(10)
        .all()
    )

    top_tags = [
        TopTag(tag_id=tag_id, url_code=url_code, click_count=click_count)
        for tag_id, url_code, click_count in top_tags_query
    ]

    # Calculate daily clicks for each day of the current week (Mon-Sun)
    week_daily_clicks: list[int] = []
    for i in range(7):
        day_start = week_start + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        day_clicks = (
            db.query(func.count(TagClick.id))
            .filter(
                and_(
                    TagClick.clicked_at >= day_start,
                    TagClick.clicked_at < day_end,
                )
            )
            .scalar()
            or 0
        )
        week_daily_clicks.append(day_clicks)

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
        week_daily_clicks=week_daily_clicks,
    )


@router.get("/daily", response_model=DailyStats)
def get_daily_stats(
    date_str: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_operator_or_admin),
) -> DailyStats:
    """Get daily statistics (operator or admin only)."""
    target_date = parse_date(date_str)

    day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=UTC)
    day_end = day_start + timedelta(days=1)

    click_count = (
        db.query(func.count(TagClick.id))
        .filter(
            and_(
                TagClick.clicked_at >= day_start,
                TagClick.clicked_at < day_end,
            )
        )
        .scalar()
        or 0
    )

    new_tags = db.query(func.count(NFCTag.id)).filter(func.date(NFCTag.created_at) == target_date).scalar() or 0

    approved_tags = (
        db.query(func.count(NFCTag.id))
        .filter(
            and_(
                NFCTag.approved_at == target_date,
                NFCTag.approval_status == "approved",
            )
        )
        .scalar()
        or 0
    )

    return DailyStats(
        date=date_str,
        click_count=click_count,
        new_tags=new_tags,
        approved_tags=approved_tags,
    )


@router.get("/weekly", response_model=WeeklyStats)
def get_weekly_stats(
    week: str = Query(..., description="Week in YYYY-Www format (e.g., 2026-W15)"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_operator_or_admin),
) -> WeeklyStats:
    """Get weekly statistics (operator or admin only)."""
    week_start, week_end = parse_week(week)

    click_count = (
        db.query(func.count(TagClick.id))
        .filter(
            and_(
                TagClick.clicked_at >= week_start,
                TagClick.clicked_at < week_end,
            )
        )
        .scalar()
        or 0
    )

    new_tags = (
        db.query(func.count(NFCTag.id))
        .filter(
            and_(
                NFCTag.created_at >= week_start,
                NFCTag.created_at < week_end,
            )
        )
        .scalar()
        or 0
    )

    approved_tags = (
        db.query(func.count(NFCTag.id))
        .filter(
            and_(
                NFCTag.approved_at >= week_start.date(),
                NFCTag.approved_at < week_end.date(),
                NFCTag.approval_status == "approved",
            )
        )
        .scalar()
        or 0
    )

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
    _current_user: User = Depends(require_operator_or_admin),
) -> MonthlyStats:
    """Get monthly statistics (operator or admin only)."""
    try:
        year, month_num = map(int, month.split("-"))
        if month_num < 1 or month_num > MONTHS_PER_YEAR:
            raise ValueError("月份必须在1到12之间")
        month_start = datetime(year, month_num, 1, tzinfo=UTC)
        month_end = (
            datetime(year + 1, 1, 1)
            if month_num == MONTHS_PER_YEAR
            else datetime(year, month_num + 1, 1, tzinfo=UTC)
        )
    except (ValueError, IndexError) as e:
        raise ValueError("月份格式错误,请使用YYYY-MM格式") from e

    click_count = (
        db.query(func.count(TagClick.id))
        .filter(
            and_(
                TagClick.clicked_at >= month_start,
                TagClick.clicked_at < month_end,
            )
        )
        .scalar()
        or 0
    )

    new_tags = (
        db.query(func.count(NFCTag.id))
        .filter(
            and_(
                NFCTag.created_at >= month_start,
                NFCTag.created_at < month_end,
            )
        )
        .scalar()
        or 0
    )

    approved_tags = (
        db.query(func.count(NFCTag.id))
        .filter(
            and_(
                NFCTag.approved_at >= month_start.date(),
                NFCTag.approved_at < month_end.date(),
                NFCTag.approval_status == "approved",
            )
        )
        .scalar()
        or 0
    )

    return MonthlyStats(
        month=month,
        click_count=click_count,
        new_tags=new_tags,
        approved_tags=approved_tags,
    )
