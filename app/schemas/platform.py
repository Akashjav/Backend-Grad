from datetime import datetime, timezone
from typing import Annotated, Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

Name = Annotated[str, Field(min_length=1, max_length=200)]
Score = Annotated[float, Field(ge=0, le=100)]


class Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, allow_inf_nan=False
    )


class Signup(Input):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: Name
    role: Literal["student", "alumni", "academician", "industry"] = "student"
    domain_id: int
    discipline_id: int | None = None


class Signin(Input):
    email: EmailStr
    password: str


class Refresh(Input):
    refresh_token: str


class Email(Input):
    email: EmailStr


class OTP(Email):
    code: str = Field(min_length=6, max_length=128)


class Reset(OTP):
    password: str = Field(min_length=10, max_length=128)


class DomainInput(Input):
    name: Name
    description: str | None = None


class DisciplineInput(Input):
    name: Name
    domain_id: int


class SkillInput(DisciplineInput):
    category: Name = "domain"
    aliases: list[Name] = Field(default_factory=list, max_length=30)
    related_skill_ids: list[int] = Field(default_factory=list, max_length=30)


class CompetencyInput(DisciplineInput):
    skill_weights: dict[int, Annotated[float, Field(gt=0)]] = Field(
        min_length=1, max_length=100
    )


class ProfileUpdate(Input):
    display_name: Name | None = None
    domain_id: int | None = None
    discipline_id: int | None = None
    interests: list[Name] | None = None
    bio: str | None = Field(default=None, max_length=5000)
    organization_name: Name | None = None
    publications: list[Name] | None = None
    discoverable: bool | None = None


class SkillClaim(Input):
    skill_id: int
    score: Score = 0


class SkillsUpdate(Input):
    skills: list[SkillClaim] = Field(max_length=100)


class ProfileItemInput(Input):
    title: Name
    description: str = Field(default="", max_length=5000)
    skill_ids: list[int] = Field(default_factory=list, max_length=100)
    url: HttpUrl | None = None


class Question(Input):
    id: Name
    prompt: Name
    options: list[Name] = Field(min_length=2, max_length=10)
    answer: int = Field(ge=0)
    skill_id: int
    weight: float = Field(default=1, gt=0, le=100)

    @model_validator(mode="after")
    def valid_answer(self):
        if self.answer >= len(self.options):
            raise ValueError("Answer index is outside the options")
        return self


class AssessmentInput(Input):
    domain_id: int
    title: Name
    duration_minutes: int = Field(default=30, ge=1, le=180)
    questions: list[Question] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_questions(self):
        if len({q.id for q in self.questions}) != len(self.questions):
            raise ValueError("Question IDs must be unique")
        return self


class Submission(Input):
    attempt_id: int
    answers: dict[str, int] = Field(max_length=100)


class OpportunityInput(Input):
    domain_id: int
    discipline_id: int | None = None
    title: Name
    description: str = Field(min_length=1, max_length=20000)
    kind: Literal[
        "job",
        "internship",
        "project",
        "research",
        "consultancy",
        "fdp",
        "faculty_internship",
        "workshop",
    ] = "internship"
    location: Name = "Remote"
    duration_weeks: int | None = Field(default=None, ge=1, le=260)
    deadline: datetime | None = None
    interests: list[Name] = Field(default_factory=list, max_length=30)
    cross_domain: bool = False

    @field_validator("deadline")
    @classmethod
    def utc_date(cls, value):
        if value and value.tzinfo:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value


class OpportunityPatch(Input):
    title: Name | None = None
    description: str | None = Field(default=None, min_length=1, max_length=20000)
    location: Name | None = None
    interests: list[Name] | None = None


class RequirementInput(Input):
    skill_id: int
    level: float = Field(gt=0, le=100)
    weight: float = Field(default=1, gt=0, le=100)
    core: bool = True


class ApplicationUpdate(Input):
    status: Literal[
        "shortlisted",
        "interview",
        "selected",
        "started",
        "completed",
        "rejected",
        "withdrawn",
    ]
    mentor_id: str | None = None


class ProgressInput(Input):
    progress: int = Field(ge=0, le=100)


class FeedbackInput(Input):
    scores: dict[int, Score] = Field(min_length=1, max_length=100)
    comment: str = Field(min_length=1, max_length=5000)


class LearningInput(Input):
    skill_id: int
    title: Name
    url: HttpUrl
    kind: Literal["course", "project", "article", "workshop"] = "course"
    target_level: Score = 60


class CollaborationInput(Input):
    opportunity_id: int
    title: Name


class Invite(Input):
    user_id: str
    role: Literal["member", "mentor"] = "member"


class CollaborationPatch(ProgressInput):
    status: Literal["active", "completed"] = "active"


class Extraction(Input):
    text: str = Field(min_length=1, max_length=50000)
    domain_id: int | None = None


class ResumeExtraction(Input):
    document_id: int


class RoleUpdate(Input):
    role: Literal[
        "student",
        "alumni",
        "academician",
        "industry",
        "institution_admin",
        "super_admin",
    ]
    institution_id: int | None = None


class InstitutionAssignment(Input):
    institution_id: int


class DomainWeights(Input):
    readiness_weights: dict[str, Annotated[float, Field(gt=0)]] = Field(min_length=1)
    matching_weights: dict[str, Annotated[float, Field(ge=0)]]

    @model_validator(mode="after")
    def valid_weights(self):
        if set(self.matching_weights) != {
            "skill",
            "core",
            "project",
            "interest",
            "eligibility",
        }:
            raise ValueError(
                "Matching requires skill, core, project, interest, eligibility weights"
            )
        if abs(sum(self.matching_weights.values()) - 1) > 0.0001:
            raise ValueError("Matching weights must sum to one")
        return self
