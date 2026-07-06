from __future__ import annotations

import json
import os
import random
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import Base, engine, get_db
from app.models import PracticeSession, Question, QuestionInsight, RecallEvaluation, ReviewSchedule
from app.schemas import (
    PracticeSessionRead,
    QuestionCreate,
    QuestionRead,
    RecallAttemptCreate,
    RecallEvaluationRead,
    ReviewScheduleRead,
)
from app.services import build_review_schedule, detect_pattern, evaluate_recall, now_utc

app = FastAPI(title="DSA Memory Trainer API")
Base.metadata.create_all(bind=engine)


def _load_question_query(db: Session):
    return db.query(Question).options(joinedload(Question.insight), joinedload(Question.review_schedule))


def _load_practice_session_query(db: Session):
    return db.query(PracticeSession).options(
        joinedload(PracticeSession.question).joinedload(Question.insight),
        joinedload(PracticeSession.question).joinedload(Question.review_schedule),
        joinedload(PracticeSession.evaluation),
    )


def _normalize_required_field(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question fields cannot be blank")
    return cleaned


@app.get("/health")
def health() -> dict:
    ai_provider = os.getenv("AI_PROVIDER", "ollama")
    return {
        "status": "ok",
        "database": "sqlite",
        "ai_provider": ai_provider,
        "ollama_model": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
        "transformers_model": os.getenv("TRANSFORMERS_MODEL", "WeiboAI/VibeThinker-3B")
        if ai_provider == "transformers"
        else None,
    }


@app.post("/questions", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)) -> Question:
    question = Question(
        leetcode_id=_normalize_required_field(payload.leetcode_id),
        title=_normalize_required_field(payload.title),
        approach=_normalize_required_field(payload.approach),
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    insight = QuestionInsight(question_id=question.id, pattern=detect_pattern(question.approach))
    db.add(insight)
    db.commit()
    question.insight = insight
    return question


@app.get("/questions", response_model=List[QuestionRead])
def list_questions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> List[Question]:
    return (
        _load_question_query(db)
        .order_by(Question.created_at.desc(), Question.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.get("/questions/{question_id}", response_model=QuestionRead)
def get_question(question_id: int, db: Session = Depends(get_db)) -> Question:
    question = _load_question_query(db).filter(Question.id == question_id).one_or_none()
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return question


@app.get("/review/schedules", response_model=List[ReviewScheduleRead])
def list_review_schedules(db: Session = Depends(get_db)) -> List[ReviewSchedule]:
    return db.query(ReviewSchedule).order_by(ReviewSchedule.next_review_at.asc(), ReviewSchedule.question_id.asc()).all()


@app.get("/questions/{question_id}/review-schedule", response_model=ReviewScheduleRead)
def get_review_schedule(question_id: int, db: Session = Depends(get_db)) -> ReviewSchedule:
    schedule = db.get(ReviewSchedule, question_id)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review schedule not found")
    return schedule


@app.post("/practice/sessions", response_model=PracticeSessionRead, status_code=status.HTTP_201_CREATED)
def start_practice_session(db: Session = Depends(get_db)) -> PracticeSession:
    due_questions = (
        db.query(Question)
        .join(ReviewSchedule)
        .filter(ReviewSchedule.next_review_at <= now_utc())
        .order_by(ReviewSchedule.next_review_at.asc(), Question.id.asc())
        .all()
    )
    question: Question | None = due_questions[0] if due_questions else None

    if question is None:
        questions = _load_question_query(db).order_by(Question.created_at.asc(), Question.id.asc()).all()
        if not questions:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No questions available for practice")
        question = random.choice(questions)

    session = PracticeSession(question=question)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@app.get("/practice/sessions", response_model=List[PracticeSessionRead])
def list_practice_sessions(db: Session = Depends(get_db)) -> List[PracticeSession]:
    return _load_practice_session_query(db).order_by(PracticeSession.created_at.desc(), PracticeSession.id.desc()).all()


@app.post("/practice/sessions/{session_id}/recall", response_model=RecallEvaluationRead)
def submit_recall(session_id: int, payload: RecallAttemptCreate, db: Session = Depends(get_db)) -> dict:
    session = _load_practice_session_query(db).filter(PracticeSession.id == session_id).one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practice session not found")

    evaluation_data = evaluate_recall(session.question.approach, payload.recall_attempt)
    schedule = session.question.review_schedule
    schedule_data = build_review_schedule(
        evaluation_data["score"],
        current_interval_days=schedule.interval_days if schedule is not None else None,
        review_count=schedule.review_count if schedule is not None else 0,
    )

    evaluation = db.get(RecallEvaluation, session.id)
    if evaluation is None:
        evaluation = RecallEvaluation(
            session_id=session.id,
            question_id=session.question_id,
            recall_attempt=payload.recall_attempt.strip(),
            score=evaluation_data["score"],
            strengths_json=json.dumps(evaluation_data["strengths"]),
            missing_concepts_json=json.dumps(evaluation_data["missing_concepts"]),
            feedback=evaluation_data["feedback"],
        )
    else:
        evaluation.recall_attempt = payload.recall_attempt.strip()
        evaluation.score = evaluation_data["score"]
        evaluation.strengths_json = json.dumps(evaluation_data["strengths"])
        evaluation.missing_concepts_json = json.dumps(evaluation_data["missing_concepts"])
        evaluation.feedback = evaluation_data["feedback"]

    if schedule is None:
        schedule = ReviewSchedule(
            question_id=session.question_id,
            interval_days=schedule_data["interval_days"],
            review_count=schedule_data["review_count"],
            last_score=evaluation_data["score"],
            next_review_at=schedule_data["next_review_at"],
            updated_at=schedule_data["updated_at"],
        )
    else:
        schedule.interval_days = schedule_data["interval_days"]
        schedule.review_count = schedule_data["review_count"]
        schedule.last_score = evaluation_data["score"]
        schedule.next_review_at = schedule_data["next_review_at"]
        schedule.updated_at = schedule_data["updated_at"]

    db.add(evaluation)
    db.add(schedule)
    db.commit()
    db.refresh(evaluation)
    db.refresh(schedule)

    return {
        "session_id": evaluation.session_id,
        "question_id": evaluation.question_id,
        "recall_attempt": evaluation.recall_attempt,
        "score": evaluation.score,
        "strengths": evaluation.strengths,
        "missing_concepts": evaluation.missing_concepts,
        "feedback": evaluation.feedback,
        "next_review_at": schedule.next_review_at,
        "review_count": schedule.review_count,
        "interval_days": schedule.interval_days,
        "created_at": evaluation.created_at,
    }
