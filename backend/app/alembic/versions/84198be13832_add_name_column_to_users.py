"""add name column to users

Revision ID: 84198be13832
Revises: b1a9bdd73747
Create Date: 2026-07-31 19:40:02.453261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84198be13832'
down_revision: Union[str, None] = 'b1a9bdd73747'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('name', sa.String(150), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'name')
