# True Token Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `/api/interview/chat/stream` to real Ark token streaming while keeping the existing SSE event contract consumed by the frontend.

**Architecture:** Keep the current API route, SSE event types, and frontend `delta` append logic unchanged. Add a streaming generator to the Ark-backed LLM service, then update the answer pipeline to relay model chunks immediately as `delta` events instead of waiting for a full reply string.

**Tech Stack:** FastAPI, Uvicorn, Ark SDK (`volcenginesdkarkruntime`), pytest, Vue/Pinia frontend consuming SSE

---

## File Map

- Modify: `backend/src/app/services/llm_service.py`
  - Add a streaming interface that yields incremental text chunks from Ark with `stream=True`.
  - Keep the existing non-streaming `generate_reply()` behavior for `/api/interview/chat`.
- Modify: `backend/src/app/services/answer_pipeline.py`
  - Replace buffered full-response generation inside `stream_answer()` with chunk-by-chunk forwarding from `llm_service.stream_reply()`.
  - Preserve event ordering and current event schema.
- Modify: `backend/tests/test_interview_api.py`
  - Add tests for stream chunk forwarding, stream error handling, and preserve existing non-streaming behavior.
- Verify only: `frontend/src/store/interview/index.ts`
  - No code change planned; confirm existing `delta` append logic remains compatible.

---

### Task 1: Add Ark streaming support in the LLM service

**Files:**
- Modify: `backend/src/app/services/llm_service.py`
- Test: `backend/tests/test_interview_api.py`

- [ ] **Step 1: Write the failing streaming LLM test**

Add this test near the existing Ark service tests in `backend/tests/test_interview_api.py`:

```python
def test_interview_chat_stream_maps_interviewer_role_to_ark_user_and_enables_stream(monkeypatch) -> None:
    observed = {}

    class FakeStreamChunk:
        def __init__(self, text: str):
            self.choices = [
                type(
                    'FakeChoiceDelta',
                    (),
                    {
                        'delta': type('FakeDelta', (), {'content': text})(),
                    },
                )()
            ]

    class FakeArkClient:
        class _Chat:
            class _Completions:
                def create(self, *, model, messages, temperature, stream):
                    observed['model'] = model
                    observed['messages'] = messages
                    observed['temperature'] = temperature
                    observed['stream'] = stream
                    return iter([
                        FakeStreamChunk('第一段'),
                        FakeStreamChunk('第二段'),
                    ])

            completions = _Completions()

        chat = _Chat()

    monkeypatch.setattr('app.services.llm_service.Ark', object())
    monkeypatch.setattr('app.services.llm_service.settings.ark_api_key', 'test-key')
    monkeypatch.setattr('app.services.llm_service.settings.ark_endpoint_id', 'ep-test')

    from app.services.llm_service import LLMService

    service = LLMService()
    service._client = FakeArkClient()

    chunks = list(
        service.stream_reply(
            [{'role': 'interviewer', 'content': '请介绍项目'}],
            '候选人做过检索项目。',
        )
    )

    assert chunks == ['第一段', '第二段']
    assert observed['model'] == 'ep-test'
    assert observed['temperature'] == 0.3
    assert observed['stream'] is True
    assert observed['messages'][0]['role'] == 'system'
    assert observed['messages'][1]['role'] == 'user'
    assert observed['messages'][1]['content'] == '请介绍项目'
```

- [ ] **Step 2: Run the new test to verify it fails**

Run:

```bash
uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_chat_stream_maps_interviewer_role_to_ark_user_and_enables_stream -v
```

Expected: FAIL with `AttributeError` because `LLMService` has no `stream_reply` method yet.

- [ ] **Step 3: Implement minimal streaming support in `llm_service.py`**

Update `backend/src/app/services/llm_service.py` to this shape:

