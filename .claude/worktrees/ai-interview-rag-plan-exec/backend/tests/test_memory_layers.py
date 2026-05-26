from app.services.memory import MemoryManager
from app.services.memory_summary import summarize_session
from app.services.memory_writeback import should_write_memory


def test_memory_layers_track_recent_summary_and_writeback() -> None:
    manager = MemoryManager()
    session_id = "session-42"

    manager.record_turn(session_id, "user", "I built retrieval and ranking demos.")
    manager.record_turn(session_id, "assistant", "Thanks, tell me more. [assistant] [source:projects.md]")
    manager.record_turn(session_id, "user", "Please remember that I led an interview copilot prototype.")

    recent_turns = manager.get_recent_turns(session_id, limit=2)
    summary = summarize_session(manager.get_recent_turns(session_id, limit=5))

    assert len(recent_turns) == 2
    assert "interview copilot prototype" in summary.lower()
    assert should_write_memory("Please remember that I led an interview copilot prototype.") is True

    manager.maybe_writeback(session_id, "Please remember that I led an interview copilot prototype.")
    memories = manager.get_written_memories(session_id)
    assert memories
    assert "interview copilot prototype" in memories[0].lower()
