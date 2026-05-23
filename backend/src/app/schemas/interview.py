from typing import Literal

from pydantic import BaseModel, Field, model_validator


class MessageCitation(BaseModel):
    title: str
    url: str
    snippet: str
    kind: str


class InterviewMessage(BaseModel):
    id: str
    role: Literal["interviewer", "assistant"]
    content: str
    sources: list[MessageCitation] = Field(default_factory=list)
    createdAt: str


class InterviewChatRequest(BaseModel):
    messages: list[InterviewMessage | dict] = Field(min_length=1)
    mode: Literal["text", "voice"] = "text"

    @model_validator(mode="after")
    def validate_has_interviewer_message(self) -> "InterviewChatRequest":
        has_interviewer_message = any(
            isinstance(message, InterviewMessage) and message.role == "interviewer"
            or isinstance(message, dict) and message.get("role") == "interviewer"
            for message in self.messages
        )
        if not has_interviewer_message:
            raise ValueError("At least one interviewer message is required")
        return self


class InterviewChatResponse(BaseModel):
    reply: InterviewMessage