```python
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

try:
    from volcenginesdkarkruntime import Ark
except ModuleNotFoundError:
    Ark = Any

from app.core.config import settings
from app.services.persona import build_persona_prompt


class LLMDependencyError(RuntimeError):
    pass


class LLMService:
    def __init__(self) -> None:
        self._client: Ark | None = None

    def ensure_client(self) -> Ark:
        if self._client is not None:
            return self._client
        if not settings.ark_api_key or not settings.ark_endpoint_id:
            raise LLMDependencyError("Interview model configuration is missing")
        if Ark is Any:
            raise LLMDependencyError("Ark SDK is not installed")
        try:
            self._client = Ark(
                base_url=settings.ark_base_url,
                api_key=settings.ark_api_key,
                timeout=1800,
            )
        except Exception as error:
            raise LLMDependencyError("Ark client initialization failed") from error
        return self._client

    def _build_messages(self, history_messages: list[dict[str, str]], rag_context: str) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": f"{build_persona_prompt()}\n\nCandidate materials:\n{rag_context.strip()}",
            },
            *[
                {
                    "role": "user" if message["role"] == "interviewer" else "assistant",
                    "content": message["content"],
                }
                for message in history_messages
            ],
        ]

    def _extract_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                item.get("text", "") if isinstance(item, dict) else getattr(item, "text", "")
                for item in content
            )
        return ""

    def generate_reply(self, history_messages: list[dict[str, str]], rag_context: str) -> str:
        client = self.ensure_client()
        messages = self._build_messages(history_messages, rag_context)
        try:
            response = client.chat.completions.create(
                model=settings.ark_endpoint_id,
                messages=messages,
                temperature=0.3,
                stream=False,
            )
        except Exception as error:
            raise LLMDependencyError("Ark request failed") from error

        choice = response.choices[0] if getattr(response, "choices", None) else None
        message = getattr(choice, "message", None)
        content = self._extract_text(getattr(message, "content", ""))
        if not content.strip():
            raise LLMDependencyError("Ark returned empty content")
        return content.strip()

    def stream_reply(self, history_messages: list[dict[str, str]], rag_context: str) -> Iterator[str]:
        client = self.ensure_client()
        messages = self._build_messages(history_messages, rag_context)
        try:
            stream = client.chat.completions.create(
                model=settings.ark_endpoint_id,
                messages=messages,
                temperature=0.3,
                stream=True,
            )
            yielded = False
            for chunk in stream:
                choice = chunk.choices[0] if getattr(chunk, 'choices', None) else None
                delta = getattr(choice, 'delta', None)
                text = self._extract_text(getattr(delta, 'content', ''))
                if not text:
                    continue
                yielded = True
                yield text
            if not yielded:
                raise LLMDependencyError("Ark returned empty content")
        except LLMDependencyError:
            raise
        except Exception as error:
            raise LLMDependencyError("Ark request failed") from error


llm_service = LLMService()
```

- [ ] **Step 4: Run the targeted test to verify it passes**

Run:

```bash
uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_chat_stream_maps_interviewer_role_to_ark_user_and_enables_stream -v
```

Expected: PASS

- [ ] **Step 5: Commit the LLM streaming support**

```bash
git add backend/src/app/services/llm_service.py backend/tests/test_interview_api.py
git commit -m "feat: add Ark streaming reply support"
```

---

### Task 2: Forward Ark chunks directly through the SSE pipeline

**Files:**
- Modify: `backend/src/app/services/answer_pipeline.py`
- Test: `backend/tests/test_interview_api.py`

- [ ] **Step 1: Write the failing SSE forwarding test**

Add this test in `backend/tests/test_interview_api.py` near the existing streaming API tests:

