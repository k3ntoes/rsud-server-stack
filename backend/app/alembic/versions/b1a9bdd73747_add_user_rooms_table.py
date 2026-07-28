"""add user_rooms table

Revision ID: b1a9bdd73747
Revises: c3941b4c0503
Create Date: 2026-07-28 21:41:05.000880

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1a9bdd73747'
down_revision: Union[str, None] = 'c3941b4c0503'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('user_rooms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'room_id', name='uq_user_room')
    )
    # Auto-assign all active inspector/supervisor users to all active rooms
    op.execute("""
        INSERT INTO user_rooms (user_id, room_id, created_at)
        SELECT u.id, r.id, datetime('now')
        FROM users u, rooms r
        WHERE u.role IN ('inspector', 'supervisor')
          AND u.is_active = 1
          AND r.is_active = 1
    """)


def downgrade() -> None:
    op.drop_table('user_rooms')
