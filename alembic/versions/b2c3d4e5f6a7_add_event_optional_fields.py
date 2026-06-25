"""add optional event fields

Revision ID: b2c3d4e5f6a7
Revises: f6e7d8c9b0a1
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "f6e7d8c9b0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(op.get_bind())
    if not inspector.has_table(table_name):
        return False

    return any(
        column["name"] == column_name
        for column in inspector.get_columns(table_name)
    )


def upgrade() -> None:
    """Upgrade schema."""
    if not _column_exists("events", "ends_at"):
        op.add_column("events", sa.Column("ends_at", sa.DateTime(), nullable=True))
    if not _column_exists("events", "host"):
        op.add_column("events", sa.Column("host", sa.String(), nullable=True))
    if not _column_exists("events", "audience"):
        op.add_column("events", sa.Column("audience", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    if _column_exists("events", "audience"):
        op.drop_column("events", "audience")
    if _column_exists("events", "host"):
        op.drop_column("events", "host")
    if _column_exists("events", "ends_at"):
        op.drop_column("events", "ends_at")
