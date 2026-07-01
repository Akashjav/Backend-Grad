from app.models.user import User
from app.models.profile import Profile
from app.models.alumni import AlumniProfile
from app.models.community import Community
from app.models.events import Event
from app.models.conversation import Conversation, Message
from app.models.notification import Notification
from app.models.community import Community, CommunityMembership
from app.models.events import Event, EventRSVP
from app.models.conversation import Conversation, ConversationParticipant, Message
from app.models.settings import (
    UserPrivacySettings,
    UserNotificationPreferences,
    UserSecuritySettings,
    UserLanguageSettings
)
from app.models.student import StudentProfile
from app.models.alumni import AlumniProfile
from app.models.student_document import StudentDocument
from app.models.mentorship import MentorshipRequest, MentorshipSession
from app.models.job import Job, SavedJob, JobApplication
from app.models.community import (
    Community,
    CommunityMembership,
    CommunityPost,
    CommunityPostLike,
    CommunityPostReply
)
from app.models.subscription import Domain, SubscriptionPlan, Subscription, Payment
from app.models.alumni_payment import AlumniEarning, AlumniPayout
from app.models.ai_chat import AIChatMessage