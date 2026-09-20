"""Delivery evidence and institution training interventions."""
from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class CompletionCertificate(Base):
    __tablename__ = "completion_certificates"
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), unique=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    snapshot: Mapped[dict] = mapped_column(JSON)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
    revocation_reason: Mapped[str | None] = mapped_column(Text)


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"
    id: Mapped[int] = mapped_column(primary_key=True)
    collaboration_id: Mapped[int] = mapped_column(ForeignKey("collaborations.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    evidence_url: Mapped[str | None] = mapped_column(String(2000))
    submission_note: Mapped[str] = mapped_column(Text, default="")
    submitted_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    review_note: Mapped[str] = mapped_column(Text, default="")
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))


class TrainingProgram(Base):
    __tablename__ = "training_programs"
    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), index=True)
    discipline_id: Mapped[int | None] = mapped_column(ForeignKey("disciplines.id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    skill_ids: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TrainingEnrollment(Base):
    __tablename__ = "training_enrollments"
    __table_args__ = (UniqueConstraint("program_id", "student_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("training_programs.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    baseline: Mapped[dict] = mapped_column(JSON)
    outcome: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="enrolled")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class PracticalAssessment(Base):
    __tablename__ = "practical_assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"))
    title: Mapped[str] = mapped_column(String(200))
    instructions: Mapped[str] = mapped_column(Text)
    rubric: Mapped[dict] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(default=True)


class PracticalSubmission(Base):
    __tablename__ = "practical_submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("practical_assessments.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    evidence_url: Mapped[str] = mapped_column(String(2000))
    note: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="submitted")
    scores: Mapped[dict] = mapped_column(JSON, default=dict)
    feedback: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
