from datetime import date

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import RoomMonthlyStats, IssueFrequencyStats
from app.modules.auth.models import User
from app.modules.inspection.models import Inspection


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
