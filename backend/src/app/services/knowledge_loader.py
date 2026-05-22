from pathlib import Path


KNOWLEDGE_DIR = Path(__file__).resolve().parents[4] / "knowledge"


def load_knowledge_documents() -> dict[str, str]:
    documents: dict[str, str] = {}
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        documents[path.stem] = path.read_text(encoding="utf-8")
    return documents
