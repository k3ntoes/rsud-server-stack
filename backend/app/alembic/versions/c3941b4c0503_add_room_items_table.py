"""add room_items table

Revision ID: c3941b4c0503
Revises: c2e9ef77ab08
Create Date: 2026-07-28 21:37:29.507151

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3941b4c0503'
down_revision: Union[str, None] = 'c2e9ef77ab08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('room_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['inspection_items.id'], ),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_id', 'item_id', name='uq_room_item')
    )
    # Auto-assign all active items to all active rooms (backward compat)
    op.execute("""
        INSERT INTO room_items (room_id, item_id, created_at)
        SELECT r.id, i.id, datetime('now')
        FROM rooms r, inspection_items i
        WHERE r.is_active = 1 AND i.is_active = 1
    """)


def downgrade() -> None:
    op.drop_table('room_items')
