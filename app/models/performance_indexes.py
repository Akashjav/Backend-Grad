"""Indexes for bounded message polling, candidate listing and authentication."""
from sqlalchemy import Index
from app.models.conversation import Message, ConversationParticipant
from app.models.platform import Opportunity, AuthChallenge, MailOutbox, Feedback

Index("ix_messages_conversation_cursor", Message.conversation_id, Message.id)
Index("ix_participants_user_conversation", ConversationParticipant.user_id, ConversationParticipant.conversation_id)
Index("ix_opportunities_status_domain", Opportunity.status, Opportunity.domain_id, Opportunity.id)
Index("ix_challenges_user_purpose_used", AuthChallenge.user_id, AuthChallenge.purpose, AuthChallenge.used, AuthChallenge.id)
Index("ix_outbox_pending", MailOutbox.sent_at, MailOutbox.id)
Index("ix_feedback_application", Feedback.application_id)
