# AI 面试分身引用区改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 删除右侧 TerminalStatusPanel，并把每条 assistant 回答的引用来源以内联引用区的形式展示在消息下方。

**Architecture:** 前端继续以 Pinia store 驱动单页聊天流程，但移除只服务于右侧面板的 `topic` 与 `activeSources` 状态，把引用数据完全归属到 `InterviewMessage.sources`。后端响应契约同步从轻量标签升级为完整 citation 对象，消息组件负责渲染来源名称、可点击链接和摘要片段。

**Tech Stack:** Vue 3, Pinia, TypeScript, Vite, Vitest, Vue Test Utils, FastAPI-compatible JSON API contract

---

## File Structure

### Existing files to modify
- Modify: `frontend/src/pages/interview/InterviewPage.vue` — 移除右侧面板引用，收敛为单列聊天布局
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.vue` — 为 assistant 消息增加 citation 渲染区
- Modify: `frontend/src/store/interview/types.ts` — 把 `SourceTag` 升级为完整 citation 类型
- Modify: `frontend/src/store/interview/index.ts` — 删除 `topic`、`activeSources` 及相关赋值/重置逻辑
- Modify: `frontend/src/store/interview/api.ts` — 更新响应类型与 mock fallback，使 `reply.sources` 返回完整 citation 结构
- Modify: `frontend/src/store/interview/mock.ts` — 更新 mock 数据结构，移除会话级 `topic`/`activeSources` 依赖
- Modify: `frontend/src/ui-copy.test.ts` — 删除对 `TerminalStatusPanel.vue` 文案的断言，新增引用区文案断言

### Existing files to delete
- Delete: `frontend/src/pages/interview/components/TerminalStatusPanel.vue` — 右侧独立状态面板不再保留

### Existing tests or verification targets to add/modify
- Modify: `frontend/src/store/interview/api.ts` — 通过内置 mock fallback 维持可运行性并体现新契约
- Create: `frontend/src/pages/interview/components/TerminalChatPanel.test.ts` — 验证 assistant/interviewer 消息的 citation 渲染边界
- Create: `frontend/src/store/interview/index.test.ts` — 验证 send/reset 流程删除面板状态后仍正确工作

---

### Task 1: Upgrade interview message citations and API contract

**Files:**
- Modify: `frontend/src/store/interview/types.ts:1-21`
- Modify: `frontend/src/store/interview/api.ts:1-90`
- Modify: `frontend/src/store/interview/mock.ts:1-80`

- [ ] **Step 1: Write the failing type target for the new citation shape**

```ts
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

- [ ] **Step 2: Run the frontend type-aware test command to verify the current API contract is still using the old structure**

Run: `pnpm --filter frontend test -- --run`
Expected: FAIL with type or assertion errors because `label` / `topic` / `activeSources` still exist in the current contract

- [ ] **Step 3: Replace `frontend/src/store/interview/types.ts` with the new citation model**

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

- [ ] **Step 4: Replace `frontend/src/store/interview/mock.ts` so mock replies return per-message citations instead of session-level source tags**

