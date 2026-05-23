from __future__ import annotations

from app.core.config import settings
from app.services.persona import build_persona_prompt


class LLMService:
    def ensure_client(self) -> None:
        if settings.interview_model == "placeholder" and not settings.ark_endpoint_id:
            raise RuntimeError("Interview model configuration is missing")

    def generate_reply(self, history_messages: list[dict[str, str]], rag_context: str) -> str:
        self.ensure_client()
        latest_question = next(
            (message["content"] for message in reversed(history_messages) if message["role"] == "interviewer"),
            "",
        )
        persona_prompt = build_persona_prompt()
        if rag_context:
            return (
                f"{latest_question}\n\n"
                f"基于候选人资料，我建议从项目背景、个人职责、技术难点和结果四个维度来回答。\n\n"
                f"参考资料：{rag_context.splitlines()[0].strip()}"
            )
        return (
            f"{latest_question}\n\n"
            "当前资料里没有直接支持这次回答的检索结果，我会坚持基于已有候选人资料回答，避免编造未经支持的经历。\n\n"
            f"约束：{persona_prompt}"
        )


llm_service = LLMService()
