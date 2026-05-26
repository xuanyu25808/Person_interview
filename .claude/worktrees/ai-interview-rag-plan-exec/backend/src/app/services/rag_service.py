from __future__ import annotations

from dataclasses import dataclass

from app.services.knowledge_loader import KNOWLEDGE_DIR
from app.services.retrieval import RetrievalResult, retrieve_documents


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
        documents = retrieve_documents(query)
        citations = [self._to_citation(document, query) for document in documents]
        context_text = "\n\n".join(document.content for document in documents)
        return RagResult(context_text=context_text, citations=citations)

    def _to_citation(self, document: RetrievalResult, query: str) -> Citation:
        snippet = self._build_snippet(document.content, query)
        title = f"{document.slug}.md"
        relative_path = (KNOWLEDGE_DIR / f"{document.slug}.md").relative_to(KNOWLEDGE_DIR.parent)
        return Citation(
            title=title,
            url=relative_path.as_posix(),
            snippet=snippet,
        )

    def _build_snippet(self, content: str, query: str) -> str:
        query_tokens = [token.lower() for token in query.split() if token]
        candidates = [line.strip().lstrip("-# ").strip() for line in content.splitlines()]
        for candidate in candidates:
            lowered = candidate.lower()
            if candidate and any(token in lowered for token in query_tokens):
                return candidate
        for candidate in candidates:
            if candidate:
                return candidate
        return content.strip()[:160]


rag_service = RagService()
