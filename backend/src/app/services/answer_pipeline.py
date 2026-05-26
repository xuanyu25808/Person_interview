from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterator
from uuid import uuid4

from app.schemas.interview import InterviewMessage, InterviewStreamEvent, InterviewThinking
from app.services.llm_service import LLMDependencyError, llm_service
from app.services.rag_service import RagDependencyError, RagInsufficientEvidenceError, rag_service


class InterviewPipelineError(RuntimeError):
    pass


class InterviewDependencyError(InterviewPipelineError):
    pass


class InterviewInsufficientEvidenceError(InterviewPipelineError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _create_thinking(phase: str, summary: str) -> InterviewThinking:
    return InterviewThinking(phase=phase, summary=summary, updatedAt=_now_iso())


def _create_reply(content: str, sources: list[dict], *, state: str | None = None, thinking: InterviewThinking | None = None, reply_id: str | None = None, created_at: str | None = None) -> InterviewMessage:
    return InterviewMessage(
        id=reply_id or f"msg_{uuid4().hex}",
        role="assistant",
        content=content,
        sources=sources,
        createdAt=created_at or _now_iso(),
        state=state,
        thinking=thinking,
    )


def _event_payload(event: InterviewStreamEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"


def _chunk_text(content: str) -> list[str]:
    parts = [segment for segment in content.split("\n") if segment]
    if parts:
        return [segment + ("\n" if index < len(parts) - 1 else "") for index, segment in enumerate(parts)]
    return [content]


def build_answer(messages: list[dict[str, str]]) -> InterviewMessage:
    interviewer_messages = [message for message in messages if message["role"] == "interviewer"]
    if not interviewer_messages:
        raise ValueError("At least one interviewer message is required")

    query = interviewer_messages[-1]["content"]

    try:
        rag_result = rag_service.retrieve(query)
    except RagInsufficientEvidenceError as error:
        return _create_reply(
            content=f"我暂时没法基于现有资料给出可靠回答。\n\n原因：{error}",
            sources=[],
            state="done",
            thinking=_create_thinking("thinking", "现有资料里没有找到足够支撑这次回答的依据。"),
        )
    except RagDependencyError as error:
        raise InterviewDependencyError(str(error)) from error

    try:
        reply_content = llm_service.generate_reply(messages, rag_result.context_text)
    except LLMDependencyError as error:
        raise InterviewDependencyError(str(error)) from error

    return _create_reply(
        content=reply_content,
        sources=[citation.__dict__ for citation in rag_result.citations],
        state="done",
        thinking=_create_thinking("responding", "已基于检索到的资料生成最终回答。"),
    )


def stream_answer(messages: list[dict[str, str]]) -> Iterator[str]:
    interviewer_messages = [message for message in messages if message["role"] == "interviewer"]
    if not interviewer_messages:
        raise ValueError("At least one interviewer message is required")

    query = interviewer_messages[-1]["content"]
    reply_id = f"msg_{uuid4().hex}"
    created_at = _now_iso()

    yield _event_payload(InterviewStreamEvent(type="status", status="retrieving", replyId=reply_id, createdAt=created_at))
    yield _event_payload(
        InterviewStreamEvent(
            type="thinking",
            status="retrieving",
            replyId=reply_id,
            createdAt=created_at,
            thinking=_create_thinking("retrieving", "正在检索候选人资料与相关项目证据。"),
        )
    )

    try:
        rag_result = rag_service.retrieve(query)
    except RagInsufficientEvidenceError as error:
        yield _event_payload(InterviewStreamEvent(type="status", status="thinking", replyId=reply_id, createdAt=created_at))
        yield _event_payload(
            InterviewStreamEvent(
                type="thinking",
                status="thinking",
                replyId=reply_id,
                createdAt=created_at,
                thinking=_create_thinking("thinking", "现有资料里没有找到足够支撑这次回答的依据。"),
            )
        )
        refusal = f"我暂时没法基于现有资料给出可靠回答。\n\n原因：{error}"
        yield _event_payload(InterviewStreamEvent(type="status", status="responding", replyId=reply_id, createdAt=created_at))
        for chunk in _chunk_text(refusal):
            yield _event_payload(InterviewStreamEvent(type="delta", status="responding", replyId=reply_id, createdAt=created_at, delta=chunk))
        yield _event_payload(InterviewStreamEvent(type="sources", replyId=reply_id, createdAt=created_at, sources=[]))
        yield _event_payload(InterviewStreamEvent(type="done", status="done", replyId=reply_id, createdAt=created_at))
        return
    except RagDependencyError as error:
        yield _event_payload(
            InterviewStreamEvent(
                type="error",
                status="error",
                replyId=reply_id,
                createdAt=created_at,
                error=str(error),
            )
        )
        yield _event_payload(InterviewStreamEvent(type="done", status="done", replyId=reply_id, createdAt=created_at))
        return

    yield _event_payload(InterviewStreamEvent(type="status", status="thinking", replyId=reply_id, createdAt=created_at))
    yield _event_payload(
        InterviewStreamEvent(
            type="thinking",
            status="thinking",
            replyId=reply_id,
            createdAt=created_at,
            thinking=_create_thinking("thinking", "正在归纳与你问题最相关的证据，并组织回答重点。"),
        )
    )

    try:
        reply_content = llm_service.generate_reply(messages, rag_result.context_text)
    except LLMDependencyError as error:
        yield _event_payload(
            InterviewStreamEvent(
                type="error",
                status="error",
                replyId=reply_id,
                createdAt=created_at,
                error=str(error),
            )
        )
        yield _event_payload(InterviewStreamEvent(type="done", status="done", replyId=reply_id, createdAt=created_at))
        return

    yield _event_payload(InterviewStreamEvent(type="status", status="responding", replyId=reply_id, createdAt=created_at))
    yield _event_payload(
        InterviewStreamEvent(
            type="thinking",
            status="responding",
            replyId=reply_id,
            createdAt=created_at,
            thinking=_create_thinking("responding", "正在把整理后的证据转成最终回答。"),
        )
    )
    for chunk in _chunk_text(reply_content):
        yield _event_payload(InterviewStreamEvent(type="delta", status="responding", replyId=reply_id, createdAt=created_at, delta=chunk))
    yield _event_payload(
        InterviewStreamEvent(
            type="sources",
            replyId=reply_id,
            createdAt=created_at,
            sources=[citation.__dict__ for citation in rag_result.citations],
        )
    )
    yield _event_payload(InterviewStreamEvent(type="done", status="done", replyId=reply_id, createdAt=created_at))
