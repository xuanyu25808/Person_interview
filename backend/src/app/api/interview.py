from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.interview import InterviewChatRequest, InterviewChatResponse
from app.services.answer_pipeline import InterviewDependencyError, build_answer, stream_answer

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/chat", response_model=InterviewChatResponse)
def interview_chat(request: InterviewChatRequest) -> InterviewChatResponse:
    try:
        reply = build_answer(
            messages=[
                {"role": message.role, "content": message.content}
                if hasattr(message, "role")
                else {"role": message["role"], "content": message["content"]}
                for message in request.messages
            ]
        )
    except InterviewDependencyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return InterviewChatResponse(reply=reply)


@router.post("/chat/stream")
def interview_chat_stream(request: InterviewChatRequest) -> StreamingResponse:
    try:
        event_stream = stream_answer(
            messages=[
                {"role": message.role, "content": message.content}
                if hasattr(message, "role")
                else {"role": message["role"], "content": message["content"]}
                for message in request.messages
            ]
        )
    except InterviewDependencyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return StreamingResponse(
        event_stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
