from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.interview import InterviewMessage
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service


def build_answer(messages: list[dict[str, str]]) -> InterviewMessage:
    interviewer_messages = [message for message in messages if message["role"] == "interviewer"]
    if not interviewer_messages:
        raise ValueError("At least one interviewer message is required")

    query = interviewer_messages[-1]["content"]
    rag_result = rag_service.retrieve(query)
    reply_content = llm_service.generate_reply(messages, rag_result.context_text)

    return InterviewMessage(
        id=f"msg_{uuid4().hex}",
        role="assistant",
        content=reply_content,
        sources=[citation.__dict__ for citation in rag_result.citations],
        createdAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
