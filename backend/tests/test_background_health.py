"""Tests for the background-worker healthcheck (stale PENDING job detection)."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.background.healthcheck import count_stale_jobs
from app.modules.background.models import BackgroundJob


def _job(status: str, minutes_old: int, task_type: str = "recalculate_analytics") -> BackgroundJob:
    return BackgroundJob(
        reference_id=1,
        task_type=task_type,
        status=status,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_old),
    )


@pytest.mark.asyncio
async def test_no_jobs_is_healthy(db_session: AsyncSession):
    """Empty job table → 0 stale jobs."""
    assert await count_stale_jobs(db_session, stale_minutes=5) == 0


@pytest.mark.asyncio
async def test_fresh_pending_job_not_stale(db_session: AsyncSession):
    """A PENDING job younger than the threshold is not stale."""
    db_session.add(_job("PENDING", minutes_old=1))
    await db_session.commit()
    assert await count_stale_jobs(db_session, stale_minutes=5) == 0


@pytest.mark.asyncio
async def test_stale_pending_job_detected(db_session: AsyncSession):
    """A PENDING job older than the threshold is flagged."""
    db_session.add(_job("PENDING", minutes_old=10))
    await db_session.commit()
    assert await count_stale_jobs(db_session, stale_minutes=5) == 1


@pytest.mark.asyncio
async def test_only_pending_status_counts(db_session: AsyncSession):
    """COMPLETED/FAILED jobs are never flagged, however old."""
    db_session.add(_job("COMPLETED", minutes_old=120))
    db_session.add(_job("FAILED", minutes_old=120))
    db_session.add(_job("PENDING", minutes_old=10))
    await db_session.commit()
    assert await count_stale_jobs(db_session, stale_minutes=5) == 1


@pytest.mark.asyncio
async def test_threshold_editable(db_session: AsyncSession):
    """Raising the threshold can clear a borderline job."""
    db_session.add(_job("PENDING", minutes_old=6))
    await db_session.commit()
    assert await count_stale_jobs(db_session, stale_minutes=5) == 1
    assert await count_stale_jobs(db_session, stale_minutes=10) == 0
