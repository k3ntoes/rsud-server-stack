from datetime import datetime, timezone

from sqlalchemy import Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RoomMonthlyStats(Base):
    __tablename__ = "room_monthly_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(Integer, nullable=False)
    year_month: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-07"
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[int] = mapped_column(Integer, default=0)
    inspection_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("room_id", "year_month", name="uq_room_month"),
    )


class IssueFrequencyStats(Base):
    __tablename__ = "issue_frequency_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    item_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    year_month: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-07"
    score_zero_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("item_id", "year_month", name="uq_item_month"),
    )
