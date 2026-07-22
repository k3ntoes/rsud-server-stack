import json
import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.background.models import BackgroundJob

logger = logging.getLogger(__name__)


async def create_job(
    db: AsyncSession,
    task_type: str,
    reference_id: int,
    payload: dict | None = None,
) -> BackgroundJob:
    job = BackgroundJob(
        reference_id=reference_id,
        task_type=task_type,
        payload=json.dumps(payload) if payload else None,
    )
    db.add(job)
    # No commit — caller controls transaction (atomicity with parent operation)
    return job


async def fetch_pending_jobs(db: AsyncSession, limit: int = 10) -> list[BackgroundJob]:
    result = await db.execute(
        select(BackgroundJob)
        .where(BackgroundJob.status == "PENDING")
        .order_by(BackgroundJob.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def mark_job(db: AsyncSession, job_id: int, status: str) -> None:
    job = await db.get(BackgroundJob, job_id)
    if job:
        job.status = status
        await db.commit()


async def recalculate_analytics(db: AsyncSession, inspection_id: int) -> None:
    """Recalculate analytics for an approved inspection."""
    from app.modules.inspection.models import Inspection, InspectionDetail

    inspection = await db.get(Inspection, inspection_id)
    if inspection is None:
        logger.warning("Inspection %s not found for analytics recalc", inspection_id)
        return

    # Extract year_month from business_date
    ym = _year_month(inspection.business_date)

    # Calculate scores
    result = await db.execute(
        select(InspectionDetail).where(InspectionDetail.inspection_id == inspection_id)
    )
    details = list(result.scalars().all())
    total = sum(d.score for d in details)
    max_possible = len(details) * 2

    # UPSERT room_monthly_stats
    from app.modules.analytics.models import RoomMonthlyStats

    r = await db.execute(
        select(RoomMonthlyStats).where(
            RoomMonthlyStats.room_id == inspection.room_id,
            RoomMonthlyStats.year_month == ym,
        )
    )
    stats = r.scalar_one_or_none()
    if stats:
        stats.total_score += total
        stats.max_score += max_possible
        stats.inspection_count += 1
    else:
        stats = RoomMonthlyStats(
            room_id=inspection.room_id,
            year_month=ym,
            total_score=total,
            max_score=max_possible,
            inspection_count=1,
        )
        db.add(stats)

    # UPSERT issue_frequency_stats for score==0 items
    from app.modules.analytics.models import IssueFrequencyStats

    zero_items = [d for d in details if d.score == 0]
    for d in zero_items:
        iq = await db.execute(
            select(IssueFrequencyStats).where(
                IssueFrequencyStats.item_id == d.item_id,
                IssueFrequencyStats.year_month == ym,
            )
        )
        issue = iq.scalar_one_or_none()
        if issue:
            issue.score_zero_count += 1
        else:
            issue = IssueFrequencyStats(
                item_id=d.item_id,
                item_name_snapshot=d.item_name_snapshot,
                year_month=ym,
                score_zero_count=1,
            )
            db.add(issue)

    await db.commit()


async def _generate_thumbnail(db: AsyncSession, photo_id: int) -> None:
    """Generate a thumbnail placeholder.

    ponytail: no-op until upload flow triggers thumbnail jobs.
    Add real resize (Pillow) when the trigger side lands.
    """
    logger.info("Thumbnail generation for photo %s: skipped (placeholder)", photo_id)


async def process_one_job(db: AsyncSession, job: BackgroundJob) -> bool:
    """Process a single job. Returns True if successful, False otherwise.

    ponytail: PROCESSING set in-memory only — final commit flushes it.
    If worker crashes before final commit, job stays PENDING (safe retry).
    On failure: retry up to max_retries. Dead-letter at max_retries.
    """
    job.status = "PROCESSING"

    try:
        if job.task_type == "recalculate_analytics":
            await recalculate_analytics(db, job.reference_id)
        elif job.task_type == "generate_thumbnail":
            await _generate_thumbnail(db, job.reference_id)
        else:
            logger.warning("Unknown task_type: %s", job.task_type)
            await mark_job(db, job.id, "FAILED")
            return False

        await mark_job(db, job.id, "COMPLETED")
        return True
    except Exception:
        logger.exception("Job %s failed", job.id)
        # Refresh job to avoid expired-object issues after previous commit
        job = await db.get(BackgroundJob, job.id)
        if job and job.retry_count < job.max_retries:
            job.retry_count += 1
            job.status = "PENDING"
            await db.commit()
            logger.info("Job %s will retry (%d/%d)", job.id, job.retry_count, job.max_retries)
            return False
        await mark_job(db, job.id, "FAILED")
        return False


def _year_month(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"
