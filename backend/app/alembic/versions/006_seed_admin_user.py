"""Seed admin PPI user

Revision ID: 006
Revises: 005
Create Date: 2026-07-22
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa

from app.core.security import hash_password

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT id FROM users WHERE username = 'admin'")
    )
    if result.fetchone() is None:
        conn.execute(
            sa.text(
                "INSERT INTO users (username, password_hash, role, is_active) "
                "VALUES ('admin', :hash, 'admin_ppi', 1)"
            ).bindparams(hash=hash_password("admin123"))
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM users WHERE username = 'admin' AND role = 'admin_ppi'")
    )
