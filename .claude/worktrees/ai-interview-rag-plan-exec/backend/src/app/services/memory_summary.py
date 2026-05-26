from app.services.memory_writeback import ChatMemory


def summarize_session(turns: list[ChatMemory]) -> str:
    if not turns:
        return "No session summary yet."

    user_points = [turn.content.strip() for turn in turns if turn.role == "user"]
    if not user_points:
        return "No user-provided details yet."

    return "Session summary: " + " | ".join(user_points[-3:])
