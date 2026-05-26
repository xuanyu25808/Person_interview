# AI Interview LLM/RAG Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real text-mode interview chat pipeline that uses the old project's Volcengine LLM and knowledge-base retrieval, returns citations with each assistant reply, and wires the current frontend interview page to the new backend API.

**Architecture:** Extend the current FastAPI backend with a focused interview chat API, a retriever service, and an LLM service. Keep RTC and scene-based voice flows out of scope for now; the frontend remains the current terminal-style interview UI and only swaps mock transport for the new HTTP chat endpoint.

**Tech Stack:** FastAPI, Pydantic Settings, httpx, Volcengine Ark SDK, Vue 3, Pinia, fetch, Vitest

---

## File Map

### Backend

- Modify: `backend/src/app/core/config.py`
  - Add concrete LLM/RAG settings used by the new services.
- Modify: `backend/src/app/main.py`
  - Register the interview router under the existing API prefix.
- Create: `backend/src/app/schemas/interview.py`
  - Define request/response models and shared message/citation schemas.
- Create: `backend/src/app/services/rag_service.py`
  - Call the Volcengine knowledge base search API and normalize context plus citations.
- Create: `backend/src/app/services/llm_service.py`
  - Initialize Ark client and generate a non-streaming interview answer from history plus retrieved context.
- Create: `backend/src/app/api/interview.py`
  - Validate input, orchestrate retrieval and generation, and return a single assistant reply.
- Modify: `backend/src/app/api/__init__.py`
  - Export and include the new interview router in the aggregate API router.
- Create: `backend/tests/test_interview_api.py`
  - Cover request validation, success path, and retrieval-failure fallback path.
- Create: `backend/tests/test_rag_service.py`
  - Cover citation normalization from knowledge-base payloads.

### Frontend

- Modify: `frontend/src/store/interview/api.ts`
  - Replace silent mock fallback with real request/response mapping for the new API shape.
- Modify: `frontend/src/store/interview/index.ts`
  - Send current message history in the new backend contract and keep assistant citations on the stored reply.
- Modify: `frontend/src/store/interview/types.ts`
  - Keep the message/citation contract aligned with the backend and expose request-side roles if needed.
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.vue`
  - Keep citation rendering but ensure missing/relative URLs degrade cleanly in the UI.
- Create: `frontend/src/store/interview/api.test.ts`
  - Cover payload mapping and invalid backend payload handling.

---

### Task 1: Add backend config and schemas

**Files:**
- Modify: `backend/src/app/core/config.py`
- Create: `backend/src/app/schemas/interview.py`
- Test: `backend/tests/test_interview_api.py`

- [ ] **Step 1: Write the failing backend schema/config test**

```python
from app.core.config import Settings
from app.schemas.interview import InterviewChatRequest, InterviewChatResponse, InterviewMessage, MessageCitation


def test_interview_settings_defaults_and_schema_shapes():
    settings = Settings()

    assert settings.interview_model == "placeholder"
    assert settings.ark_base_url == "https://ark.cn-beijing.volces.com/api/v3"
    assert settings.kb_domain == "api-knowledgebase.mlp.cn-beijing.volces.com"

    citation = MessageCitation(
        title="projects.md",
        url="knowledge/projects.md",
        snippet="candidate project highlights",
        kind="knowledge",
    )
    reply = InterviewMessage(
        id="msg_1",
        role="assistant",
        content="answer",
        sources=[citation],
        createdAt="2026-05-22T12:00:00Z",
    )
    request = InterviewChatRequest(
        messages=[{"role": "interviewer", "content": "介绍一下你的项目"}],
        mode="text",
    )
    response = InterviewChatResponse(reply=reply)

    assert request.messages[0].role == "interviewer"
    assert response.reply.sources[0].title == "projects.md"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_settings_defaults_and_schema_shapes -v`
Expected: FAIL with import or attribute errors for missing interview schemas/settings.

- [ ] **Step 3: Write minimal config and schema implementation**

Update `backend/src/app/core/config.py` to:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Interview Twin API"
    api_prefix: str = "/api"
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    interview_model: str = "placeholder"
    interview_mode: str = "text"

    ark_api_key: str = ""
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    ark_endpoint_id: str = ""

    kb_api_key: str = ""
    kb_project_name: str = "default"
    kb_collection_name: str = "dw_ai"
    kb_domain: str = "api-knowledgebase.mlp.cn-beijing.volces.com"

    volcengine_app_id: str = ""
    volcengine_access_key: str = ""
    volcengine_secret_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
```

