from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_interview_chat_returns_structured_reply_with_sources() -> None:
    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "interviewer", "content": "请介绍一下你做过的 retrieval 项目。"},
                {"role": "assistant", "content": "好的。"},
                {"role": "interviewer", "content": "重点说下 source attribution。"},
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    reply = payload["reply"]

    assert reply["id"]
    assert reply["role"] == "assistant"
    assert isinstance(reply["content"], str)
    assert reply["content"]
    assert isinstance(reply["sources"], list)
    assert reply["sources"]
    assert reply["createdAt"]

    first_source = reply["sources"][0]
    assert first_source["title"] == "projects.md"
    assert first_source["url"] == "knowledge/projects.md"
    assert "retrieval" in first_source["snippet"].lower() or "source" in first_source["snippet"].lower()
    assert first_source["kind"] == "knowledge"


def test_interview_chat_rejects_requests_without_interviewer_message() -> None:
    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "assistant", "content": "hello"},
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 422
