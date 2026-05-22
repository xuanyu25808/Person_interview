from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMemory:
    role: str
    content: str


def should_write_memory(message: str) -> bool:
    lowered = message.lower()
    triggers = ("remember", "led", "built", "shipped", "experience", "worked on")
    return any(trigger in lowered for trigger in triggers)