Create `backend/src/app/schemas/interview.py`:

```python
from typing import Literal

from pydantic import BaseModel, Field


class MessageCitation(BaseModel):
    title: str
    url: str
    snippet: str
    kind: str


class InterviewTurn(BaseModel):
    role: Literal["interviewer", "assistant"]
    content: str = Field(min_length=1)


class InterviewMessage(InterviewTurn):
    id: str
    sources: list[MessageCitation]
    createdAt: str


class InterviewChatRequest(BaseModel):
    messages: list[InterviewTurn] = Field(min_length=1)
    mode: Literal["text", "voice"] = "text"


class InterviewChatResponse(BaseModel):
    reply: InterviewMessage
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_settings_defaults_and_schema_shapes -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/core/config.py backend/src/app/schemas/interview.py backend/tests/test_interview_api.py
git commit -m "feat: add interview chat schemas and config"
```

---

### Task 2: Implement the RAG service with citation normalization

**Files:**
- Create: `backend/src/app/services/rag_service.py`
- Test: `backend/tests/test_rag_service.py`

- [ ] **Step 1: Write the failing RAG normalization test**

Create `backend/tests/test_rag_service.py` with:

```python
from app.services.rag_service import RagService


def test_extract_result_builds_context_and_citations():
    service = RagService()
    payload = {
        "data": {
            "result_list": [
                {
                    "content": "项目经历应突出背景、职责和结果。",
                    "doc_name": "projects.md",
                    "chunk_title": "项目表达",
                    "attachment_link": "knowledge/projects.md",
                },
                {
                    "content": "回答要围绕真实经历，不要编造。",
                    "doc_name": "resume.md",
                    "attachment_link": "knowledge/resume.md",
                },
            ]
        }
    }

    result = service._extract_result(payload)

    assert "项目经历应突出背景、职责和结果。" in result["context_text"]
    assert len(result["citations"]) == 2
    assert result["citations"][0]["title"] == "项目表达"
    assert result["citations"][0]["url"] == "knowledge/projects.md"
    assert result["citations"][1]["title"] == "resume.md"
    assert result["citations"][1]["kind"] == "knowledge"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory backend pytest backend/tests/test_rag_service.py::test_extract_result_builds_context_and_citations -v`
Expected: FAIL because `RagService` does not exist.

- [ ] **Step 3: Write minimal RAG service implementation**

Create `backend/src/app/services/rag_service.py`:

