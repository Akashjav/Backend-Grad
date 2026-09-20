"""Additive GradAlumni 2.0 entities; existing foundation tables are retained."""

from datetime import datetime
from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    DateTime,
    Integer,
    Float,
    Boolean,
    JSON,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class Institution(Base):
    __tablename__ = "institutions"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str | None] = mapped_column(Text)


class Discipline(Base):
    __tablename__ = "disciplines"
    __table_args__ = (UniqueConstraint("domain_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))


class DomainPolicy(Base):
    __tablename__ = "domain_policies"
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"), primary_key=True)
    readiness_weights: Mapped[dict] = mapped_column(JSON, default=dict)
    matching_weights: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "skill": 0.4,
            "core": 0.25,
            "project": 0.15,
            "interest": 0.1,
            "eligibility": 0.1,
        },
    )


class DomainProfile(Base):
    __tablename__ = "domain_profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    domain_id: Mapped[int | None] = mapped_column(ForeignKey("domains.id"), index=True)
    discipline_id: Mapped[int | None] = mapped_column(ForeignKey("disciplines.id"))
    institution_id: Mapped[int | None] = mapped_column(
        ForeignKey("institutions.id"), index=True
    )
    interests: Mapped[list] = mapped_column(JSON, default=list)
    bio: Mapped[str] = mapped_column(Text, default="")
    organization_name: Mapped[str | None] = mapped_column(String(200))
    publications: Mapped[list] = mapped_column(JSON, default=list)
    discoverable: Mapped[bool] = mapped_column(Boolean, default=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class AuthChallenge(Base):
    __tablename__ = "auth_challenges"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(30))
    token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)


class MailOutbox(Base):
    __tablename__ = "mail_outbox"
    id: Mapped[int] = mapped_column(primary_key=True)
    recipient: Mapped[str] = mapped_column(String)
    subject: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100))
    target: Mapped[str] = mapped_column(String(200))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("domain_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(100), default="domain")
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    related_skill_ids: Mapped[list] = mapped_column(JSON, default=list)


class Competency(Base):
    __tablename__ = "competencies"
    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    skill_weights: Mapped[dict] = mapped_column(JSON)


class StudentSkill(Base):
    __tablename__ = "student_skills"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id"),
        CheckConstraint("score >= 0 AND score <= 100"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    score: Mapped[float] = mapped_column(Float, default=0)
    evidence_type: Mapped[str] = mapped_column(String(40), default="self_declared")
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProfileItem(Base):
    __tablename__ = "profile_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    skill_ids: Mapped[list] = mapped_column(JSON, default=list)
    url: Mapped[str | None] = mapped_column(String)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    questions: Mapped[list] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1)


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"))
    question_snapshot: Mapped[list] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)


class Opportunity(Base):
    __tablename__ = "opportunities"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"), index=True)
    discipline_id: Mapped[int | None] = mapped_column(ForeignKey("disciplines.id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(30), default="internship")
    location: Mapped[str] = mapped_column(String(200), default="Remote")
    duration_weeks: Mapped[int | None] = mapped_column(Integer)
    deadline: Mapped[datetime | None] = mapped_column(DateTime)
    interests: Mapped[list] = mapped_column(JSON, default=list)
    cross_domain: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    approved: Mapped[bool] = mapped_column(Boolean, default=False)


class Requirement(Base):
    __tablename__ = "opportunity_requirements"
    __table_args__ = (UniqueConstraint("opportunity_id", "skill_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey("opportunities.id"), index=True
    )
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    level: Mapped[float] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float, default=1)
    core: Mapped[bool] = mapped_column(Boolean, default=True)


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("opportunity_id", "student_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey("opportunities.id"), index=True
    )
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="applied")
    mentor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    progress: Mapped[int] = mapped_column(Integer, default=0)
    certificate: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MatchResult(Base):
    __tablename__ = "match_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"))
    score: Mapped[float] = mapped_column(Float)
    explanation: Mapped[dict] = mapped_column(JSON)
    algorithm: Mapped[str] = mapped_column(String(80), default="weighted-skills-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SkillGap(Base):
    __tablename__ = "skill_gaps"
    __table_args__ = (UniqueConstraint("student_id", "opportunity_id", "skill_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    current_level: Mapped[float] = mapped_column(Float)
    required_level: Mapped[float] = mapped_column(Float)
    gap_score: Mapped[float] = mapped_column(Float)
    priority: Mapped[str] = mapped_column(String(10))


class ReadinessSnapshot(Base):
    __tablename__ = "readiness_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    components: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LearningResource(Base):
    __tablename__ = "learning_resources"
    id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String(30), default="course")
    target_level: Mapped[float] = mapped_column(Float, default=60)


class LearningProgress(Base):
    __tablename__ = "learning_progress"
    __table_args__ = (UniqueConstraint("user_id", "resource_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("learning_resources.id"))
    status: Mapped[str] = mapped_column(String(30), default="started")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class Collaboration(Base):
    __tablename__ = "collaborations"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"))
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="active")
    progress: Mapped[int] = mapped_column(Integer, default=0)


class CollaborationMember(Base):
    __tablename__ = "collaboration_members"
    __table_args__ = (UniqueConstraint("collaboration_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    collaboration_id: Mapped[int] = mapped_column(ForeignKey("collaborations.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(30), default="member")
    status: Mapped[str] = mapped_column(String(30), default="invited")


class Feedback(Base):
    __tablename__ = "competency_feedback"
    __table_args__ = (UniqueConstraint("reviewer_id", "application_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    scores: Mapped[dict] = mapped_column(JSON)
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ResumeDocument(Base):
    __tablename__ = "resume_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    storage_name: Mapped[str] = mapped_column(String, unique=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
