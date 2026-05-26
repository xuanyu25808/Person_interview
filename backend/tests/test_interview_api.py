from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.services.answer_pipeline import InterviewDependencyError
from app.services.llm_service import LLMDependencyError
from app.services.rag_service import RagDependencyError

client = TestClient(app)


@pytest.fixture(autouse=True)
def patch_runtime_dependencies(monkeypatch) -> None:
    monkeypatch.setattr("app.services.rag_service.rag_service.ensure_config", lambda: None)


def test_interview_chat_returns_structured_reply_with_sources(monkeypatch) -> None:
    def fake_search_knowledge_base(query: str):
        assert query == "重点说下 source attribution。"
        return {
            "data": {
                "result_list": [
                    {
                        "content": "Candidate worked on retrieval and grounded source attribution.",
                        "title": "projects.md",
                        "attachment_link": "knowledge/projects.md",
                        "chunk": "Retrieval project with source attribution.",
                    }
                ]
            }
        }

    def fake_generate_reply(messages, rag_context: str) -> str:
        assert rag_context == "Candidate worked on retrieval and grounded source attribution."
        return "我做过 retrieval 项目，重点会用 source attribution 把回答绑定到资料片段上。"

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)
    monkeypatch.setattr("app.services.answer_pipeline.llm_service.generate_reply", fake_generate_reply)

    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "interviewer", "content": "请介绍一下你做过的 retrieval 项目。"},
                {"role": "assistant", "content": "好的。"},
                {"role": "interviewer", "content": "重点说下 source attribution。"},
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    reply = payload["reply"]

    assert reply["id"]
    assert reply["role"] == "assistant"
    assert isinstance(reply["content"], str)
    assert reply["content"]
    assert isinstance(reply["sources"], list)
    assert reply["sources"]
    assert reply["createdAt"]
    assert reply["state"] == "done"
    assert reply["thinking"]["phase"] == "responding"

    first_source = reply["sources"][0]
    assert first_source["title"] == "projects.md"
    assert first_source["url"] == "knowledge/projects.md"
    assert "retrieval" in first_source["snippet"].lower() or "source" in first_source["snippet"].lower()
    assert first_source["kind"] == "knowledge"


def test_interview_chat_rejects_requests_without_interviewer_message() -> None:
    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "assistant", "content": "hello"},
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 422


def test_interview_chat_returns_422_when_rag_has_no_evidence(monkeypatch) -> None:
    def fake_search_knowledge_base(query: str):
        assert query == "completely unmatched phrase xyz"
        return {"data": {"result_list": []}}

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)

    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "interviewer", "content": "completely unmatched phrase xyz"},
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"]["role"] == "assistant"
    assert payload["reply"]["sources"] == []
    assert "我暂时没法基于现有资料给出可靠回答" in payload["reply"]["content"]
    assert "Knowledge base returned no usable context" in payload["reply"]["content"]
    assert payload["reply"]["state"] == "done"


def test_interview_chat_returns_422_when_rag_result_has_no_query_overlap(monkeypatch) -> None:
    def fake_search_knowledge_base(query: str):
        assert query == "77"
        return {
            "data": {
                "result_list": [
                    {
                        "content": "CrossFire weapon guide for M4A1 and AK47.",
                        "title": "cf-guide.md",
                        "attachment_link": "knowledge/cf-guide.md",
                        "chunk": "Weapon guide and gameplay tips.",
                    }
                ]
            }
        }

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)

    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "interviewer", "content": "77"},
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"]["role"] == "assistant"
    assert payload["reply"]["sources"] == []
    assert "我暂时没法基于现有资料给出可靠回答" in payload["reply"]["content"]
    assert "Knowledge base returned no usable evidence for this question" in payload["reply"]["content"]


