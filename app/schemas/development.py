from datetime import datetime
from typing import Literal
from pydantic import Field, HttpUrl, field_validator
from app.schemas.platform import Input, Name, Score


class RevokeCertificate(Input):
    reason: str = Field(min_length=3, max_length=2000)


class MilestoneInput(Input):
    title: Name
    description: str = Field(default="", max_length=5000)
    due_date: datetime | None = None

    @field_validator("due_date")
    @classmethod
    def utc_date(cls, value):
        if value and value.tzinfo:
            from datetime import timezone
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value


class MilestoneSubmission(Input):
    evidence_url: HttpUrl
    submission_note: str = Field(min_length=1, max_length=5000)


class MilestoneReview(Input):
    status: Literal["accepted", "changes_requested"]
    review_note: str = Field(min_length=1, max_length=5000)


class TrainingInput(Input):
    title: Name
    description: str = Field(default="", max_length=5000)
    discipline_id: int | None = None
    skill_ids: list[int] = Field(min_length=1, max_length=100)


class TrainingStatus(Input):
    status: Literal["open", "closed"]


class PracticalInput(Input):
    domain_id: int
    title: Name
    instructions: str = Field(min_length=10, max_length=10000)
    rubric: dict[int, str] = Field(min_length=1, max_length=50)

    @field_validator("rubric")
    @classmethod
    def meaningful_criteria(cls, value):
        if any(not v.strip() or len(v) > 2000 for v in value.values()):
            raise ValueError("Each skill needs a non-empty rubric of up to 2000 characters")
        return value


class PracticalEvidence(Input):
    evidence_url: HttpUrl
    note: str = Field(min_length=1, max_length=5000)


class PracticalReview(Input):
    scores: dict[int, Score] = Field(min_length=1, max_length=50)
    feedback: str = Field(min_length=1, max_length=5000)