```ts
import type { InterviewMessage, MessageCitation } from './types'

interface MockReply {
  content: string
  sources: MessageCitation[]
}

const openingSources: MessageCitation[] = [
  {
    title: 'resume.md',
    url: '/knowledge/resume.md',
    snippet: '候选人长期聚焦前端工程化、AI 应用落地与复杂交互体验设计。',
    kind: 'resume',
  },
  {
    title: 'projects.md',
    url: '/knowledge/projects.md',
    snippet: '项目资料覆盖 AI 面试分身、语音交互链路与知识检索问答设计。',
    kind: 'projects',
  },
]

export const createMockWelcomeMessage = (): InterviewMessage => ({
  id: 'welcome',
  role: 'assistant',
  content:
    '欢迎来到 AI 面试分身演示页。你可以直接追问项目经历、架构取舍、技术深度，或者我在工程推进中的判断方式。',
  sources: openingSources,
  createdAt: new Date().toISOString(),
})

const mockReplies: MockReply[] = [
  {
    content:
      '我会先从 AI 面试分身切入，因为它同时覆盖了前端交互、RAG、语音链路和面试场景下的产品取舍。',
    sources: [
      {
        title: 'projects.md',
        url: '/knowledge/projects.md',
        snippet: 'AI 面试分身项目重点是让回答基于真实资料，而不是通用大模型自由发挥。',
        kind: 'projects',
      },
      {
        title: 'interview_qa.md',
        url: '/knowledge/interview_qa.md',
        snippet: '在面试叙事里，优先强调单页收敛、RAG 约束和上下文连续性。',
        kind: 'interview_qa',
      },
    ],
  },
  {
    content:
      '如果面试官继续追问技术深度，我通常会把回答拆成约束、方案、取舍和落地结果四个部分。',
    sources: [
      {
        title: 'notes.md',
        url: '/knowledge/notes.md',
        snippet: '技术说明优先围绕真实项目上下文解释，而不是脱离经历做泛泛原理回答。',
        kind: 'notes',
      },
    ],
  },
]

export const buildMockReply = (turn: number): InterviewMessage => {
  const payload = mockReplies[turn % mockReplies.length]

  return {
    id: crypto.randomUUID(),
    role: 'assistant',
    content: payload.content,
    sources: payload.sources,
    createdAt: new Date().toISOString(),
  }
}
```

- [ ] **Step 5: Replace `frontend/src/store/interview/api.ts` so the response contract no longer requires `topic` and returns message citations directly**

```ts
import { buildMockReply } from './mock'
import type { InterviewMessage } from './types'

interface SendInterviewMessageParams {
  sessionId: string
  message: string
  history: Array<{
    role: InterviewMessage['role']
    content: string
  }>
}

interface InterviewApiResponse {
  reply: InterviewMessage
}

export const sendInterviewMessage = async ({
  sessionId,
  message,
  history,
}: SendInterviewMessageParams): Promise<InterviewApiResponse> => {
  try {
    const response = await fetch('/api/interview/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sessionId,
        message,
        history,
      }),
    })

    if (!response.ok) {
      throw new Error(`Interview API request failed: ${response.status}`)
    }

    return (await response.json()) as InterviewApiResponse
  } catch {
    return {
      reply: buildMockReply(history.length),
    }
  }
}
```

- [ ] **Step 6: Run the frontend test command again to verify the contract changes compile cleanly before store and UI updates**

Run: `pnpm --filter frontend test -- --run`
Expected: FAIL, but now only on store/UI assertions that still reference `topic`, `activeSources`, or `label`

- [ ] **Step 7: Commit**

```bash
git add frontend/src/store/interview/types.ts frontend/src/store/interview/api.ts frontend/src/store/interview/mock.ts
git commit -m "refactor: upgrade interview message citations"
```

### Task 2: Remove side-panel-only store state and add store tests

**Files:**
- Modify: `frontend/src/store/interview/index.ts:1-149`
- Create: `frontend/src/store/interview/index.test.ts`

- [ ] **Step 1: Create the failing store test in `frontend/src/store/interview/index.test.ts`**

```ts
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('./api', () => ({
  sendInterviewMessage: vi.fn(async () => ({
    reply: {
      id: 'assistant-1',
      role: 'assistant',
      content: 'mock reply',
      sources: [
        {
          title: 'projects.md',
          url: '/knowledge/projects.md',
          snippet: 'mock snippet',
          kind: 'projects',
        },
      ],
      createdAt: '2026-05-21T00:00:00.000Z',
    },
  })),
}))

import { useInterviewStore } from './index'

describe('useInterviewStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('appends interviewer and assistant messages without tracking activeSources or topic', async () => {
    const store = useInterviewStore()

    await store.send('介绍一下你的代表项目')

    expect(store.messages.at(-1)?.sources[0]?.title).toBe('projects.md')
    expect('activeSources' in store).toBe(false)
    expect('topic' in store).toBe(false)
  })

  it('reset restores the welcome message and clears busy state', () => {
    const store = useInterviewStore()

    store.messages.push({
      id: 'assistant-2',
      role: 'assistant',
      content: 'extra',
      sources: [],
      createdAt: '2026-05-21T00:00:00.000Z',
    })
    store.status = 'responding'
    store.reset()

    expect(store.messages).toHaveLength(1)
    expect(store.messages[0].id).toBe('welcome')
    expect(store.status).toBe('idle')
  })
})
```

