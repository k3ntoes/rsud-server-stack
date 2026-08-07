"""add sort_order to room_items (ADR-0013)

Revision ID: 008
Revises: 007
Create Date: 2026-08-07

Alasan (ADR-0013):
- Kolom `sort_order` di pivot `room_items` mengatur urutan tampilan item
  inspeksi per ruangan (diatur Admin PPI via web-admin).
- Backfill `sort_order = item_id` agar urutan tampilan existing tidak berubah
  setelah deploy (dulu tidak ada ORDER BY → urutan praktis mengikuti id).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "room_items",
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    # Backfill: sort_order = item_id → urutan tampilan saat ini tidak berubah
    op.execute("UPDATE room_items SET sort_order = item_id")


def downgrade() -> None:
    op.drop_column("room_items", "sort_order")
