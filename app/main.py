from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Question
from app.schemas import QuestionCreate, QuestionRead

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
