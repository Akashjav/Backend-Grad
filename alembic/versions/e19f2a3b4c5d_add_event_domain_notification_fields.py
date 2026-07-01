"""add event domain notification fields

Revision ID: e19f2a3b4c5d
Revises: c0d0c9596c42
Create Date: 2026-07-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "e19f2a3b4c5d"
down_revision: Union[str, Sequence[str], None] = "c0d0c9596c42"
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
    if not _column_exists("events", "domain_id"):
        op.add_column(
            "events",
            sa.Column("domain_id", sa.Integer(), sa.ForeignKey("domains.id"), nullable=True),
        )
    if not _column_exists("events", "speaker_name"):
        op.add_column("events", sa.Column("speaker_name", sa.String(), nullable=True))
    if not _column_exists("events", "speaker_company"):
        op.add_column("events", sa.Column("speaker_company", sa.String(), nullable=True))
    if not _column_exists("events", "cover_image_url"):
        op.add_column("events", sa.Column("cover_image_url", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    if _column_exists("events", "cover_image_url"):
        op.drop_column("events", "cover_image_url")
    if _column_exists("events", "speaker_company"):
        op.drop_column("events", "speaker_company")
    if _column_exists("events", "speaker_name"):
        op.drop_column("events", "speaker_name")
    if _column_exists("events", "domain_id"):
        op.drop_column("events", "domain_id")
