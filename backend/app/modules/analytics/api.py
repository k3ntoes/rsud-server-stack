from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_supervisor_user
from app.modules.auth.models import User
from app.modules.analytics.schemas import RoomScoreOut, IssueFrequencyOut, InspectorPerformanceOut
from app.modules.analytics.services import get_lowest_rooms, get_top_issues, get_inspector_performance

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/lowest-rooms", response_model=list[RoomScoreOut])
async def lowest_rooms(
    year_month: str | None = Query(None, description="YYYY-MM, defaults to current"),
    limit: int = Query(3, le=20),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_supervisor_user),
):
    ym = year_month or datetime.now().strftime("%Y-%m")
    rows = await get_lowest_rooms(db, ym, limit)
    return [
        RoomScoreOut(
            room_id=r.room_id,
            year_month=r.year_month,
            total_score=r.total_score,
            max_score=r.max_score,
            score_pct=round(r.total_score / r.max_score * 100, 1) if r.max_score > 0 else 0,
            inspection_count=r.inspection_count,
        )
        for r in rows
    ]


@router.get("/top-issues", response_model=list[IssueFrequencyOut])
async def top_issues(
    year_month: str | None = Query(None, description="YYYY-MM, defaults to current"),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_supervisor_user),
):
    ym = year_month or datetime.now().strftime("%Y-%m")
    return await get_top_issues(db, ym, limit)


@router.get("/inspector-performance", response_model=list[InspectorPerformanceOut])
async def inspector_performance(
    year_month: str | None = Query(None, description="YYYY-MM, defaults to current"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_supervisor_user),
):
    ym = year_month or datetime.now().strftime("%Y-%m")
    return await get_inspector_performance(db, ym)
