"""Worker healthcheck — fail when background jobs are stuck PENDING.

Runs as the Docker healthcheck for the rsud-worker container (via the
``healthcheck`` entrypoint passthrough in docker-entrypoint.sh). Exits 0
when no PENDING job is older than ``WORKER_HEALTH_STALE_MINUTES`` (default
5), exits 1 otherwise so Docker / Portainer flag the worker as unhealthy.

Why this detects a broken worker: approvals only *create* a
``recalculate_analytics`` job (outbox pattern); the worker polls every 5s and
dead-letters failing jobs after ``max_retries``. A job that stays PENDING for
minutes therefore means the worker is not making progress — down,
crash-looping, or unable to reach the DB.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.modules.background.models import BackgroundJob

STALE_MINUTES = int(os.getenv("WORKER_HEALTH_STALE_MINUTES", "5"))


async def count_stale_jobs(db: AsyncSession, stale_minutes: int = STALE_MINUTES) -> int:
    """Count PENDING jobs created more than ``stale_minutes`` ago."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)
    result = await db.execute(
        select(func.count(BackgroundJob.id)).where(
            BackgroundJob.status == "PENDING",
            BackgroundJob.created_at < cutoff,
        )
    )
    return result.scalar() or 0


async def main() -> int:
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as db:
            stuck = await count_stale_jobs(db, STALE_MINUTES)
    except Exception as exc:  # noqa: BLE001 — healthcheck must never crash silently
        print(f"UNHEALTHY: cannot query background_jobs: {exc}")
        return 1
    finally:
        await engine.dispose()

    if stuck:
        print(
            f"UNHEALTHY: {stuck} PENDING job(s) older than {STALE_MINUTES} min "
            f"— worker not processing"
        )
        return 1
    print("OK: no stale PENDING jobs")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
