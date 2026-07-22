from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BackgroundJob(Base):
    __tablename__ = "background_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_id: Mapped[int] = mapped_column(Integer, nullable=False)  # FK to inspection/user/etc.
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)  # recalculate_analytics | generate_thumbnail
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING | PROCESSING | COMPLETED | FAILED
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
