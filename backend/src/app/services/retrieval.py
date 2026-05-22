from dataclasses import dataclass
from pathlib import Path

from app.services.knowledge_loader import KNOWLEDGE_DIR, load_knowledge_documents


@dataclass(frozen=True)
class RetrievalResult:
    slug: str
    content: str
    score: int
    source_path: Path


def _tokenize(text: str) -> list[str]:
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in text)
    return [token for token in cleaned.split() if token]


def retrieve_documents(query: str, limit: int = 3) -> list[RetrievalResult]:
    query_tokens = _tokenize(query)
    results: list[RetrievalResult] = []

    for slug, content in load_knowledge_documents().items():
        haystack = _tokenize(content)
        score = sum(haystack.count(token) for token in query_tokens)
        if score > 0:
            results.append(
                RetrievalResult(
                    slug=slug,
                    content=content,
                    score=score,
                    source_path=KNOWLEDGE_DIR / f"{slug}.md",
                )
            )

    results.sort(key=lambda item: (-item.score, item.slug))
    return results[:limit]
