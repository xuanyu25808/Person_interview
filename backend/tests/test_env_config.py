from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_allowed_origins_env_uses_json_array() -> None:
    content = (ROOT / ".env").read_text(encoding="utf-8")

    assert 'ALLOWED_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]' in content