def test_interview_chat_stream_emits_status_delta_sources_and_done(monkeypatch) -> None:
    def fake_search_knowledge_base(query: str):
        assert query == "retrieval"
        return {
            "data": {
                "result_list": [
                    {
                        "content": "Candidate worked on retrieval and source attribution.",
                        "title": "projects.md",
                        "attachment_link": "knowledge/projects.md",
                        "chunk": "retrieval and source attribution details",
                    }
                ]
            }
        }

    def fake_generate_reply(messages, rag_context: str) -> str:
        assert rag_context == "Candidate worked on retrieval and source attribution."
        return "第一段回答\n第二段回答"

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)
    monkeypatch.setattr("app.services.answer_pipeline.llm_service.generate_reply", fake_generate_reply)

    with client.stream(
        "POST",
        "/api/interview/chat/stream",
        json={
            "messages": [
                {"role": "interviewer", "content": "retrieval"},
            ],
            "mode": "text",
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())

    assert '"type":"status","status":"retrieving"' in body
    assert '"type":"thinking","status":"retrieving"' in body
    assert '"type":"status","status":"thinking"' in body
    assert '"type":"status","status":"responding"' in body
    assert '"type":"delta"' in body
    assert '第一段回答' in body
    assert '第二段回答' in body
    assert '"type":"sources"' in body
    assert '"type":"done","status":"done"' in body


def test_interview_chat_stream_returns_refusal_as_normal_stream(monkeypatch) -> None:
    def fake_search_knowledge_base(query: str):
        assert query == "unknown"
        return {"data": {"result_list": []}}

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)

    with client.stream(
        "POST",
        "/api/interview/chat/stream",
        json={
            "messages": [
                {"role": "interviewer", "content": "unknown"},
            ],
            "mode": "text",
        },
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert '"type":"thinking","status":"thinking"' in body
    assert '我暂时没法基于现有资料给出可靠回答' in body
    assert 'Knowledge base returned no usable context' in body
    assert '"type":"sources"' in body
    assert '"sources":[]' in body
    assert '"type":"done","status":"done"' in body


def test_interview_chat_stream_emits_error_event_when_llm_dependency_fails_after_rag_succeeds(monkeypatch) -> None:
    def fake_search_knowledge_base(query: str):
        assert query == "雷神"
        return {
            "data": {
                "result_list": [
                    {
                        "content": "M4A1-雷神是穿越火线中的英雄级武器，拥有特殊外观与强化属性。",
                        "title": "weapon-guide.md",
                        "attachment_link": "knowledge/weapon-guide.md",
                        "chunk": "M4A1-雷神是热门英雄级步枪。",
                    }
                ]
            }
        }

    def fake_generate_reply(messages, rag_context: str) -> str:
        raise LLMDependencyError("Ark SDK is not installed")

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)
    monkeypatch.setattr("app.services.answer_pipeline.llm_service.generate_reply", fake_generate_reply)

    with client.stream(
        "POST",
        "/api/interview/chat/stream",
        json={
            "messages": [
                {"role": "interviewer", "content": "雷神"},
            ],
            "mode": "text",
        },
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert '"type":"status","status":"retrieving"' in body
    assert '"type":"status","status":"thinking"' in body
    assert '"type":"error","status":"error"' in body
    assert 'Ark SDK is not installed' in body
    assert '"type":"done","status":"done"' in body


def test_interview_chat_stream_emits_error_event_when_rag_dependency_fails(monkeypatch) -> None:
    def fake_retrieve(query: str):
        assert query == "retrieval"
        raise RagDependencyError("Knowledge base configuration is missing")

    monkeypatch.setattr("app.services.answer_pipeline.rag_service.retrieve", fake_retrieve)

    with client.stream(
        "POST",
        "/api/interview/chat/stream",
        json={
            "messages": [
                {"role": "interviewer", "content": "retrieval"},
            ],
            "mode": "text",
        },
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert '"type":"status","status":"retrieving"' in body
    assert '"type":"error","status":"error"' in body
    assert 'Knowledge base configuration is missing' in body
    assert '"type":"done","status":"done"' in body


def test_interview_chat_calls_real_kb_and_ark_services(monkeypatch) -> None:
    called = {"kb": False, "ark": False}

    def fake_search_knowledge_base(query: str):
        called["kb"] = True
        assert query == "请介绍你的 retrieval 项目。"
        return {
            "data": {
                "result_list": [
                    {
                        "content": "候选人做过 retrieval 项目，负责 RAG 与 citation attribution。",
                        "title": "kb-doc",
                        "attachment_link": "https://kb.example/doc",
                        "chunk": "retrieval 项目中的 RAG 与 citation attribution 经验。",
                    }
                ]
            }
        }

    def fake_generate_reply(messages, rag_context: str) -> str:
        called["ark"] = True
        assert rag_context == "候选人做过 retrieval 项目，负责 RAG 与 citation attribution。"
        return "这是 Ark 基于知识库依据生成的回答"

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)
    monkeypatch.setattr("app.services.answer_pipeline.llm_service.generate_reply", fake_generate_reply)

    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "interviewer", "content": "请介绍你的 retrieval 项目。"},
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"]["content"] == "这是 Ark 基于知识库依据生成的回答"
    assert payload["reply"]["sources"][0]["title"] == "kb-doc"
    assert payload["reply"]["sources"][0]["url"] == "https://kb.example/doc"
    assert called == {"kb": True, "ark": True}


