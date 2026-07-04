from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    leetcode_id: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(255))
    approach: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    practice_sessions: Mapped[list["PracticeSession"]] = relationship("PracticeSession", back_populates="question")
    insight: Mapped["QuestionInsight | None"] = relationship(
        "QuestionInsight",
        back_populates="question",
        uselist=False,
    )
    review_schedule: Mapped["ReviewSchedule | None"] = relationship(
        "ReviewSchedule",
        back_populates="question",
        uselist=False,
    )

    @property
    def pattern(self) -> str:
        if self.insight is not None:
            return self.insight.pattern
        from app.services import detect_pattern

        return detect_pattern(self.approach)


class QuestionInsight(Base):
    __tablename__ = "question_insights"

    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), primary_key=True)
    pattern: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    question: Mapped[Question] = relationship("Question", back_populates="insight")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    question: Mapped[Question] = relationship("Question", back_populates="practice_sessions")
    evaluation: Mapped["RecallEvaluation | None"] = relationship(
        "RecallEvaluation",
        back_populates="session",
        uselist=False,
    )

    @property
    def prompt(self) -> str:
        from app.services import rephrase_question

        return rephrase_question(self.question.title, self.question.approach)

    @property
    def recall_attempt(self) -> str | None:
        return self.evaluation.recall_attempt if self.evaluation is not None else None

    @property
    def score(self) -> int | None:
        return self.evaluation.score if self.evaluation is not None else None

    @property
    def strengths(self) -> list[str]:
        if self.evaluation is None:
            return []
        return self.evaluation.strengths

    @property
    def missing_concepts(self) -> list[str]:
        if self.evaluation is None:
            return []
        return self.evaluation.missing_concepts

    @property
    def feedback(self) -> str | None:
        return self.evaluation.feedback if self.evaluation is not None else None

    @property
    def completed_at(self) -> datetime | None:
        return _ensure_aware(self.evaluation.created_at) if self.evaluation is not None else None

    @property
    def next_review_at(self) -> datetime | None:
        if self.question.review_schedule is None:
            return None
        return _ensure_aware(self.question.review_schedule.next_review_at)

    @property
    def is_due(self) -> bool:
        next_review_at = self.next_review_at
        return next_review_at is not None and next_review_at <= datetime.now(timezone.utc)


class RecallEvaluation(Base):
    __tablename__ = "recall_evaluations"

    session_id: Mapped[int] = mapped_column(ForeignKey("practice_sessions.id"), primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True, nullable=False)
    recall_attempt: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    strengths_json: Mapped[str] = mapped_column(Text, nullable=False)
    missing_concepts_json: Mapped[str] = mapped_column(Text, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    session: Mapped[PracticeSession] = relationship("PracticeSession", back_populates="evaluation")
    question: Mapped[Question] = relationship("Question")

    @property
    def strengths(self) -> list[str]:
        return json.loads(self.strengths_json)

    @property
    def missing_concepts(self) -> list[str]:
        return json.loads(self.missing_concepts_json)


class ReviewSchedule(Base):
    __tablename__ = "review_schedules"

    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), primary_key=True)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    question: Mapped[Question] = relationship("Question", back_populates="review_schedule")


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
