from __future__ import annotations

from collections.abc import Iterator
from typing import Any

try:
    from volcenginesdkarkruntime import Ark
except ModuleNotFoundError:
    Ark = Any

from app.core.config import settings
from app.services.persona import build_persona_prompt


class LLMDependencyError(RuntimeError):
    pass


class LLMService:
    def __init__(self) -> None:
        self._client: Ark | None = None

    def ensure_client(self) -> Ark:
        if self._client is not None:
            return self._client
        if not settings.ark_api_key or not settings.ark_endpoint_id:
            raise LLMDependencyError("Interview model configuration is missing")
        if Ark is Any:
            raise LLMDependencyError("Ark SDK is not installed")
        try:
            self._client = Ark(
                base_url=settings.ark_base_url,
                api_key=settings.ark_api_key,
                timeout=1800,
            )
        except Exception as error:
            raise LLMDependencyError("Ark client initialization failed") from error
        return self._client

    def _build_messages(self, history_messages: list[dict[str, str]], rag_context: str) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": f"{build_persona_prompt()}\n\nCandidate materials:\n{rag_context.strip()}",
            },
            *[
                {
                    "role": "user" if message["role"] == "interviewer" else "assistant",
                    "content": message["content"],
                }
                for message in history_messages
            ],
        ]

    def _extract_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                item.get("text", "") if isinstance(item, dict) else getattr(item, "text", "")
                for item in content
            )
        return ""

    def generate_reply(self, history_messages: list[dict[str, str]], rag_context: str) -> str:
        client = self.ensure_client()
        messages = self._build_messages(history_messages, rag_context)
        try:
            response = client.chat.completions.create(
                model=settings.ark_endpoint_id,
                messages=messages,
                temperature=0.3,
                stream=False,
            )
        except Exception as error:
            raise LLMDependencyError("Ark request failed") from error

        choice = response.choices[0] if getattr(response, "choices", None) else None
        message = getattr(choice, "message", None)
        content = self._extract_text(getattr(message, "content", ""))
        if not content.strip():
            raise LLMDependencyError("Ark returned empty content")
        return content.strip()

    def stream_reply(self, history_messages: list[dict[str, str]], rag_context: str) -> Iterator[str]:
        client = self.ensure_client()
        messages = self._build_messages(history_messages, rag_context)
        try:
            stream = client.chat.completions.create(
                model=settings.ark_endpoint_id,
                messages=messages,
                temperature=0.3,
                stream=True,
            )
            yielded = False
            for chunk in stream:
                choice = chunk.choices[0] if getattr(chunk, "choices", None) else None
                delta = getattr(choice, "delta", None)
                text = self._extract_text(getattr(delta, "content", ""))
                if not text:
                    continue
                yielded = True
                yield text
            if not yielded:
                raise LLMDependencyError("Ark returned empty content")
        except LLMDependencyError:
            raise
        except Exception as error:
            raise LLMDependencyError("Ark request failed") from error


llm_service = LLMService()