def test_interview_chat_maps_interviewer_role_to_ark_user(monkeypatch) -> None:
    observed = {}

    class FakeArkClient:
        class _Chat:
            class _Completions:
                def create(self, *, model, messages, temperature, stream):
                    observed['model'] = model
                    observed['messages'] = messages
                    observed['temperature'] = temperature
                    observed['stream'] = stream
                    return type(
                        'FakeResponse',
                        (),
                        {
                            'choices': [
                                type(
                                    'FakeChoice',
                                    (),
                                    {
                                        'message': type('FakeMessage', (), {'content': 'Ark reply'})(),
                                    },
                                )()
                            ]
                        },
                    )()

            completions = _Completions()

        chat = _Chat()

    def fake_search_knowledge_base(query: str):
        assert query == 'retrieval'
        return {
            'data': {
                'result_list': [
                    {
                        'content': 'retrieval experience summary',
                        'title': 'retrieval.md',
                        'attachment_link': 'knowledge/retrieval.md',
                        'chunk': 'retrieval project details',
                    }
                ]
            }
        }

    monkeypatch.setattr('app.services.rag_service.rag_service._search_knowledge_base', fake_search_knowledge_base)
    monkeypatch.setattr('app.services.llm_service.llm_service.ensure_client', lambda: FakeArkClient())

    response = client.post(
        '/api/interview/chat',
        json={
            'messages': [
                {'role': 'interviewer', 'content': 'retrieval'},
            ],
            'mode': 'text',
        },
    )

    assert response.status_code == 200
    assert observed['messages'][0]['role'] == 'system'
    assert observed['messages'][1]['role'] == 'user'


def test_interview_chat_returns_structured_reply_with_sources(monkeypatch) -> None:
    def fake_search_knowledge_base(query: str):
        assert query == "重点说下 source attribution。"
        return {
            "data": {
                "result_list": [
                    {
                        "content": "Candidate worked on retrieval and grounded source attribution.",
                        "title": "projects.md",
                        "attachment_link": "knowledge/projects.md",
                        "chunk": "Retrieval project with source attribution.",
                    }
                ]
            }
        }

    def fake_generate_reply(messages, rag_context: str) -> str:
        assert rag_context == "Candidate worked on retrieval and grounded source attribution."
        return "我做过 retrieval 项目，重点会用 source attribution 把回答绑定到资料片段上。"

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)
    monkeypatch.setattr("app.services.answer_pipeline.llm_service.generate_reply", fake_generate_reply)

    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "interviewer", "content": "请介绍一下你做过的 retrieval 项目。"},
                {"role": "assistant", "content": "好的。"},
                {"role": "interviewer", "content": "重点说下 source attribution。"},
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    reply = payload["reply"]

    assert reply["id"]
    assert reply["role"] == "assistant"
    assert isinstance(reply["content"], str)
    assert reply["content"]
    assert isinstance(reply["sources"], list)
    assert reply["sources"]
    assert reply["createdAt"]
    assert reply["state"] == "done"
    assert reply["thinking"]["phase"] == "responding"

    first_source = reply["sources"][0]
    assert first_source["title"] == "projects.md"
    assert first_source["url"] == "knowledge/projects.md"
    assert "retrieval" in first_source["snippet"].lower() or "source" in first_source["snippet"].lower()
    assert first_source["kind"] == "knowledge"


