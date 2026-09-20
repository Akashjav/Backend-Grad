"""Completion certificates, project milestones and training cohorts."""
from alembic import op
import sqlalchemy as sa

revision = "ga20_delivery"
down_revision = "ga20_platform"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("completion_certificates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id"), nullable=False, unique=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime()),
        sa.Column("revocation_reason", sa.Text()))
    op.create_table("project_milestones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("collaboration_id", sa.Integer(), sa.ForeignKey("collaborations.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("due_date", sa.DateTime()),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("evidence_url", sa.String(2000)),
        sa.Column("submission_note", sa.Text(), nullable=False),
        sa.Column("submitted_by", sa.Uuid(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("review_note", sa.Text(), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(as_uuid=False), sa.ForeignKey("users.id")))
    op.create_index("ix_project_milestones_collaboration_id", "project_milestones", ["collaboration_id"])
    op.create_table("training_programs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("institution_id", sa.Integer(), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("discipline_id", sa.Integer(), sa.ForeignKey("disciplines.id")),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("skill_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_training_programs_institution_id", "training_programs", ["institution_id"])
    op.create_table("training_enrollments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("program_id", sa.Integer(), sa.ForeignKey("training_programs.id"), nullable=False),
        sa.Column("student_id", sa.Uuid(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("baseline", sa.JSON(), nullable=False),
        sa.Column("outcome", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("completed_at", sa.DateTime()),
        sa.UniqueConstraint("program_id", "student_id"))
    op.create_index("ix_training_enrollments_program_id", "training_enrollments", ["program_id"])
    op.create_index("ix_training_enrollments_student_id", "training_enrollments", ["student_id"])
    op.create_table("practical_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reviewer_id", sa.Uuid(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("domain_id", sa.Integer(), sa.ForeignKey("domains.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("rubric", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False))
    op.create_index("ix_practical_assessments_reviewer_id", "practical_assessments", ["reviewer_id"])
    op.create_table("practical_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("practical_assessments.id"), nullable=False),
        sa.Column("student_id", sa.Uuid(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("evidence_url", sa.String(2000), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("scores", sa.JSON(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime()))
    op.create_index("ix_practical_submissions_assessment_id", "practical_submissions", ["assessment_id"])
    op.create_index("ix_practical_submissions_student_id", "practical_submissions", ["student_id"])


def downgrade():
    for name in ["practical_submissions", "practical_assessments", "training_enrollments", "training_programs", "project_milestones", "completion_certificates"]:
        op.drop_table(name)
