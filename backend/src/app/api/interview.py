from fastapi import APIRouter

from app.schemas.interview import InterviewChatRequest, InterviewChatResponse
from app.services.answer_pipeline import build_answer

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/chat", response_model=InterviewChatResponse)
def interview_chat(request: InterviewChatRequest) -> InterviewChatResponse:
    reply, topic = build_answer(
        session_id=request.session_id,
        message=request.message,
        history=[turn.model_dump() for turn in request.history],
    )
    return InterviewChatResponse(reply=reply, topic=topic)
