"""use native UUID ids for users, communities, and events

Revision ID: f6e7d8c9b0a1
Revises: a1b2c3d4e5f6
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "f6e7d8c9b0a1"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID_PATTERN = (
    "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    "[0-9a-f]{4}-[0-9a-f]{12}$"
)

ID_COLUMNS = (
    ("users", "id", "users"),
    ("communities", "id", "communities"),
    ("events", "id", "events"),
)

FK_COLUMNS = (
    ("profiles", "user_id", "users"),
    ("alumni_profiles", "user_id", "users"),
    ("conversations", "created_by", "users"),
    ("notifications", "user_id", "users"),
    ("messages", "author_id", "users"),
    ("community_memberships", "user_id", "users"),
    ("community_memberships", "community_id", "communities"),
    ("event_rsvps", "user_id", "users"),
    ("event_rsvps", "event_id", "events"),
)

FOREIGN_KEYS = (
    ("profiles_user_id_fkey", "profiles", "users", ["user_id"], ["id"]),
    ("alumni_profiles_user_id_fkey", "alumni_profiles", "users", ["user_id"], ["id"]),
    ("conversations_created_by_fkey", "conversations", "users", ["created_by"], ["id"]),
    ("notifications_user_id_fkey", "notifications", "users", ["user_id"], ["id"]),
    ("messages_author_id_fkey", "messages", "users", ["author_id"], ["id"]),
    ("community_memberships_user_id_fkey", "community_memberships", "users", ["user_id"], ["id"]),
    (
        "community_memberships_community_id_fkey",
        "community_memberships",
        "communities",
        ["community_id"],
        ["id"],
    ),
    ("event_rsvps_user_id_fkey", "event_rsvps", "users", ["user_id"], ["id"]),
    ("event_rsvps_event_id_fkey", "event_rsvps", "events", ["event_id"], ["id"]),
)


def _table_exists(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False

    return any(
        column["name"] == column_name
        for column in inspect(op.get_bind()).get_columns(table_name)
    )


def _drop_constraint_if_exists(table_name: str, constraint_name: str) -> None:
    op.execute(
        sa.text(
            f'ALTER TABLE "{table_name}" '
            f'DROP CONSTRAINT IF EXISTS "{constraint_name}"'
        )
    )


def _drop_managed_foreign_keys() -> None:
    for constraint_name, table_name, referred_table, local_cols, _ in FOREIGN_KEYS:
        if not _table_exists(table_name):
            continue

        for foreign_key in inspect(op.get_bind()).get_foreign_keys(table_name):
            if (
                foreign_key.get("constrained_columns") == local_cols
                and foreign_key.get("referred_table") == referred_table
                and foreign_key.get("name")
            ):
                _drop_constraint_if_exists(table_name, foreign_key["name"])

        _drop_constraint_if_exists(table_name, constraint_name)


def _create_managed_foreign_keys() -> None:
    for constraint_name, table_name, referred_table, local_cols, referred_cols in FOREIGN_KEYS:
        if not (_table_exists(table_name) and _table_exists(referred_table)):
            continue
        if not all(_column_exists(table_name, column) for column in local_cols):
            continue
        if not all(_column_exists(referred_table, column) for column in referred_cols):
            continue

        op.create_foreign_key(
            constraint_name,
            table_name,
            referred_table,
            local_cols,
            referred_cols,
        )


def _uuid_expression(column_name: str, namespace: str) -> str:
    column_ref = f'"{column_name}"'
    digest = f"md5('{namespace}:' || {column_ref}::text)"
    generated_uuid = (
        f"substr({digest}, 1, 8) || '-' || "
        f"substr({digest}, 9, 4) || '-' || "
        f"substr({digest}, 13, 4) || '-' || "
        f"substr({digest}, 17, 4) || '-' || "
        f"substr({digest}, 21, 12)"
    )

    return (
        f"CASE "
        f"WHEN {column_ref}::text ~* '{UUID_PATTERN}' THEN {column_ref}::uuid "
        f"ELSE ({generated_uuid})::uuid "
        f"END"
    )


def _convert_column_to_uuid(table_name: str, column_name: str, namespace: str) -> None:
    if not _column_exists(table_name, column_name):
        return

    expression = _uuid_expression(column_name, namespace)
    op.execute(
        sa.text(
            f'ALTER TABLE "{table_name}" '
            f'ALTER COLUMN "{column_name}" DROP DEFAULT'
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{table_name}" '
            f'ALTER COLUMN "{column_name}" TYPE uuid USING {expression}'
        )
    )


def _convert_column_to_string(table_name: str, column_name: str) -> None:
    if not _column_exists(table_name, column_name):
        return

    op.execute(
        sa.text(
            f'ALTER TABLE "{table_name}" '
            f'ALTER COLUMN "{column_name}" TYPE varchar USING "{column_name}"::text'
        )
    )


def _create_event_rsvps_if_missing() -> None:
    if _table_exists("event_rsvps"):
        return
    if not (_table_exists("events") and _table_exists("users")):
        return

    op.create_table(
        "event_rsvps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_event_rsvps_id"), "event_rsvps", ["id"], unique=False)


def upgrade() -> None:
    """Upgrade schema."""
    if op.get_bind().dialect.name != "postgresql":
        raise RuntimeError("Native UUID id migration currently supports PostgreSQL only")

    _drop_managed_foreign_keys()

    for table_name, column_name, namespace in ID_COLUMNS:
        _convert_column_to_uuid(table_name, column_name, namespace)

    for table_name, column_name, namespace in FK_COLUMNS:
        _convert_column_to_uuid(table_name, column_name, namespace)

    _create_event_rsvps_if_missing()
    _create_managed_foreign_keys()


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().dialect.name != "postgresql":
        raise RuntimeError("Native UUID id migration currently supports PostgreSQL only")

    _drop_managed_foreign_keys()

    for table_name, column_name, _ in FK_COLUMNS:
        _convert_column_to_string(table_name, column_name)

    for table_name, column_name, _ in ID_COLUMNS:
        _convert_column_to_string(table_name, column_name)

    _create_managed_foreign_keys()
