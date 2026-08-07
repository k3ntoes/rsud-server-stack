from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Wajib terisi sejak dibuat — sync incremental Android memfilter berdasarkan kolom ini
    # (lihat kontrak sync di docs). Kolom tetap nullable agar tidak memutus data lama yang
    # belum backfill; service layer yang menjamin tidak pernah menyimpan NULL baru.
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=True
    )


class InspectionItem(Base):
    __tablename__ = "inspection_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Wajib terisi sejak dibuat — sync incremental Android memfilter berdasarkan kolom ini
    # (lihat kontrak sync di docs). Kolom tetap nullable agar tidak memutus data lama yang
    # belum backfill; service layer yang menjamin tidak pernah menyimpan NULL baru.
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=True
    )


class RoomItem(Base):
    __tablename__ = "room_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("inspection_items.id"), nullable=False)
    # Urutan tampilan item dalam checklist inspeksi ruangan (ADR-0013) — diatur
    # Admin PPI via web-admin (tombol ▲/▼). Query memakai sort_order ASC, item_id ASC.
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    # Soft-delete tombstone — unassign menandai is_active=False (bukan hard delete)
    # agar sync incremental Android bisa melihat penghapusan relasi (ADR-0009).
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Dibump saat assign/ubah/unassign — sync Android memfilter kolom ini.
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("room_id", "item_id", name="uq_room_item"),
    )