- [ ] **Step 2: Run the store test to verify it fails before the store is simplified**

Run: `pnpm --filter frontend test -- --run frontend/src/store/interview/index.test.ts`
Expected: FAIL because `useInterviewStore` still exposes `topic` / `activeSources` and expects API payloads with `topic`

- [ ] **Step 3: Replace `frontend/src/store/interview/index.ts` with a store that only tracks real session state**

```ts
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { sendInterviewMessage } from './api'
import type { InterviewMessage, InterviewMode, InterviewStatus, MessageCitation } from './types'

const sessionId = () => crypto.randomUUID()

const openingSources: MessageCitation[] = [
  {
    title: 'resume.md',
    url: '/knowledge/resume.md',
    snippet: '候选人长期聚焦前端工程化、AI 应用落地与复杂交互体验设计。',
    kind: 'resume',
  },
  {
    title: 'projects.md',
    url: '/knowledge/projects.md',
    snippet: '项目资料覆盖 AI 面试分身、语音交互链路与知识检索问答设计。',
    kind: 'projects',
  },
]

const createWelcomeMessage = (): InterviewMessage => ({
  id: 'welcome',
  role: 'assistant',
  content:
    '欢迎来到 AI 面试分身演示页。你可以直接追问项目经历、架构取舍、技术深度，或者我在工程推进中的判断方式。',
  sources: openingSources,
  createdAt: new Date().toISOString(),
})

export const useInterviewStore = defineStore('interview', () => {
  const mode = ref<InterviewMode>('text')
  const speechEnabled = ref(true)
  const status = ref<InterviewStatus>('idle')
  const voiceStatus = ref<InterviewStatus>('idle')
  const messages = ref<InterviewMessage[]>([createWelcomeMessage()])
  const draft = ref('')
  const currentSessionId = ref(sessionId())

  const isVoiceMode = computed(() => mode.value === 'voice')
  const displayStatus = computed(() => {
    if (isVoiceMode.value && voiceStatus.value !== 'idle') {
      return voiceStatus.value
    }

    return status.value
  })
  const isBusy = computed(() => displayStatus.value !== 'idle')

  const setMode = (value: InterviewMode) => {
    mode.value = value
    if (value !== 'voice') {
      voiceStatus.value = 'idle'
    }
  }

  const setDraft = (value: string) => {
    draft.value = value
  }

  const toggleSpeech = () => {
    speechEnabled.value = !speechEnabled.value
  }

  const startListening = async () => {
    if (!isVoiceMode.value) {
      return
    }

    voiceStatus.value = 'listening'
    await new Promise((resolve) => setTimeout(resolve, 500))
    voiceStatus.value = 'transcribing'
  }

  const stopListening = () => {
    voiceStatus.value = 'idle'
  }

  const send = async (question?: string) => {
    const value = (question ?? draft.value).trim()
    if (!value || isBusy.value) {
      return
    }

    messages.value.push({
      id: crypto.randomUUID(),
      role: 'interviewer',
      content: value,
      sources: [],
      createdAt: new Date().toISOString(),
    })
    draft.value = ''
    status.value = 'retrieving'

    try {
      const payload = await sendInterviewMessage({
        sessionId: currentSessionId.value,
        message: value,
        history: messages.value.slice(0, -1).map((message) => ({
          role: message.role,
          content: message.content,
        })),
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

  const reset = () => {
    currentSessionId.value = sessionId()
    status.value = 'idle'
    voiceStatus.value = 'idle'
    messages.value = [createWelcomeMessage()]
    draft.value = ''
  }

  return {
    currentSessionId,
    displayStatus,
    draft,
    isBusy,
    isVoiceMode,
    messages,
    mode,
    reset,
    send,
    setDraft,
    setMode,
    speechEnabled,
    startListening,
    status,
    stopListening,
    toggleSpeech,
    voiceStatus,
  }
})
```