```python
import httpx

from app.core.config import settings


class RagService:
    def _build_url(self) -> str:
        return f"http://{settings.kb_domain}/api/knowledge/collection/search_knowledge"

    def _build_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Host": settings.kb_domain,
            "Authorization": f"Bearer {settings.kb_api_key}",
        }

    def _build_body(self, query: str) -> dict:
        return {
            "project": settings.kb_project_name,
            "name": settings.kb_collection_name,
            "query": query,
            "limit": 3,
            "pre_processing": {
                "need_instruction": True,
                "return_token_usage": True,
                "messages": [
                    {"role": "system", "content": ""},
                    {"role": "user", "content": query},
                ],
            },
            "dense_weight": 0.5,
            "post_processing": {
                "get_attachment_link": True,
                "rerank_only_chunk": False,
                "rerank_switch": False,
            },
        }

    def _extract_result(self, data: dict) -> dict:
        result_list = data.get("data", {}).get("result_list", [])
        citations = []
        contents = []

        for item in result_list:
            content = (item.get("content") or "").strip()
            if not content:
                continue

            contents.append(content)
            citations.append(
                {
                    "title": item.get("chunk_title") or item.get("doc_name") or "knowledge",
                    "url": item.get("attachment_link") or item.get("doc_url") or "",
                    "snippet": content,
                    "kind": "knowledge",
                }
            )

        return {
            "context_text": "\n\n".join(contents),
            "citations": citations,
        }

    async def retrieve(self, query: str) -> dict:
        if not settings.kb_api_key:
            return {"context_text": "", "citations": []}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._build_url(),
                headers=self._build_headers(),
                json=self._build_body(query),
                timeout=10.0,
            )

        if response.status_code != 200:
            return {"context_text": "", "citations": []}

        return self._extract_result(response.json())


rag_service = RagService()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --directory backend pytest backend/tests/test_rag_service.py::test_extract_result_builds_context_and_citations -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/services/rag_service.py backend/tests/test_rag_service.py
git commit -m "feat: add interview rag service"
```

---

### Task 3: Implement the LLM service for interview answers

**Files:**
- Create: `backend/src/app/services/llm_service.py`
- Test: `backend/tests/test_interview_api.py`

- [ ] **Step 1: Write the failing LLM prompt test**

Append to `backend/tests/test_interview_api.py`:

```python
from app.services.llm_service import LLMService


def test_build_messages_includes_interview_context():
    service = LLMService()

    messages = service._build_messages(
        [{"role": "interviewer", "content": "介绍你的项目亮点"}],
        "项目经历应突出背景、职责和结果。",
    )

    assert messages[0]["role"] == "system"
    assert "AI 面试分身" in messages[0]["content"]
    assert "项目经历应突出背景、职责和结果。" in messages[0]["content"]
    assert messages[1]["role"] == "interviewer"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory backend pytest backend/tests/test_interview_api.py::test_build_messages_includes_interview_context -v`
Expected: FAIL because `LLMService` does not exist.

- [ ] **Step 3: Write minimal LLM service implementation**

Create `backend/src/app/services/llm_service.py`:

```python
from app.core.config import settings


class LLMService:
    def __init__(self) -> None:
        self.client = None
        self.init_error = None

    def ensure_client(self) -> bool:
        if self.client is not None:
            return True

        if not settings.ark_api_key or not settings.ark_endpoint_id:
            self.init_error = "missing Ark configuration"
            return False

        try:
            from volcenginesdkarkruntime import Ark

            self.client = Ark(
                base_url=settings.ark_base_url,
                api_key=settings.ark_api_key,
                timeout=1800,
            )
            self.init_error = None
            return True
        except Exception as exc:
            self.init_error = str(exc)
            return False

    def _build_system_prompt(self, rag_context: str) -> str:
        base_prompt = (
            "你是候选人的 AI 面试分身。"
            "请优先依据提供的真实资料回答面试问题，表达简洁、专业、自然。"
            "如果资料不足以支持某个具体经历或结论，请明确说明边界，不要编造。"
        )

        if not rag_context:
            return base_prompt

        return f"{base_prompt}\n\n### 参考资料\n{rag_context.strip()}"

    def _build_messages(self, history_messages: list[dict[str, str]], rag_context: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self._build_system_prompt(rag_context)},
            *history_messages,
        ]

    def generate(self, history_messages: list[dict[str, str]], rag_context: str) -> str:
        if not self.ensure_client():
            raise RuntimeError(self.init_error or "Ark client init failed")

        completion = self.client.chat.completions.create(
            model=settings.ark_endpoint_id,
            messages=self._build_messages(history_messages, rag_context),
            temperature=0.3,
            stream=False,
        )
        return (completion.choices[0].message.content or "").strip()


llm_service = LLMService()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --directory backend pytest backend/tests/test_interview_api.py::test_build_messages_includes_interview_context -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/services/llm_service.py backend/tests/test_interview_api.py
git commit -m "feat: add interview llm service"
```

