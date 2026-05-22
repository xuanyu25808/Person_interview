from app.services.persona import build_persona_prompt


def test_persona_prompt_requires_grounding_and_no_invention() -> None:
    prompt = build_persona_prompt()

    assert "candidate materials" in prompt.lower()
    assert "do not invent" in prompt.lower()
    assert "resume" in prompt.lower()
    assert "projects" in prompt.lower()
