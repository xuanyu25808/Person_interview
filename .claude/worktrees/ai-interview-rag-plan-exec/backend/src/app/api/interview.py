from fastapi import APIRouter

from app.schemas.interview import InterviewChatRequest, InterviewChatResponse
from app.services.answer_pipeline import build_answer

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/chat", response_model=InterviewChatResponse)
def interview_chat(request: InterviewChatRequest) -> InterviewChatResponse:
    reply = build_answer(
        messages=[
            {"role": message.role, "content": message.content}
            if hasattr(message, "role")
            else {"role": message["role"], "content": message["content"]}
            for message in request.messages
        ]
    )
    return InterviewChatResponse(reply=reply)
