"""Async worker loop for processing background jobs (outbox pattern).

Run standalone:  uv run python -m app.modules.background.worker
Or via docker:  CMD ["python", "-m", "app.modules.background.worker"]
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.modules.background.services import fetch_pending_jobs, process_one_job

logger = logging.getLogger(__name__)

POLL_INTERVAL = 5  # seconds


async def run_worker_loop():
    logger.info("Background worker started (poll every %ss)", POLL_INTERVAL)
    while True:
        try:
            async with async_session() as db:
                jobs = await fetch_pending_jobs(db)
                for job in jobs:
                    success = await process_one_job(db, job)
                    logger.info("Job %s (%s): %s", job.id, job.task_type, "OK" if success else "FAILED")
        except Exception:
            logger.exception("Worker cycle error")
        await asyncio.sleep(POLL_INTERVAL)


async def run_once():
    """Process all pending jobs once, then exit. For cron-style usage."""
    async with async_session() as db:
        jobs = await fetch_pending_jobs(db)
        for job in jobs:
            success = await process_one_job(db, job)
            logger.info("Job %s (%s): %s", job.id, job.task_type, "OK" if success else "FAILED")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker_loop())