```python
def test_interview_chat_stream_forwards_llm_chunks_as_multiple_delta_events(monkeypatch) -> None:
    def fake_retrieve(query: str):
        assert query == 'retrieval'
        return type(
            'FakeRagResult',
            (),
            {
                'context_text': 'Candidate worked on retrieval and source attribution.',
                'citations': [
                    type(
                        'FakeCitation',
                        (),
                        {
                            'title': 'projects.md',
                            'url': 'knowledge/projects.md',
                            'snippet': 'retrieval and source attribution details',
                            'kind': 'knowledge',
                        },
                    )()
                ],
            },
        )()

    def fake_stream_reply(messages, rag_context: str):
        assert rag_context == 'Candidate worked on retrieval and source attribution.'
        yield '第一段'
        yield '第二段'

    monkeypatch.setattr('app.services.answer_pipeline.rag_service.retrieve', fake_retrieve)
    monkeypatch.setattr('app.services.answer_pipeline.llm_service.stream_reply', fake_stream_reply)

    with client.stream(
        'POST',
        '/api/interview/chat/stream',
        json={
            'messages': [
                {'role': 'interviewer', 'content': 'retrieval'},
            ],
            'mode': 'text',
        },
    ) as response:
        assert response.status_code == 200
        body = ''.join(response.iter_text())

    assert body.count('"type":"delta"') == 2
    assert '"delta":"第一段"' in body
    assert '"delta":"第二段"' in body
    assert '"type":"sources"' in body
    assert '"type":"done","status":"done"' in body
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run:

```bash
uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_chat_stream_forwards_llm_chunks_as_multiple_delta_events -v
```

Expected: FAIL because `stream_answer()` still calls `generate_reply()` instead of `stream_reply()`.

- [ ] **Step 3: Update `stream_answer()` to relay model chunks immediately**

Change the responding phase in `backend/src/app/services/answer_pipeline.py` to this:

```python
    yield _event_payload(InterviewStreamEvent(type="status", status="responding", replyId=reply_id, createdAt=created_at))
    yield _event_payload(
        InterviewStreamEvent(
            type="thinking",
            status="responding",
            replyId=reply_id,
            createdAt=created_at,
            thinking=_create_thinking("responding", "正在把整理后的证据转成最终回答。"),
        )
    )

    try:
        for chunk in llm_service.stream_reply(messages, rag_result.context_text):
            yield _event_payload(
                InterviewStreamEvent(
                    type="delta",
                    status="responding",
                    replyId=reply_id,
                    createdAt=created_at,
                    delta=chunk,
                )
            )
    except LLMDependencyError as error:
        yield _event_payload(
            InterviewStreamEvent(
                type="error",
                status="error",
                replyId=reply_id,
                createdAt=created_at,
                error=str(error),
            )
        )
        yield _event_payload(InterviewStreamEvent(type="done", status="done", replyId=reply_id, createdAt=created_at))
        return

    yield _event_payload(
        InterviewStreamEvent(
            type="sources",
            replyId=reply_id,
            createdAt=created_at,
            sources=[citation.__dict__ for citation in rag_result.citations],
        )
    )
    yield _event_payload(InterviewStreamEvent(type="done", status="done", replyId=reply_id, createdAt=created_at))
```

Also remove the old buffered call:

```python
    try:
        reply_content = llm_service.generate_reply(messages, rag_result.context_text)
    except LLMDependencyError as error:
        ...

    for chunk in _chunk_text(reply_content):
        ...
```

- [ ] **Step 4: Run the targeted test to verify it passes**

Run:

```bash
uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_chat_stream_forwards_llm_chunks_as_multiple_delta_events -v
```

Expected: PASS

- [ ] **Step 5: Commit the pipeline streaming change**

```bash
git add backend/src/app/services/answer_pipeline.py backend/tests/test_interview_api.py
git commit -m "feat: stream Ark chunks over interview SSE"
```

---

### Task 3: Preserve failure behavior and non-streaming API compatibility

**Files:**
- Modify: `backend/tests/test_interview_api.py`
- Verify: `backend/src/app/services/llm_service.py`
- Verify: `backend/src/app/services/answer_pipeline.py`

- [ ] **Step 1: Add a failing test for streaming error propagation**

Add this test in `backend/tests/test_interview_api.py`:

```python
def test_interview_chat_stream_emits_error_when_streaming_llm_fails(monkeypatch) -> None:
    def fake_retrieve(query: str):
        assert query == 'retrieval'
        return type(
            'FakeRagResult',
            (),
            {
                'context_text': 'Candidate worked on retrieval and source attribution.',
                'citations': [],
            },
        )()

    def fake_stream_reply(messages, rag_context: str):
        yield '第一段'
        raise LLMDependencyError('Ark stream interrupted')

    monkeypatch.setattr('app.services.answer_pipeline.rag_service.retrieve', fake_retrieve)
    monkeypatch.setattr('app.services.answer_pipeline.llm_service.stream_reply', fake_stream_reply)

    with client.stream(
        'POST',
        '/api/interview/chat/stream',
        json={
            'messages': [
                {'role': 'interviewer', 'content': 'retrieval'},
            ],
            'mode': 'text',
        },
    ) as response:
        assert response.status_code == 200
        body = ''.join(response.iter_text())

    assert '"delta":"第一段"' in body
    assert '"type":"error","status":"error"' in body
    assert 'Ark stream interrupted' in body
    assert '"type":"done","status":"done"' in body
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run:

```bash
uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_chat_stream_emits_error_when_streaming_llm_fails -v
```

Expected: FAIL before the implementation is fully wired for stream-time exceptions.

- [ ] **Step 3: Keep the non-streaming API path unchanged and verify stream-time exception handling**

Confirm these code shapes remain true after Tasks 1-2:

`backend/src/app/services/llm_service.py`

