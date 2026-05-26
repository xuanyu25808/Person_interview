from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_uv_workflow() -> None:
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "[tool.uv]" in content
    assert "[tool.uv.sources]" in content
    assert 'package = false' in content
