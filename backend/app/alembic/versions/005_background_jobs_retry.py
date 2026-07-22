"""Add retry_count and max_retries to background_jobs

Revision ID: 005
Revises: 004
Create Date: 2026-07-22
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "background_jobs",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "background_jobs",
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
    )


def downgrade() -> None:
    op.drop_column("background_jobs", "max_retries")
    op.drop_column("background_jobs", "retry_count")
