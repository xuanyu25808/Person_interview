from collections import defaultdict

from app.services.memory_summary import summarize_session
from app.services.memory_writeback import ChatMemory, should_write_memory


class MemoryManager:
    def __init__(self) -> None:
        self._turns: dict[str, list[ChatMemory]] = defaultdict(list)
        self._writebacks: dict[str, list[str]] = defaultdict(list)
        self._summaries: dict[str, str] = defaultdict(lambda: "No session summary yet.")

    def record_turn(self, session_id: str, role: str, content: str) -> None:
        self._turns[session_id].append(ChatMemory(role=role, content=content))
        self._summaries[session_id] = summarize_session(self._turns[session_id])

    def get_recent_turns(self, session_id: str, limit: int = 4) -> list[ChatMemory]:
        return self._turns[session_id][-limit:]

    def get_summary(self, session_id: str) -> str:
        return self._summaries[session_id]

    def maybe_writeback(self, session_id: str, message: str) -> None:
        if should_write_memory(message):
            self._writebacks[session_id].append(message.strip())

    def get_written_memories(self, session_id: str) -> list[str]:
        return self._writebacks[session_id]
