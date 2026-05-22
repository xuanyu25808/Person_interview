from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: str
    content: str


class InterviewChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    history: list[ChatTurn] = Field(default_factory=list)


class InterviewChatResponse(BaseModel):
    reply: str
    topic: str
