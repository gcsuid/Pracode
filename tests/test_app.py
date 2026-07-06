from datetime import datetime, timedelta, timezone
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AI_PROVIDER"] = "heuristic"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import ReviewSchedule


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def _create_question(payload: dict) -> dict:
    response = client.post("/questions", json=payload)
    assert response.status_code == 201
    return response.json()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "sqlite"


def test_create_list_and_get_question():
    create_payload = {
        "leetcode_id": "LC-11",
        "title": "Container With Most Water",
        "approach": "Use two pointers moving inward from both ends.",
    }
    created = client.post("/questions", json=create_payload)
    assert created.status_code == 201
    body = created.json()
    assert body["id"] > 0
    assert body["leetcode_id"] == "LC-11"
    assert body["pattern"] == "Two Pointers"

    listed = client.get("/questions")
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) >= 1
    assert any(item["id"] == body["id"] for item in items)

    fetched = client.get(f"/questions/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == create_payload["title"]


def test_get_question_not_found():
    response = client.get("/questions/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Question not found"


def test_start_and_list_practice_session(monkeypatch):
    created_questions = []
    for idx in range(5):
        payload = {
            "leetcode_id": f"LC-{100 + idx}",
            "title": f"Question {idx}",
            "approach": f"Approach {idx}",
        }
        created_questions.append(_create_question(payload))

    monkeypatch.setattr("app.main.random.choice", lambda items: items[0])

    started = client.post("/practice/sessions")
    assert started.status_code == 201
    session = started.json()
    assert session["question"]["id"] == created_questions[0]["id"]
    assert session["question"]["title"] == created_questions[0]["title"]
    assert session["prompt"].startswith("Practice prompt:")
    assert session["score"] is None

    history = client.get("/practice/sessions")
    assert history.status_code == 200
    sessions = history.json()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session["id"]
    assert sessions[0]["question"]["id"] == created_questions[0]["id"]


def test_start_practice_session_requires_questions():
    response = client.post("/practice/sessions")
    assert response.status_code == 404
    assert response.json()["detail"] == "No questions available for practice"


def test_submit_recall_updates_schedule():
    question = _create_question(
        {
            "leetcode_id": "LC-42",
            "title": "Trapping Rain Water",
            "approach": "Use two pointers and track the maximum left and right walls.",
        }
    )

    started = client.post("/practice/sessions")
    assert started.status_code == 201
    session_id = started.json()["id"]

    response = client.post(
        f"/practice/sessions/{session_id}/recall",
        json={"recall_attempt": "Track left and right maxima with two pointers."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["question_id"] == question["id"]
    assert 0 <= body["score"] <= 100
    assert body["next_review_at"] is not None
    assert body["review_count"] == 1
    assert body["interval_days"] >= 1

    schedule = client.get(f"/questions/{question['id']}/review-schedule")
    assert schedule.status_code == 200
    schedule_body = schedule.json()
    assert schedule_body["review_count"] == 1
    assert schedule_body["question_id"] == question["id"]


def test_due_questions_are_prioritized():
    first = _create_question(
        {
            "leetcode_id": "LC-200",
            "title": "Due Question",
            "approach": "Use breadth first search over a graph.",
        }
    )
    second = _create_question(
        {
            "leetcode_id": "LC-201",
            "title": "Fresh Question",
            "approach": "Use dynamic programming with memoization.",
        }
    )

    with SessionLocal() as db:
        db.add(
            ReviewSchedule(
                question_id=first["id"],
                interval_days=1,
                review_count=2,
                last_score=95,
                next_review_at=datetime.now(timezone.utc) - timedelta(days=1),
                updated_at=datetime.now(timezone.utc) - timedelta(days=1),
            )
        )
        db.commit()

    started = client.post("/practice/sessions")
    assert started.status_code == 201
    session = started.json()
    assert session["question"]["id"] == first["id"]
    assert session["question"]["title"] == first["title"]
    assert second["id"] != session["question"]["id"]


def test_rephrase_uses_transformers_provider(monkeypatch):
    from app import services

    monkeypatch.setenv("AI_PROVIDER", "transformers")
    monkeypatch.setattr(services, "_transformers_generate", lambda _: "Transformed prompt")

    result = services.rephrase_question("Two Sum", "Use a hash map.")
    assert result == "Transformed prompt"
