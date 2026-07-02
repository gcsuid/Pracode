import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


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

    listed = client.get("/questions")
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) >= 1
    assert any(item["id"] == body["id"] for item in items)

    fetched = client.get("/questions/{question_id}".format(question_id=body["id"]))
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
        response = client.post("/questions", json=payload)
        assert response.status_code == 201
        created_questions.append(response.json())

    monkeypatch.setattr("app.main.random.choice", lambda items: items[0])

    started = client.post("/practice/sessions")
    assert started.status_code == 201
    session = started.json()
    assert session["question"]["id"] == created_questions[0]["id"]
    assert session["question"]["title"] == created_questions[0]["title"]

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