---

### Task 4: Add the interview API route and wire it into FastAPI

**Files:**
- Create: `backend/src/app/api/interview.py`
- Modify: `backend/src/app/api/__init__.py`
- Modify: `backend/src/app/main.py`
- Test: `backend/tests/test_interview_api.py`

- [ ] **Step 1: Write the failing API success-path test**

Append to `backend/tests/test_interview_api.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_interview_chat_returns_reply(monkeypatch):
    async def fake_retrieve(query: str):
        return {
            "context_text": "项目经历应突出背景、职责和结果。",
            "citations": [
                {
                    "title": "projects.md",
                    "url": "knowledge/projects.md",
                    "snippet": "项目经历应突出背景、职责和结果。",
                    "kind": "knowledge",
                }
            ],
        }

    def fake_generate(history_messages, rag_context: str):
        assert history_messages[-1]["content"] == "请介绍一下你做过的项目"
        assert "职责和结果" in rag_context
        return "我会先从项目背景、职责和结果来回答。"

    monkeypatch.setattr("app.api.interview.rag_service.retrieve", fake_retrieve)
    monkeypatch.setattr("app.api.interview.llm_service.generate", fake_generate)

    client = TestClient(app)
    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "interviewer", "content": "请介绍一下你做过的项目"}
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"]["role"] == "assistant"
    assert body["reply"]["content"] == "我会先从项目背景、职责和结果来回答。"
    assert body["reply"]["sources"][0]["title"] == "projects.md"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_chat_returns_reply -v`
Expected: FAIL because `/api/interview/chat` does not exist.

- [ ] **Step 3: Write minimal route and router wiring**

Create `backend/src/app/api/interview.py`:

```python
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.schemas.interview import InterviewChatRequest, InterviewChatResponse, InterviewMessage
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/chat", response_model=InterviewChatResponse)
async def chat(request: InterviewChatRequest) -> InterviewChatResponse:
    if request.messages[-1].role != "interviewer":
        raise HTTPException(status_code=400, detail="last message must be interviewer")

    retrieval = await rag_service.retrieve(request.messages[-1].content)
    answer = llm_service.generate(
        [message.model_dump() for message in request.messages],
        retrieval["context_text"],
    )

    reply = InterviewMessage(
        id=f"msg_{uuid4().hex}",
        role="assistant",
        content=answer,
        sources=retrieval["citations"],
        createdAt=datetime.now(timezone.utc).isoformat(),
    )
    return InterviewChatResponse(reply=reply)
```

Update `backend/src/app/api/__init__.py` to:

```python
from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.interview import router as interview_router

router = APIRouter()
router.include_router(health_router)
router.include_router(interview_router)
```

Keep `backend/src/app/main.py` as:

```python
from fastapi import FastAPI

from app.api import router as api_router
from app.core.config import settings
from app.core.cors import configure_cors
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title=settings.app_name)
configure_cors(app)
app.include_router(api_router, prefix=settings.api_prefix)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_chat_returns_reply -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/api/interview.py backend/src/app/api/__init__.py backend/src/app/main.py backend/tests/test_interview_api.py
git commit -m "feat: add interview chat api"
```

---

### Task 5: Handle retrieval failure without breaking the chat flow

**Files:**
- Modify: `backend/src/app/api/interview.py`
- Test: `backend/tests/test_interview_api.py`

- [ ] **Step 1: Write the failing fallback test**

Append to `backend/tests/test_interview_api.py`:

```python
def test_interview_chat_allows_empty_retrieval(monkeypatch):
    async def fake_retrieve(query: str):
        return {"context_text": "", "citations": []}

    def fake_generate(history_messages, rag_context: str):
        assert rag_context == ""
        return "我会基于现有资料范围回答这个问题。"

    monkeypatch.setattr("app.api.interview.rag_service.retrieve", fake_retrieve)
    monkeypatch.setattr("app.api.interview.llm_service.generate", fake_generate)

    client = TestClient(app)
    response = client.post(
        "/api/interview/chat",
        json={
            "messages": [
                {"role": "interviewer", "content": "你如何做技术选型"}
            ],
            "mode": "text",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"]["content"] == "我会基于现有资料范围回答这个问题。"
    assert body["reply"]["sources"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_chat_allows_empty_retrieval -v`
Expected: FAIL if the route assumes retrieval always returns citations or crashes on empty context.

- [ ] **Step 3: Write minimal fallback implementation**

Update `backend/src/app/api/interview.py` so retrieval defaults are normalized before generation:

```python
    retrieval = await rag_service.retrieve(request.messages[-1].content)
    context_text = retrieval.get("context_text", "")
    citations = retrieval.get("citations", [])

    answer = llm_service.generate(
        [message.model_dump() for message in request.messages],
        context_text,
    )

    reply = InterviewMessage(
        id=f"msg_{uuid4().hex}",
        role="assistant",
        content=answer,
        sources=citations,
        createdAt=datetime.now(timezone.utc).isoformat(),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --directory backend pytest backend/tests/test_interview_api.py::test_interview_chat_allows_empty_retrieval -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/app/api/interview.py backend/tests/test_interview_api.py
git commit -m "fix: allow interview chat without citations"
```

---

### Task 6: Update frontend API transport to the new backend contract

**Files:**
- Modify: `frontend/src/store/interview/api.ts`
- Create: `frontend/src/store/interview/api.test.ts`

- [ ] **Step 1: Write the failing frontend API test**

Create `frontend/src/store/interview/api.test.ts`:

```ts
import { describe, expect, it, vi, beforeEach } from 'vitest'

import { sendInterviewMessage } from './api'

describe('sendInterviewMessage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('posts messages to the backend and returns the reply', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          reply: {
            id: 'msg_1',
            role: 'assistant',
            content: '我会从项目背景、职责和结果来回答。',
            sources: [
              {
                title: 'projects.md',
                url: 'knowledge/projects.md',
                snippet: '项目经历应突出背景、职责和结果。',
                kind: 'knowledge',
              },
            ],
            createdAt: '2026-05-22T12:00:00Z',
          },
        }),
      }),
    )

    const response = await sendInterviewMessage({
      messages: [{ role: 'interviewer', content: '请介绍一下你做过的项目' }],
      mode: 'text',
    })

    expect(fetch).toHaveBeenCalledWith('/api/interview/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'interviewer', content: '请介绍一下你做过的项目' }],
        mode: 'text',
      }),
    })
    expect(response.reply.sources[0].title).toBe('projects.md')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --dir frontend vitest run src/store/interview/api.test.ts`
Expected: FAIL because the current API function still sends `session_id`, `message`, and `history`.

- [ ] **Step 3: Write minimal frontend API implementation**

Replace `frontend/src/store/interview/api.ts` with:

