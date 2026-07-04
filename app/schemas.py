from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class QuestionCreate(BaseModel):
    leetcode_id: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=255)
    approach: str = Field(min_length=1)


class QuestionRead(BaseModel):
    id: int
    leetcode_id: str
    title: str
    approach: str
    created_at: datetime
    pattern: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PracticeSessionRead(BaseModel):
    id: int
    question: QuestionRead
    prompt: str
    recall_attempt: str | None = None
    score: int | None = None
    strengths: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    feedback: str | None = None
    completed_at: datetime | None = None
    next_review_at: datetime | None = None
    is_due: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecallAttemptCreate(BaseModel):
    recall_attempt: str = Field(min_length=1)


class RecallEvaluationRead(BaseModel):
    session_id: int
    question_id: int
    recall_attempt: str
    score: int
    strengths: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    feedback: str
    next_review_at: datetime
    review_count: int
    interval_days: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewScheduleRead(BaseModel):
    question_id: int
    interval_days: int
    review_count: int
    last_score: int
    next_review_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
