from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_interview_chat_returns_grounded_reply_and_topic() -> None:
    response = client.post(
        "/api/interview/chat",
        json={
            "session_id": "session-1",
            "message": "Tell me about your retrieval work and recent projects.",
            "history": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello, happy to help. [assistant] [source:notes.md]"},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["topic"] == "projects"
    assert "[assistant]" in payload["reply"]
    assert "[source:" in payload["reply"]
    assert "invent" not in payload["reply"].lower()
