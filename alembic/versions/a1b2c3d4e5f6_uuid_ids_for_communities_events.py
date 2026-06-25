"""switch communities and events ids to UUID strings

Revision ID: a1b2c3d4e5f6
Revises: 10c0ffa66793
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '10c0ffa66793'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if op.get_bind().dialect.name == 'postgresql':
        if op.get_bind().dialect.has_table(op.get_bind(), 'community_memberships'):
            op.execute('ALTER TABLE community_memberships DROP CONSTRAINT IF EXISTS community_memberships_community_id_fkey')
        if op.get_bind().dialect.has_table(op.get_bind(), 'event_rsvps'):
            op.execute('ALTER TABLE event_rsvps DROP CONSTRAINT IF EXISTS event_rsvps_event_id_fkey')

    if op.get_bind().dialect.has_table(op.get_bind(), 'communities'):
        op.execute("ALTER TABLE communities ALTER COLUMN id TYPE VARCHAR USING id::text")
    if op.get_bind().dialect.has_table(op.get_bind(), 'events'):
        op.execute("ALTER TABLE events ALTER COLUMN id TYPE VARCHAR USING id::text")
    if op.get_bind().dialect.has_table(op.get_bind(), 'community_memberships'):
        op.execute("ALTER TABLE community_memberships ALTER COLUMN community_id TYPE VARCHAR USING community_id::text")
    if op.get_bind().dialect.has_table(op.get_bind(), 'event_rsvps'):
        op.execute("ALTER TABLE event_rsvps ALTER COLUMN event_id TYPE VARCHAR USING event_id::text")

    if op.get_bind().dialect.has_table(op.get_bind(), 'community_memberships'):
        op.create_foreign_key(
            'community_memberships_community_id_fkey',
            'community_memberships',
            'communities',
            ['community_id'],
            ['id'],
        )
    if op.get_bind().dialect.has_table(op.get_bind(), 'event_rsvps'):
        op.create_foreign_key(
            'event_rsvps_event_id_fkey',
            'event_rsvps',
            'events',
            ['event_id'],
            ['id'],
        )


def downgrade() -> None:
    if op.get_bind().dialect.has_table(op.get_bind(), 'event_rsvps'):
        op.drop_constraint('event_rsvps_event_id_fkey', 'event_rsvps', type_='foreignkey')
    if op.get_bind().dialect.has_table(op.get_bind(), 'community_memberships'):
        op.drop_constraint('community_memberships_community_id_fkey', 'community_memberships', type_='foreignkey')

    if op.get_bind().dialect.has_table(op.get_bind(), 'event_rsvps'):
        op.execute("ALTER TABLE event_rsvps ALTER COLUMN event_id TYPE INTEGER USING event_id::integer")
    if op.get_bind().dialect.has_table(op.get_bind(), 'community_memberships'):
        op.execute("ALTER TABLE community_memberships ALTER COLUMN community_id TYPE INTEGER USING community_id::integer")
    if op.get_bind().dialect.has_table(op.get_bind(), 'events'):
        op.execute("ALTER TABLE events ALTER COLUMN id TYPE INTEGER USING id::integer")
    if op.get_bind().dialect.has_table(op.get_bind(), 'communities'):
        op.execute("ALTER TABLE communities ALTER COLUMN id TYPE INTEGER USING id::integer")