- [ ] **Step 4: Fix the assignment in the test so it mutates refs through store properties exactly as Pinia exposes them**

```ts
store.status = 'responding'
store.reset()
```

Expected test behavior after store rewrite:
- `store.status` is writable as the unwrapped Pinia property
- `store.messages` is the unwrapped message array

- [ ] **Step 5: Run the store test to verify the simplified store passes**

Run: `pnpm --filter frontend test -- --run frontend/src/store/interview/index.test.ts`
Expected: PASS and both store tests succeed

- [ ] **Step 6: Commit**

```bash
git add frontend/src/store/interview/index.ts frontend/src/store/interview/index.test.ts
git commit -m "refactor: remove interview side panel state"
```

### Task 3: Replace the page layout and remove TerminalStatusPanel

**Files:**
- Modify: `frontend/src/pages/interview/InterviewPage.vue:1-120`
- Delete: `frontend/src/pages/interview/components/TerminalStatusPanel.vue`

- [ ] **Step 1: Write the failing page target by defining the post-change layout contract**

```vue
<TerminalChatPanel :messages="store.messages" :status="store.displayStatus" />
<TerminalInputPanel />
```

And there should be no `TerminalStatusPanel` import or usage.

- [ ] **Step 2: Run the frontend test command to verify the current page still depends on `TerminalStatusPanel`**

Run: `pnpm --filter frontend test -- --run`
Expected: FAIL or current assertions still reveal `TerminalStatusPanel` usage in the page and copy test

- [ ] **Step 3: Replace `frontend/src/pages/interview/InterviewPage.vue` with the single-column composition**

```vue
<template>
  <div class="interview-page-shell">
    <section class="interview-page-grid">
      <TerminalHero />
      <TerminalModeToggle
        :mode="store.mode"
        :speech-enabled="store.speechEnabled"
        @toggle-mode="store.setMode"
        @toggle-speech="store.toggleSpeech"
      />
      <TerminalChatPanel :messages="store.messages" :status="store.displayStatus" />
      <TerminalInputPanel
        v-model="store.draft"
        :busy="store.isBusy"
        :mode="store.mode"
        @send="store.send"
        @listen="store.startListening"
        @stop-listening="store.stopListening"
        @reset="store.reset"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { useInterviewStore } from '../../store/interview'
import TerminalChatPanel from './components/TerminalChatPanel.vue'
import TerminalHero from './components/TerminalHero.vue'
import TerminalInputPanel from './components/TerminalInputPanel.vue'
import TerminalModeToggle from './components/TerminalModeToggle.vue'

const store = useInterviewStore()
</script>
```

- [ ] **Step 4: Delete the obsolete status panel file**

Delete: `frontend/src/pages/interview/components/TerminalStatusPanel.vue`

- [ ] **Step 5: Run the frontend test command to verify only citation rendering and copy assertions remain to be fixed**

Run: `pnpm --filter frontend test -- --run`
Expected: FAIL only in tests/components that still reference deleted side-panel copy or old citation fields

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/interview/InterviewPage.vue frontend/src/pages/interview/components/TerminalStatusPanel.vue
git commit -m "refactor: remove interview status side panel"
```

### Task 4: Add inline citation rendering to TerminalChatPanel with component tests

**Files:**
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.vue:1-220`
- Create: `frontend/src/pages/interview/components/TerminalChatPanel.test.ts`

- [ ] **Step 1: Create the failing component test in `frontend/src/pages/interview/components/TerminalChatPanel.test.ts`**

