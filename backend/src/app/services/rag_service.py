from __future__ import annotations

from dataclasses import dataclass
import re

import httpx

from app.core.config import settings


class RagError(RuntimeError):
    pass


class RagDependencyError(RagError):
    pass


class RagInsufficientEvidenceError(RagError):
    pass


@dataclass(frozen=True)
class Citation:
    title: str
    url: str
    snippet: str
    kind: str = "knowledge"


@dataclass(frozen=True)
class RagResult:
    context_text: str
    citations: list[Citation]


class RagService:
    def retrieve(self, query: str) -> RagResult:
        self.ensure_config()
        response_payload = self._search_knowledge_base(query)
        result = self._to_rag_result(response_payload)
        self.ensure_evidence(query, result)
        return result

    def ensure_config(self) -> None:
        if not settings.kb_api_key:
            raise RagDependencyError("Knowledge base configuration is missing")
        if not settings.kb_project_name or not settings.kb_collection_name or not settings.kb_domain:
            raise RagDependencyError("Knowledge base configuration is missing")

    def ensure_evidence(self, query: str, result: RagResult) -> None:
        if not result.context_text:
            raise RagInsufficientEvidenceError("Knowledge base returned no usable context")
        if not result.citations:
            raise RagInsufficientEvidenceError("Knowledge base returned no usable citations")
        if not any(citation.snippet.strip() for citation in result.citations):
            raise RagInsufficientEvidenceError("Knowledge base returned citations without snippets")
        if not self._has_query_overlap(query, result):
            raise RagInsufficientEvidenceError("Knowledge base returned no usable evidence for this question")

    def _has_query_overlap(self, query: str, result: RagResult) -> bool:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return False

        evidence_text = "\n".join(
            [result.context_text, *[citation.title for citation in result.citations], *[citation.snippet for citation in result.citations]]
        )
        evidence_tokens = self._tokenize(evidence_text)
        return bool(query_tokens & evidence_tokens)

    def _tokenize(self, text: str) -> set[str]:
        normalized = text.casefold()
        latin_and_digits = {token for token in re.findall(r"[a-z0-9]{2,}", normalized)}
        cjk_pairs = {
            normalized[index : index + 2]
            for index in range(len(normalized) - 1)
            if self._is_cjk(normalized[index]) and self._is_cjk(normalized[index + 1])
        }
        return latin_and_digits | cjk_pairs

    def _is_cjk(self, char: str) -> bool:
        codepoint = ord(char)
        return 0x4E00 <= codepoint <= 0x9FFF

    def _search_knowledge_base(self, query: str) -> dict:
        url = f"http://{settings.kb_domain}/api/knowledge/collection/search_knowledge"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Host": settings.kb_domain,
            "Authorization": f"Bearer {settings.kb_api_key}",
        }
        body = {
            "project": settings.kb_project_name,
            "name": settings.kb_collection_name,
            "query": query,
            "limit": 3,
            "pre_processing": {
                "need_instruction": True,
                "return_token_usage": True,
                "messages": [
                    {"role": "system", "content": ""},
                    {"role": "user", "content": query},
                ],
            },
            "dense_weight": 0.5,
            "post_processing": {
                "get_attachment_link": True,
                "rerank_only_chunk": False,
                "rerank_switch": False,
            },
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, headers=headers, json=body)
        except httpx.TimeoutException as error:
            raise RagDependencyError("Knowledge base request timed out") from error
        except httpx.HTTPError as error:
            raise RagDependencyError("Knowledge base request failed") from error

        if response.status_code != 200:
            raise RagDependencyError("Knowledge base request failed")

        try:
            return response.json()
        except ValueError as error:
            raise RagDependencyError("Knowledge base returned invalid JSON") from error

    def _to_rag_result(self, payload: dict) -> RagResult:
        raw_results = payload.get("data", {}).get("result_list", [])
        citations: list[Citation] = []
        context_parts: list[str] = []

        for item in raw_results:
            content = str(item.get("content") or "").strip()
            title = str(item.get("title") or item.get("doc_name") or item.get("source") or "").strip()
            url = str(item.get("attachment_link") or item.get("doc_url") or item.get("source") or "").strip()
            snippet = str(item.get("chunk") or item.get("content") or "").strip()

            if content:
                context_parts.append(content)

            if title or url or snippet:
                citations.append(
                    Citation(
                        title=title or "knowledge-base",
                        url=url or "knowledge-base",
                        snippet=snippet,
                    )
                )

        return RagResult(
            context_text="\n\n".join(context_parts).strip(),
            citations=citations,
        )


rag_service = RagService()
