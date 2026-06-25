"""add admin verification fields

Revision ID: bdad87a3b0a7
Revises: d4bd1c3cacb0
Create Date: 2026-06-25 02:10:51.921492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bdad87a3b0a7'
down_revision: Union[str, Sequence[str], None] = 'd4bd1c3cacb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'alumni_profiles',
        sa.Column('verified_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'events',
        sa.Column('status', sa.String(), nullable=False, server_default='draft')
    )
    op.alter_column('events', 'status', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('events', 'status')
    op.drop_column('alumni_profiles', 'verified_at')