```python
    def generate_reply(self, history_messages: list[dict[str, str]], rag_context: str) -> str:
        client = self.ensure_client()
        messages = self._build_messages(history_messages, rag_context)
        try:
            response = client.chat.completions.create(
                model=settings.ark_endpoint_id,
                messages=messages,
                temperature=0.3,
                stream=False,
            )
        except Exception as error:
            raise LLMDependencyError("Ark request failed") from error
```

`backend/src/app/services/answer_pipeline.py`

```python
    try:
        for chunk in llm_service.stream_reply(messages, rag_result.context_text):
            yield _event_payload(
                InterviewStreamEvent(
                    type="delta",
                    status="responding",
                    replyId=reply_id,
                    createdAt=created_at,
                    delta=chunk,
                )
            )
    except LLMDependencyError as error:
        yield _event_payload(
            InterviewStreamEvent(
                type="error",
                status="error",
                replyId=reply_id,
                createdAt=created_at,
                error=str(error),
            )
        )
        yield _event_payload(InterviewStreamEvent(type="done", status="done", replyId=reply_id, createdAt=created_at))
        return
```

No additional code is needed if these shapes are already in place from Tasks 1-2.

- [ ] **Step 4: Run the targeted error test and a non-streaming regression test**

Run:

```bash
uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_chat_stream_emits_error_when_streaming_llm_fails -v
uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_chat_calls_real_kb_and_ark_services -v
```

Expected:
- First command: PASS
- Second command: PASS

- [ ] **Step 5: Commit the compatibility coverage**

```bash
git add backend/tests/test_interview_api.py backend/src/app/services/llm_service.py backend/src/app/services/answer_pipeline.py
git commit -m "test: cover streaming error and chat compatibility"
```

---

### Task 4: Verify the running app shows real streaming behavior

**Files:**
- Verify: `backend/src/app/services/llm_service.py`
- Verify: `backend/src/app/services/answer_pipeline.py`
- Verify: `frontend/src/store/interview/index.ts`

- [ ] **Step 1: Start the backend API**

Run:

```bash
PYTHONPATH=/c/Users/DXM-1002/Desktop/xuanyu/xuanyu/backend/src uv run --directory backend uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Expected: `Uvicorn running on http://127.0.0.1:8010`

- [ ] **Step 2: Start the frontend app**

Run:

```bash
pnpm --dir frontend dev --host 127.0.0.1 --port 5173
```

Expected: `Local: http://127.0.0.1:5173/`

- [ ] **Step 3: Verify the SSE endpoint emits multiple deltas from a live request**

Run:

```bash
python - <<'PY'
import json, urllib.request
req = urllib.request.Request(
    'http://127.0.0.1:8010/api/interview/chat/stream',
    data=json.dumps({
        'messages': [{'role': 'interviewer', 'content': '雷神是什么'}],
        'mode': 'text'
    }).encode('utf-8'),
    headers={'Content-Type': 'application/json', 'Accept': 'text/event-stream'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=120) as resp:
    print(resp.status)
    print(resp.headers.get('content-type'))
    raw = resp.read()
print(raw.decode('utf-8', errors='replace').encode('ascii', 'backslashreplace').decode('ascii'))
PY
```

Expected:
- `200`
- `text/event-stream; charset=utf-8`
- Multiple `data: {"type":"delta"...}` frames, not a single final reply frame

- [ ] **Step 4: Verify the frontend still appends `delta` chunks without code changes**

Check this existing logic in `frontend/src/store/interview/index.ts` remains unchanged and compatible:

```ts
          if (event.type === 'delta' && event.delta) {
            currentAssistant.content += event.delta
            currentAssistant.state = 'streaming'
          }
```

Then open `http://127.0.0.1:5173`, submit a question, and confirm the assistant message grows progressively before `sources` appear.

Expected: visible incremental text growth instead of a single post-generation dump.

- [ ] **Step 5: Commit if verification required by branch policy; otherwise leave uncommitted**

```bash
git status --short
```

Expected: only the planned backend test/service files changed unless you intentionally updated more.

---

## Self-Review

- Spec coverage: This plan covers the chosen design scope only — real token streaming for `/api/interview/chat/stream` while preserving current frontend SSE contract and non-streaming `/api/interview/chat` compatibility.
- Placeholder scan: No `TODO`, `TBD`, or undefined “write tests later” steps remain.
- Type consistency: `stream_reply()` is introduced once in `LLMService` and used consistently in `answer_pipeline` and tests; existing `generate_reply()` remains the non-streaming path.