def test_interview_chat_rejects_requests_without_interviewer_message() -> None:
    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "assistant", "content": "hello"},
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 422


def test_interview_chat_returns_422_when_rag_has_no_evidence(monkeypatch) -> None:
    def fake_search_knowledge_base(query: str):
        assert query == "completely unmatched phrase xyz"
        return {"data": {"result_list": []}}

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)

    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "interviewer", "content": "completely unmatched phrase xyz"},
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"]["role"] == "assistant"
    assert payload["reply"]["sources"] == []
    assert "我暂时没法基于现有资料给出可靠回答" in payload["reply"]["content"]
    assert "Knowledge base returned no usable context" in payload["reply"]["content"]
    assert payload["reply"]["state"] == "done"


def test_interview_chat_returns_422_when_rag_result_has_no_query_overlap(monkeypatch) -> None:
    def fake_search_knowledge_base(query: str):
        assert query == "77"
        return {
            "data": {
                "result_list": [
                    {
                        "content": "CrossFire weapon guide for M4A1 and AK47.",
                        "title": "cf-guide.md",
                        "attachment_link": "knowledge/cf-guide.md",
                        "chunk": "Weapon guide and gameplay tips.",
                    }
                ]
            }
        }

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)

    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "interviewer", "content": "77"},
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"]["role"] == "assistant"
    assert payload["reply"]["sources"] == []
    assert "我暂时没法基于现有资料给出可靠回答" in payload["reply"]["content"]
    assert "Knowledge base returned no usable evidence for this question" in payload["reply"]["content"]


