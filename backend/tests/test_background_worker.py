"""Tests for the background worker: process_one_job task dispatch.

Covers process_one_job for recalculate_analytics and generate_thumbnail,
the retry/dead-letter path, unknown task types, and fetch_pending_jobs
ordering used by the poll loop.
"""

from datetime import date, datetime, timedelta, timezone

import pytest
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.analytics.models import IssueFrequencyStats, RoomMonthlyStats
from app.modules.background import services
from app.modules.background.models import BackgroundJob
from app.modules.background.services import fetch_pending_jobs, process_one_job
from app.modules.inspection.models import Inspection, InspectionDetail, InspectionPhoto

from tests.conftest import create_user, seed_item, seed_room


async def _make_approved_inspection(
    db_session: AsyncSession,
    room_id: int,
    inspector_id: int,
    item_scores: list[tuple[int, int]],
    business_date: date | None = None,
) -> int:
    """Create an APPROVED inspection with details and commit (no analytics)."""
    insp = Inspection(
        room_id=room_id,
        inspector_id=inspector_id,
        status="APPROVED",
        business_date=business_date or date.today(),
        local_timestamp=datetime.now(timezone.utc),
    )
    for item_id, score in item_scores:
        insp.details.append(InspectionDetail(
            item_id=item_id,
            item_name_snapshot=f"Item {item_id}",
            score=score,
        ))
    db_session.add(insp)
    await db_session.commit()
    await db_session.refresh(insp)
    return insp.id


async def _add_job(db_session: AsyncSession, **kwargs) -> BackgroundJob:
    job = BackgroundJob(**kwargs)
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


# ── recalculate_analytics ──


@pytest.mark.asyncio
async def test_process_recalculate_analytics_job(db_session: AsyncSession):
    """process_one_job runs recalculate_analytics and completes the job."""
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "Ruang")
    item_ok = await seed_item(db_session, "Item Baik")
    item_bad = await seed_item(db_session, "Item Buruk")

    insp_id = await _make_approved_inspection(
        db_session, room.id, inspector.id,
        [(item_ok.id, 2), (item_bad.id, 0)],
        business_date=date(2026, 8, 5),
    )
    job = await _add_job(
        db_session, reference_id=insp_id, task_type="recalculate_analytics",
    )

    assert await process_one_job(db_session, job) is True
    await db_session.refresh(job)
    assert job.status == "COMPLETED"

    # RoomMonthlyStats upserted: total=2, max=2 items × 2 = 4, count=1
    stats = (await db_session.execute(select(RoomMonthlyStats))).scalars().all()
    assert len(stats) == 1
    assert stats[0].room_id == room.id
    assert stats[0].year_month == "2026-08"
    assert stats[0].total_score == 2
    assert stats[0].max_score == 4
    assert stats[0].inspection_count == 1

    # IssueFrequencyStats only for the zero-score item
    issues = (await db_session.execute(select(IssueFrequencyStats))).scalars().all()
    assert len(issues) == 1
    assert issues[0].item_id == item_bad.id
    assert issues[0].score_zero_count == 1


@pytest.mark.asyncio
async def test_process_recalculate_job_missing_inspection(db_session: AsyncSession):
    """A job whose inspection no longer exists is a no-op, still COMPLETED."""
    job = await _add_job(
        db_session, reference_id=99999, task_type="recalculate_analytics",
    )

    assert await process_one_job(db_session, job) is True
    await db_session.refresh(job)
    assert job.status == "COMPLETED"
    assert (await db_session.execute(
        select(func.count(RoomMonthlyStats.id))
    )).scalar() == 0


# ── generate_thumbnail ──


async def _seed_photo(
    db_session: AsyncSession,
    photo_file_name: str,
) -> tuple[int, int]:
    """Inspection + detail + photo row; returns (detail_id, photo_id)."""
    inspector = await create_user(db_session, "insp", "pass", "inspector")
    room = await seed_room(db_session, "Ruang")
    item = await seed_item(db_session, "Item")
    insp_id = await _make_approved_inspection(
        db_session, room.id, inspector.id, [(item.id, 2)],
    )
    detail = (await db_session.execute(
        select(InspectionDetail).where(InspectionDetail.inspection_id == insp_id)
    )).scalar_one()
    photo = InspectionPhoto(
        inspection_detail_id=detail.id,
        photo_file_name=photo_file_name,
    )
    db_session.add(photo)
    await db_session.commit()
    await db_session.refresh(photo)
    return detail.id, photo.id


