import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


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