```ts
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import TerminalChatPanel from './TerminalChatPanel.vue'

const assistantMessage = {
  id: 'assistant-1',
  role: 'assistant' as const,
  content: '这是带引用的回答。',
  sources: [
    {
      title: 'projects.md',
      url: '/knowledge/projects.md',
      snippet: 'AI 面试分身项目重点是让回答基于真实资料，而不是通用大模型自由发挥。',
      kind: 'projects',
    },
  ],
  createdAt: '2026-05-21T00:00:00.000Z',
}

const interviewerMessage = {
  id: 'user-1',
  role: 'interviewer' as const,
  content: '请介绍一下这个项目。',
  sources: [
    {
      title: 'should-not-render',
      url: '/ignore',
      snippet: 'ignore',
      kind: 'test',
    },
  ],
  createdAt: '2026-05-21T00:00:00.000Z',
}

describe('TerminalChatPanel', () => {
  it('renders inline citations for assistant messages', () => {
    const wrapper = mount(TerminalChatPanel, {
      props: {
        messages: [assistantMessage],
        status: 'idle',
      },
    })

    expect(wrapper.text()).toContain('引用来源')
    expect(wrapper.text()).toContain('projects.md')
    expect(wrapper.text()).toContain('AI 面试分身项目重点是让回答基于真实资料')
    expect(wrapper.get('a').attributes('href')).toBe('/knowledge/projects.md')
  })

  it('does not render citations for interviewer messages', () => {
    const wrapper = mount(TerminalChatPanel, {
      props: {
        messages: [interviewerMessage],
        status: 'idle',
      },
    })

    expect(wrapper.text()).not.toContain('引用来源')
    expect(wrapper.find('a').exists()).toBe(false)
  })
})
```

- [ ] **Step 2: Run the component test to verify it fails before citation rendering is added**

Run: `pnpm --filter frontend test -- --run frontend/src/pages/interview/components/TerminalChatPanel.test.ts`
Expected: FAIL because the current component still expects `source.label`-style tags and has no inline citation section

- [ ] **Step 3: Replace `frontend/src/pages/interview/components/TerminalChatPanel.vue` so citations render beneath assistant messages**

```vue
<template>
  <section class="chat-panel">
    <header class="chat-panel-header">
      <span class="chat-panel-title">INTERVIEW_STREAM</span>
      <span class="chat-panel-status">{{ statusText }}</span>
    </header>

    <div class="chat-panel-body">
      <article
        v-for="message in messages"
        :key="message.id"
        class="chat-message"
        :class="message.role === 'assistant' ? 'chat-message-assistant' : 'chat-message-interviewer'"
      >
        <div class="chat-message-meta">
          <span>{{ message.role === 'assistant' ? 'AI_INTERVIEW_TWIN' : 'INTERVIEWER' }}</span>
          <span>{{ formatTime(message.createdAt) }}</span>
        </div>

        <div class="chat-message-content">
          {{ message.content }}
        </div>

        <section
          v-if="message.role === 'assistant' && message.sources.length"
          class="chat-citations"
        >
          <h3 class="chat-citations-title">引用来源</h3>
          <ul class="chat-citations-list">
            <li
              v-for="source in message.sources"
              :key="`${source.kind}-${source.title}-${source.url}`"
              class="chat-citation-item"
            >
              <p class="chat-citation-title">{{ source.title }}</p>
              <a
                class="chat-citation-link"
                :href="source.url"
                target="_blank"
                rel="noreferrer noopener"
              >
                {{ source.url }}
              </a>
              <p class="chat-citation-snippet">{{ source.snippet }}</p>
            </li>
          </ul>
        </section>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { InterviewMessage, InterviewStatus } from '../../../store/interview/types'

const props = defineProps<{
  messages: InterviewMessage[]
  status: InterviewStatus
}>()

const statusTextMap: Record<InterviewStatus, string> = {
  idle: '空闲',
  listening: '监听中',
  transcribing: '识别中',
  retrieving: '检索中',
  thinking: '思考中',
  responding: '输出中',
}

const statusText = computed(() => statusTextMap[props.status])

const formatTime = (value: string) =>
  new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
</script>
```

- [ ] **Step 4: Add the citation styles to `frontend/src/pages/interview/components/TerminalChatPanel.vue`**

```css
.chat-citations {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(189, 200, 206, 0.25);
}

.chat-citations-title {
  margin: 0 0 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.08em;
  color: #3e484d;
}

.chat-citations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.chat-citation-item {
  padding: 12px;
  border: 1px solid rgba(189, 200, 206, 0.3);
  border-radius: 12px;
  background: rgba(239, 244, 255, 0.55);
}

.chat-citation-title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: #0b1c30;
}

.chat-citation-link {
  display: inline-block;
  margin-top: 8px;
  font-size: 12px;
  color: #00647c;
  word-break: break-all;
}

.chat-citation-snippet {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: #3e484d;
}
```