@pytest.mark.asyncio
async def test_process_generate_thumbnail_job(
    db_session: AsyncSession, tmp_path, monkeypatch,
):
    """Generates a thumbnail file and records thumbnail_file_name."""
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    photo_name = "photo.jpg"
    Image.new("RGB", (60, 40), "blue").save(tmp_path / photo_name, "JPEG")

    _, photo_id = await _seed_photo(db_session, photo_name)
    job = await _add_job(
        db_session, reference_id=photo_id, task_type="generate_thumbnail",
    )

    assert await process_one_job(db_session, job) is True
    await db_session.refresh(job)
    photo = await db_session.get(InspectionPhoto, photo_id)

    assert job.status == "COMPLETED"
    assert photo.thumbnail_file_name == f"thumb_{photo_name}"
    assert (tmp_path / photo.thumbnail_file_name).is_file()


@pytest.mark.asyncio
async def test_process_generate_thumbnail_missing_file(
    db_session: AsyncSession, tmp_path, monkeypatch,
):
    """Photo row without a file on disk is a no-op, still COMPLETED."""
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    _, photo_id = await _seed_photo(db_session, "ghost.jpg")
    job = await _add_job(
        db_session, reference_id=photo_id, task_type="generate_thumbnail",
    )

    assert await process_one_job(db_session, job) is True
    await db_session.refresh(job)
    photo = await db_session.get(InspectionPhoto, photo_id)

    assert job.status == "COMPLETED"
    assert photo.thumbnail_file_name is None


# ── dispatch, retry, dead-letter ──


@pytest.mark.asyncio
async def test_process_unknown_task_type_fails(db_session: AsyncSession):
    """Unknown task_type → job FAILED, returns False."""
    job = await _add_job(db_session, reference_id=1, task_type="bogus_task")

    assert await process_one_job(db_session, job) is False
    await db_session.refresh(job)
    assert job.status == "FAILED"


@pytest.mark.asyncio
async def test_process_job_retries_then_dead_letters(
    db_session: AsyncSession, monkeypatch,
):
    """Failure retries up to max_retries, then dead-letters to FAILED."""

    async def _boom(_db, _inspection_id):
        raise RuntimeError("boom")

    monkeypatch.setattr(services, "recalculate_analytics", _boom)

    job = await _add_job(
        db_session, reference_id=1, task_type="recalculate_analytics",
        max_retries=2,
    )

    # Attempt 1 → retry (1/2)
    assert await process_one_job(db_session, job) is False
    await db_session.refresh(job)
    assert job.status == "PENDING"
    assert job.retry_count == 1

    # Attempt 2 → retry (2/2)
    assert await process_one_job(db_session, job) is False
    await db_session.refresh(job)
    assert job.status == "PENDING"
    assert job.retry_count == 2

    # Attempt 3 → dead-letter
    assert await process_one_job(db_session, job) is False
    await db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.retry_count == 2


# ── poll loop ──


@pytest.mark.asyncio
async def test_fetch_pending_jobs_oldest_first(db_session: AsyncSession):
    """fetch_pending_jobs returns only PENDING jobs, oldest created first."""
    base = datetime.now(timezone.utc)
    old = await _add_job(
        db_session, reference_id=1, task_type="recalculate_analytics",
        created_at=base - timedelta(minutes=10),
    )
    new = await _add_job(
        db_session, reference_id=2, task_type="generate_thumbnail",
        created_at=base,
    )
    done = await _add_job(
        db_session, reference_id=3, task_type="recalculate_analytics",
        status="COMPLETED", created_at=base - timedelta(hours=1),
    )

    jobs = await fetch_pending_jobs(db_session)
    assert [j.id for j in jobs] == [old.id, new.id]

    limited = await fetch_pending_jobs(db_session, limit=1)
    assert [j.id for j in limited] == [old.id]

    assert done.status == "COMPLETED"  # untouched by the query
