from sqlalchemy import select, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import RoomMonthlyStats, IssueFrequencyStats


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