- [ ] **Step 5: Run the component test to verify citation rendering passes**

Run: `pnpm --filter frontend test -- --run frontend/src/pages/interview/components/TerminalChatPanel.test.ts`
Expected: PASS and both component tests succeed

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/interview/components/TerminalChatPanel.vue frontend/src/pages/interview/components/TerminalChatPanel.test.ts
git commit -m "feat: render interview citations inline"
```

### Task 5: Update UI copy regression coverage and run full frontend verification

**Files:**
- Modify: `frontend/src/ui-copy.test.ts:1-80`

- [ ] **Step 1: Replace the obsolete side-panel copy assertions in `frontend/src/ui-copy.test.ts`**

```ts
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(__dirname)

const read = (relativePath: string) =>
  readFileSync(resolve(root, relativePath), 'utf-8')

describe('interview ui copy', () => {
  it('keeps the core interview landing copy', () => {
    const page = read('pages/interview/InterviewPage.vue')
    expect(page).toContain('interview-page-shell')
  })

  it('keeps the chat stream labels and inline citation copy', () => {
    const chatPanel = read('pages/interview/components/TerminalChatPanel.vue')
    expect(chatPanel).toContain('INTERVIEW_STREAM')
    expect(chatPanel).toContain('AI_INTERVIEW_TWIN')
    expect(chatPanel).toContain('引用来源')
  })

  it('keeps the hero and input guidance copy', () => {
    const hero = read('pages/interview/components/TerminalHero.vue')
    const input = read('pages/interview/components/TerminalInputPanel.vue')

    expect(hero).toContain('Talk to my AI interview twin')
    expect(input).toContain('开始新一轮')
  })
})
```

- [ ] **Step 2: Run the full frontend test suite to verify all assertions now match the new page shape**

Run: `pnpm --filter frontend test -- --run`
Expected: PASS and the copy test plus new store/component tests all succeed

- [ ] **Step 3: Run the frontend production build to verify the page compiles after removing the side panel**

Run: `pnpm --filter frontend build`
Expected: PASS and Vite emits a production bundle without unresolved imports

- [ ] **Step 4: Start the frontend dev server for manual verification**

Run: `pnpm --filter frontend dev`
Expected: PASS and Vite serves the interview page locally

- [ ] **Step 5: Verify the UI manually in a browser**

Manual verification:
- Open `/`
- Confirm there is no right-side `TerminalStatusPanel`
- Send a question and confirm the assistant reply renders in the message list
- Confirm the assistant reply shows an inline `引用来源` section
- Confirm each citation item shows title, clickable URL, and snippet text
- Switch text / voice modes and confirm citations remain attached to the correct assistant message
- Trigger `开始新一轮` and confirm the page resets to the single welcome message

- [ ] **Step 6: Commit**

```bash
git add frontend/src/ui-copy.test.ts
git commit -m "test: cover inline interview citations"
```

---

## Self-Review

- Spec coverage check:
  - 删除右侧 `TerminalStatusPanel` 组件及页面引用：Task 3
  - 调整聊天页布局为单列主聊天区：Task 3
  - 精简 interview store，删除 `topic` / `activeSources`：Task 2
  - 升级前端消息类型与 API 契约：Task 1
  - assistant 消息下方渲染引用区：Task 4
  - 同步更新 mock / fallback 数据为完整 citation 对象：Task 1
  - 前端测试覆盖引用渲染、无引用隐藏、重置与发送流程：Task 2, Task 4, Task 5
  - 页面手工验证引用、模式切换、重置行为：Task 5
- Placeholder scan: every task includes exact files, code snippets, commands, and expected outcomes; no TBD/TODO placeholders remain.
- Type consistency check:
  - `MessageCitation` is defined once in Task 1 and used consistently in Tasks 2 and 4
  - API response shape is consistently `reply: InterviewMessage` after Task 1
  - `TerminalChatPanel` citation rendering uses `title`, `url`, `snippet`, `kind` consistently with the updated store and tests
