"""Create inspections, inspection_details, inspection_photos

Revision ID: 003
Revises: 002
Create Date: 2026-07-22
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "inspections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("inspector_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("local_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_id", "local_timestamp", "inspector_id", name="uq_inspection_submit"),
    )

    op.create_table(
        "inspection_details",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("inspection_id", sa.Integer(), sa.ForeignKey("inspections.id"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("inspection_items.id"), nullable=False),
        sa.Column("item_name_snapshot", sa.String(200), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "inspection_photos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("inspection_detail_id", sa.Integer(), sa.ForeignKey("inspection_details.id"), nullable=False),
        sa.Column("photo_file_name", sa.String(255), nullable=False),
        sa.Column("thumbnail_file_name", sa.String(255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("inspection_photos")
    op.drop_table("inspection_details")
    op.drop_table("inspections")
