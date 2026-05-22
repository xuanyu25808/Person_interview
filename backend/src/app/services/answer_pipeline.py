from app.services.memory import MemoryManager
from app.services.persona import build_persona_prompt
from app.services.retrieval import retrieve_documents

memory_manager = MemoryManager()


def build_answer(session_id: str, message: str, history: list[dict[str, str]] | None = None) -> tuple[str, str]:
    history = history or []
    for turn in history:
        memory_manager.record_turn(session_id, turn["role"], turn["content"])

    memory_manager.record_turn(session_id, "user", message)
    memory_manager.maybe_writeback(session_id, message)

    summary = memory_manager.get_summary(session_id)
    recent_turns = memory_manager.get_recent_turns(session_id, limit=4)
    retrieved = retrieve_documents(message)
    topic = retrieved[0].slug if retrieved else "general"
    sources = ", ".join(f"{item.slug}.md" for item in retrieved) or "notes.md"

    evidence = []
    if retrieved:
        evidence.append(retrieved[0].content.splitlines()[-1].strip("- "))
    if memory_manager.get_written_memories(session_id):
        evidence.append(memory_manager.get_written_memories(session_id)[-1])
    if recent_turns:
        evidence.append(recent_turns[-1].content)

    detail = evidence[0] if evidence else "I can only answer from the local candidate materials currently available."
    grounding_note = "Grounded in local candidate materials only; unsupported claims are declined."
    _ = build_persona_prompt()
    reply = (
        f"[assistant] {detail}. "
        f"Topic: {topic}. "
        f"Summary: {summary}. "
        f"{grounding_note} "
        f"[source:{sources}]"
    )

    memory_manager.record_turn(session_id, "assistant", reply)
    return reply, topic
