import random
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import PracticeSession, Question
from app.schemas import PracticeSessionRead, QuestionCreate, QuestionRead

app = FastAPI(title="DSA Memory Trainer API")
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "database": "sqlite"}


@app.post("/questions", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)) -> Question:
    question = Question(
        leetcode_id=payload.leetcode_id.strip(),
        title=payload.title.strip(),
        approach=payload.approach.strip(),
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@app.get("/questions", response_model=List[QuestionRead])
def list_questions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> List[Question]:
    return db.query(Question).order_by(Question.created_at.desc(), Question.id.desc()).offset(offset).limit(limit).all()


@app.get("/questions/{question_id}", response_model=QuestionRead)
def get_question(question_id: int, db: Session = Depends(get_db)) -> Question:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return question


@app.post("/practice/sessions", response_model=PracticeSessionRead, status_code=status.HTTP_201_CREATED)
def start_practice_session(db: Session = Depends(get_db)) -> dict:
    questions = db.query(Question).order_by(Question.created_at.asc(), Question.id.asc()).all()
    if not questions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No questions available for practice")

    question = random.choice(questions)
    session = PracticeSession(question_id=question.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"id": session.id, "question": question, "created_at": session.created_at}


@app.get("/practice/sessions", response_model=List[PracticeSessionRead])
def list_practice_sessions(db: Session = Depends(get_db)) -> List[dict]:
    sessions = db.query(PracticeSession).order_by(PracticeSession.created_at.desc(), PracticeSession.id.desc()).all()
    return [{"id": session.id, "question": session.question, "created_at": session.created_at} for session in sessions]
