"""soft-delete + updated_at on pivot tables (room_items, user_rooms)

Revision ID: 007
Revises: 84198be13832
Create Date: 2026-08-01

Alasan (ADR-0009 / ADR-0010):
- Unassign sebelumnya hard-delete → sync incremental Android (`?since=`)
  tidak pernah melihat penghapusan → jumlah item di room tidak berubah.
- Kini unassign = soft delete (is_active=False) + updated_at dibump, sehingga
  sync `/api/room-items?since=` dan `/api/auth/user-rooms?since=` bisa
  mengirim tombstone ke Android.
- `updated_at` di-backfill dari `created_at` agar baris lama ikut terkirim.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: Union[str, None] = "84198be13832"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "room_items",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "room_items",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_rooms",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "user_rooms",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Backfill: baris lama dapat updated_at = created_at (bukan NULL)
    op.execute("UPDATE room_items SET updated_at = created_at WHERE updated_at IS NULL")
    op.execute("UPDATE user_rooms SET updated_at = created_at WHERE updated_at IS NULL")


def downgrade() -> None:
    op.drop_column("user_rooms", "updated_at")
    op.drop_column("user_rooms", "is_active")
    op.drop_column("room_items", "updated_at")
    op.drop_column("room_items", "is_active")