def test_interview_chat_stream_emits_status_delta_sources_and_done(monkeypatch) -> None:
    def fake_search_knowledge_base(query: str):
        assert query == "retrieval"
        return {
            "data": {
                "result_list": [
                    {
                        "content": "Candidate worked on retrieval and source attribution.",
                        "title": "projects.md",
                        "attachment_link": "knowledge/projects.md",
                        "chunk": "retrieval and source attribution details",
                    }
                ]
            }
        }

    def fake_generate_reply(messages, rag_context: str) -> str:
        assert rag_context == "Candidate worked on retrieval and source attribution."
        return "第一段回答\n第二段回答"

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)
    monkeypatch.setattr("app.services.answer_pipeline.llm_service.generate_reply", fake_generate_reply)

    with client.stream(
        "POST",
        "/api/interview/chat/stream",
        json={
            "messages": [
                {"role": "interviewer", "content": "retrieval"},
            ],
            "mode": "text",
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())

    assert '"type":"status","status":"retrieving"' in body
    assert '"type":"thinking","status":"retrieving"' in body
    assert '"type":"status","status":"thinking"' in body
    assert '"type":"status","status":"responding"' in body
    assert '"type":"delta"' in body
    assert '第一段回答' in body
    assert '第二段回答' in body
    assert '"type":"sources"' in body
    assert '"type":"done","status":"done"' in body


def test_interview_chat_stream_returns_refusal_as_normal_stream(monkeypatch) -> None:
    def fake_search_knowledge_base(query: str):
        assert query == "unknown"
        return {"data": {"result_list": []}}

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)

    with client.stream(
        "POST",
        "/api/interview/chat/stream",
        json={
            "messages": [
                {"role": "interviewer", "content": "unknown"},
            ],
            "mode": "text",
        },
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert '"type":"thinking","status":"thinking"' in body
    assert '我暂时没法基于现有资料给出可靠回答' in body
    assert 'Knowledge base returned no usable context' in body
    assert '"type":"sources"' in body
    assert '"sources":[]' in body
    assert '"type":"done","status":"done"' in body


def test_interview_chat_stream_emits_error_event_when_rag_dependency_fails(monkeypatch) -> None:
    def fake_retrieve(query: str):
        assert query == "retrieval"
        raise RagDependencyError("Knowledge base configuration is missing")

    monkeypatch.setattr("app.services.answer_pipeline.rag_service.retrieve", fake_retrieve)

    with client.stream(
        "POST",
        "/api/interview/chat/stream",
        json={
            "messages": [
                {"role": "interviewer", "content": "retrieval"},
            ],
            "mode": "text",
        },
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert '"type":"status","status":"retrieving"' in body
    assert '"type":"error","status":"error"' in body
    assert 'Knowledge base configuration is missing' in body
    assert '"type":"done","status":"done"' in body


def test_interview_chat_calls_real_kb_and_ark_services(monkeypatch) -> None:
    called = {"kb": False, "ark": False}

    def fake_search_knowledge_base(query: str):
        called["kb"] = True
        assert query == "请介绍你的 retrieval 项目。"
        return {
            "data": {
                "result_list": [
                    {
                        "content": "候选人做过 retrieval 项目，负责 RAG 与 citation attribution。",
                        "title": "kb-doc",
                        "attachment_link": "https://kb.example/doc",
                        "chunk": "retrieval 项目中的 RAG 与 citation attribution 经验。",
                    }
                ]
            }
        }

    def fake_generate_reply(messages, rag_context: str) -> str:
        called["ark"] = True
        assert rag_context == "候选人做过 retrieval 项目，负责 RAG 与 citation attribution。"
        return "这是 Ark 基于知识库依据生成的回答"

    monkeypatch.setattr("app.services.rag_service.rag_service._search_knowledge_base", fake_search_knowledge_base)
    monkeypatch.setattr("app.services.answer_pipeline.llm_service.generate_reply", fake_generate_reply)

    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "interviewer", "content": "请介绍你的 retrieval 项目。"},
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"]["content"] == "这是 Ark 基于知识库依据生成的回答"
    assert payload["reply"]["sources"][0]["title"] == "kb-doc"
    assert payload["reply"]["sources"][0]["url"] == "https://kb.example/doc"
    assert called == {"kb": True, "ark": True}


def test_interview_chat_maps_interviewer_role_to_ark_user(monkeypatch) -> None:
    observed = {}

    class FakeArkClient:
        class _Chat:
            class _Completions:
                def create(self, *, model, messages, temperature, stream):
                    observed['model'] = model
                    observed['messages'] = messages
                    observed['temperature'] = temperature
                    observed['stream'] = stream
                    return type(
                        'FakeResponse',
                        (),
                        {
                            'choices': [
                                type(
                                    'FakeChoice',
                                    (),
                                    {
                                        'message': type('FakeMessage', (), {'content': 'Ark reply'})(),
                                    },
                                )()
                            ]
                        },
                    )()

            completions = _Completions()

        chat = _Chat()

    def fake_search_knowledge_base(query: str):
        assert query == 'retrieval'
        return {
            'data': {
                'result_list': [
                    {
                        'content': 'retrieval experience summary',
                        'title': 'retrieval.md',
                        'attachment_link': 'knowledge/retrieval.md',
                        'chunk': 'retrieval project details',
                    }
                ]
            }
        }

    monkeypatch.setattr('app.services.rag_service.rag_service._search_knowledge_base', fake_search_knowledge_base)
    monkeypatch.setattr('app.services.llm_service.llm_service.ensure_client', lambda: FakeArkClient())

    response = client.post(
        '/api/interview/chat',
        json={
            'messages': [
                {'role': 'interviewer', 'content': 'retrieval'},
            ],
            'mode': 'text',
        },
    )

    assert response.status_code == 200
    assert observed['messages'][0]['role'] == 'system'
    assert observed['messages'][1]['role'] == 'user'
