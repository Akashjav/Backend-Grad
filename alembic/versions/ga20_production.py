"""Indexes for production query paths. Run once before serving traffic."""
from alembic import op

revision = "ga20_production"
down_revision = "ga20_delivery"
branch_labels = None
depends_on = None

INDEXES = [
    ("ix_messages_conversation_cursor", "messages", ["conversation_id", "id"]),
    ("ix_participants_user_conversation", "conversation_participants", ["user_id", "conversation_id"]),
    ("ix_opportunities_status_domain", "opportunities", ["status", "domain_id", "id"]),
    ("ix_challenges_user_purpose_used", "auth_challenges", ["user_id", "purpose", "used", "id"]),
    ("ix_outbox_pending", "mail_outbox", ["sent_at", "id"]),
    ("ix_feedback_application", "competency_feedback", ["application_id"]),
]


def upgrade():
    for name, table, columns in INDEXES:
        op.create_index(name, table, columns)


def downgrade():
    for name, table, _ in reversed(INDEXES):
        op.drop_index(name, table_name=table)
