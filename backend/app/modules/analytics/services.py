from datetime import date, datetime

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import RoomMonthlyStats, IssueFrequencyStats
from app.modules.auth.models import User
from app.modules.inspection.models import Inspection
from app.modules.master.models import Room


async def get_lowest_rooms(
    db: AsyncSession,
    year_month: str | None = None,
    limit: int = 3,
) -> list[RoomMonthlyStats]:
    query = select(RoomMonthlyStats).where(RoomMonthlyStats.max_score > 0)
    if year_month:
        query = query.where(RoomMonthlyStats.year_month == year_month)
    query = query.order_by(
        (RoomMonthlyStats.total_score / RoomMonthlyStats.max_score).asc()
    ).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_top_issues(
    db: AsyncSession,
    year_month: str | None = None,
    limit: int = 10,
) -> list[IssueFrequencyStats]:
    query = select(IssueFrequencyStats)
    if year_month:
        query = query.where(IssueFrequencyStats.year_month == year_month)
    query = query.order_by(desc(IssueFrequencyStats.score_zero_count)).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_inspector_performance(
    db: AsyncSession,
    year_month: str | None = None,
) -> list[dict]:
    query = select(
        User.id.label("inspector_id"),
        User.username,
        func.count(Inspection.id).label("total_inspections"),
    ).join(
        Inspection, Inspection.inspector_id == User.id
    ).where(
        User.role == "inspector",
        Inspection.status == "APPROVED",
    )
    if year_month:
        # Date-range filter — works on both SQLite and PostgreSQL (unlike .like())
        parts = year_month.split("-")
        start = date(int(parts[0]), int(parts[1]), 1)
        if int(parts[1]) == 12:
            end = date(int(parts[0]) + 1, 1, 1)
        else:
            end = date(int(parts[0]), int(parts[1]) + 1, 1)
        query = query.where(Inspection.business_date >= start, Inspection.business_date < end)
    query = query.group_by(User.id, User.username).order_by(desc("total_inspections"))
    result = await db.execute(query)
    rows = result.all()
    return [
        {"inspector_id": r.inspector_id, "username": r.username, "total_inspections": r.total_inspections}
        for r in rows
    ]


async def get_dashboard_summary(
    db: AsyncSession,
    year_month: str | None = None,
) -> dict:
    ym = year_month or datetime.now().strftime("%Y-%m")
    query = select(RoomMonthlyStats).where(RoomMonthlyStats.year_month == ym)
    result = await db.execute(query)
    rows = list(result.scalars().all())

    total_inspections = sum(r.inspection_count for r in rows)
    total_score = sum(r.total_score for r in rows)
    max_score = sum(r.max_score for r in rows)
    avg_pct = round(total_score / max_score * 100, 1) if max_score > 0 else 0.0

    return {
        "monthly_inspection_count": total_inspections,
        "avg_score_pct": avg_pct,
    }


async def get_dashboard_data(
    db: AsyncSession,
    year_month: str | None = None,
) -> dict:
    """Single endpoint for dashboard: pending count, room count, monthly stats.

    Falls back to the most recent month that has stats when the requested month
    has none, so a fresh month never shows an empty dashboard. Returns the
    effective ``year_month`` (``None`` when no stats exist at all).
    """
    ym = year_month or datetime.now().strftime("%Y-%m")

    # 1. Pending inspections count
    pending = await db.execute(
        select(func.count(Inspection.id)).where(Inspection.status == "PENDING")
    )
    pending_count = pending.scalar() or 0

    # 2. Active rooms count
    rooms = await db.execute(
        select(func.count(Room.id)).where(Room.is_active == True)
    )
    total_rooms = rooms.scalar() or 0

    # 3. Monthly stats from RoomMonthlyStats — fall back to the latest month
    #    with data (year_month is zero-padded "YYYY-MM", so max() is correct)
    stats = await db.execute(
        select(RoomMonthlyStats).where(RoomMonthlyStats.year_month == ym)
    )
    rows = list(stats.scalars().all())
    effective_ym = ym
    if not rows:
        latest = await db.execute(
            select(func.max(RoomMonthlyStats.year_month))
        )
        latest_ym = latest.scalar()
        if latest_ym:
            effective_ym = latest_ym
            stats = await db.execute(
                select(RoomMonthlyStats).where(RoomMonthlyStats.year_month == effective_ym)
            )
            rows = list(stats.scalars().all())

    monthly_inspections = sum(r.inspection_count for r in rows)
    total_score = sum(r.total_score for r in rows)
    max_score = sum(r.max_score for r in rows)
    avg_pct = round(total_score / max_score * 100, 1) if max_score > 0 else 0.0

    return {
        "pending_count": pending_count,
        "total_rooms": total_rooms,
        "monthly_inspection_count": monthly_inspections,
        "avg_score_pct": avg_pct,
        "year_month": effective_ym if rows else None,
    }