```ts
import type { InterviewMessage, InterviewMode, MessageCitation } from './types'

export interface ChatRequest {
  messages: Array<{
    role: 'interviewer' | 'assistant'
    content: string
  }>
  mode: InterviewMode
}

export interface ChatResponse {
  reply: InterviewMessage
}

const isCitation = (value: unknown): value is MessageCitation => {
  if (!value || typeof value !== 'object') {
    return false
  }

  const citation = value as Record<string, unknown>
  return (
    typeof citation.title === 'string' &&
    typeof citation.url === 'string' &&
    typeof citation.snippet === 'string' &&
    typeof citation.kind === 'string'
  )
}

const isInterviewMessage = (value: unknown): value is InterviewMessage => {
  if (!value || typeof value !== 'object') {
    return false
  }

  const message = value as Record<string, unknown>
  return (
    typeof message.id === 'string' &&
    (message.role === 'assistant' || message.role === 'interviewer') &&
    typeof message.content === 'string' &&
    Array.isArray(message.sources) &&
    message.sources.every(isCitation) &&
    typeof message.createdAt === 'string'
  )
}

export const sendInterviewMessage = async ({ messages, mode }: ChatRequest): Promise<ChatResponse> => {
  const response = await fetch('/api/interview/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages,
      mode,
    }),
  })

  if (!response.ok) {
    throw new Error('Interview chat request failed')
  }

  const payload = (await response.json()) as { reply?: unknown }
  if (!isInterviewMessage(payload.reply)) {
    throw new Error('Interview chat payload has invalid reply shape')
  }

  return {
    reply: payload.reply,
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --dir frontend vitest run src/store/interview/api.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/store/interview/api.ts frontend/src/store/interview/api.test.ts
git commit -m "feat: wire interview frontend api to backend"
```

---

### Task 7: Update the interview store to send message history correctly

**Files:**
- Modify: `frontend/src/store/interview/index.ts`
- Modify: `frontend/src/store/interview/types.ts`
- Test: `frontend/src/store/interview/api.test.ts`

- [ ] **Step 1: Write the failing store-side payload test**

Append to `frontend/src/store/interview/api.test.ts`:

```ts
import { createPinia, setActivePinia } from 'pinia'

import { useInterviewStore } from './index'

it('sends the full conversation in backend format', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        reply: {
          id: 'msg_2',
          role: 'assistant',
          content: '可以从背景、职责和结果三部分回答。',
          sources: [],
          createdAt: '2026-05-22T12:00:00Z',
        },
      }),
    }),
  )

  setActivePinia(createPinia())
  const store = useInterviewStore()
  store.setDraft('请介绍一下你做过的项目')

  await store.send()

  expect(fetch).toHaveBeenCalledWith(
    '/api/interview/chat',
    expect.objectContaining({
      body: JSON.stringify({
        messages: [{ role: 'interviewer', content: '请介绍一下你做过的项目' }],
        mode: 'text',
      }),
    }),
  )
  expect(store.messages[1].role).toBe('assistant')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --dir frontend vitest run src/store/interview/api.test.ts`
Expected: FAIL because the store still calls the old API signature with `sessionId`, `message`, and `history`.

- [ ] **Step 3: Write minimal store update**

Update the `send` function in `frontend/src/store/interview/index.ts` to:

```ts
  const send = async (question?: string) => {
    const value = (question ?? draft.value).trim()
    if (!value || isBusy.value) {
      return
    }

    const userMessage: InterviewMessage = {
      id: crypto.randomUUID(),
      role: 'interviewer',
      content: value,
      sources: [],
      createdAt: new Date().toISOString(),
    }

    messages.value.push(userMessage)
    draft.value = ''
    status.value = 'retrieving'

    try {
      const payload = await sendInterviewMessage({
        messages: messages.value.map((message) => ({
          role: message.role,
          content: message.content,
        })),
        mode: mode.value,
      })

      status.value = 'responding'
      messages.value.push(payload.reply)
    } catch {
      messages.value.push({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '当前后端问答链路暂时不可用，请稍后再试。',
        sources: [],
        createdAt: new Date().toISOString(),
      })
    } finally {
      status.value = 'idle'
    }
  }
```

Keep `frontend/src/store/interview/types.ts` as:

