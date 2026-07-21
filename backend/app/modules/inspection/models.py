from datetime import date, datetime, timezone

from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    inspector_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING | APPROVED | REJECTED
    business_date: Mapped[date] = mapped_column(Date, nullable=False)
    local_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("room_id", "local_timestamp", "inspector_id", name="uq_inspection_submit"),
    )

    details: Mapped[list["InspectionDetail"]] = relationship(
        back_populates="inspection", cascade="all, delete-orphan"
    )


class InspectionDetail(Base):
    __tablename__ = "inspection_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("inspections.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("inspection_items.id"), nullable=False)
    item_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 | 1 | 2

    inspection: Mapped["Inspection"] = relationship(back_populates="details")
    photos: Mapped[list["InspectionPhoto"]] = relationship(
        back_populates="detail", cascade="all, delete-orphan"
    )


class InspectionPhoto(Base):
    __tablename__ = "inspection_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    inspection_detail_id: Mapped[int] = mapped_column(ForeignKey("inspection_details.id"), nullable=False)
    photo_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    thumbnail_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    detail: Mapped["InspectionDetail"] = relationship(back_populates="photos")