```ts
export type InterviewMode = 'text' | 'voice'

export type InterviewStatus =
  | 'idle'
  | 'listening'
  | 'transcribing'
  | 'retrieving'
  | 'thinking'
  | 'responding'

export interface MessageCitation {
  title: string
  url: string
  snippet: string
  kind: string
}

export interface InterviewMessage {
  id: string
  role: 'interviewer' | 'assistant'
  content: string
  sources: MessageCitation[]
  createdAt: string
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --dir frontend vitest run src/store/interview/api.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/store/interview/index.ts frontend/src/store/interview/types.ts frontend/src/store/interview/api.test.ts
git commit -m "feat: send interview history to backend"
```

---

### Task 8: Finish the citation UI behavior for backend-driven results

**Files:**
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.vue`
- Test: `frontend/src/store/interview/api.test.ts`

- [ ] **Step 1: Write the failing citation link test**

Append to `frontend/src/store/interview/api.test.ts`:

```ts
import { mount } from '@vue/test-utils'

import TerminalChatPanel from '../../pages/interview/components/TerminalChatPanel.vue'

it('renders assistant citations with clickable links', () => {
  const wrapper = mount(TerminalChatPanel, {
    props: {
      messages: [
        {
          id: 'msg_1',
          role: 'assistant',
          content: '这是回答。',
          createdAt: '2026-05-22T12:00:00Z',
          sources: [
            {
              title: 'projects.md',
              url: 'knowledge/projects.md',
              snippet: '项目经历应突出背景、职责和结果。',
              kind: 'knowledge',
            },
          ],
        },
      ],
    },
  })

  expect(wrapper.text()).toContain('引用来源')
  expect(wrapper.text()).toContain('projects.md')
  expect(wrapper.find('a').attributes('href')).toBe('knowledge/projects.md')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --dir frontend vitest run src/store/interview/api.test.ts`
Expected: FAIL if the current test setup cannot mount the component or the rendering assumptions are incomplete.

- [ ] **Step 3: Write minimal citation UI adjustment**

Update the link block in `frontend/src/pages/interview/components/TerminalChatPanel.vue` to handle empty URLs without rendering a broken anchor:

```vue
<section v-if="message.role === 'assistant' && message.sources.length" class="message-citations">
  <h3 class="message-citations-title">引用来源</h3>
  <ul class="message-citations-list">
    <li
      v-for="source in message.sources"
      :key="`${message.id}-${source.kind}-${source.title}`"
      class="citation-card"
    >
      <p class="citation-title">{{ source.title }}</p>
      <a
        v-if="source.url"
        class="citation-link"
        :href="source.url"
        target="_blank"
        rel="noreferrer noopener"
      >
        {{ source.url }}
      </a>
      <p v-else class="citation-link citation-link-muted">未提供链接</p>
      <p class="citation-snippet">{{ source.snippet }}</p>
    </li>
  </ul>
</section>
```

Add style:

```css
.citation-link-muted {
  color: #6b7280;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --dir frontend vitest run src/store/interview/api.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/interview/components/TerminalChatPanel.vue frontend/src/store/interview/api.test.ts
git commit -m "feat: render interview citations from backend replies"
```

---

### Task 9: Run project verification

**Files:**
- Test: `backend/tests/test_interview_api.py`
- Test: `backend/tests/test_rag_service.py`
- Test: `frontend/src/store/interview/api.test.ts`

- [ ] **Step 1: Run backend interview API tests**

Run: `uv run --directory backend pytest backend/tests/test_interview_api.py -v`
Expected: PASS

- [ ] **Step 2: Run backend RAG service tests**

Run: `uv run --directory backend pytest backend/tests/test_rag_service.py -v`
Expected: PASS

- [ ] **Step 3: Run frontend interview tests**

Run: `pnpm --dir frontend vitest run src/store/interview/api.test.ts`
Expected: PASS

- [ ] **Step 4: Run frontend production build**

Run: `pnpm --dir frontend build`
Expected: PASS with generated build output and no type errors blocking the build.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_interview_api.py backend/tests/test_rag_service.py frontend/src/store/interview/api.test.ts
git commit -m "test: verify interview llm rag integration"
```
