# AI 面试分身单页 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个支持文字 / 语音双模切换的 AI 面试分身单页，围绕候选人的真实资料完成面试式问答，并通过分层记忆与检索增强保持长对话一致性。

**Architecture:** 前端保留一个 Vue 单页作为唯一入口，负责聊天展示、模式切换与状态反馈。后端在现有 FastAPI 基础上新增 interview pipeline，把 persona、retrieval、recent turns、session summary、selective memory write-back 组织成一条受控问答链路；语音模式与文字模式共用同一套会话与回答系统。

**Tech Stack:** pnpm Workspaces, Vue 3, Vue Router, TypeScript, Tailwind CSS, FastAPI, Pydantic, Poetry, Volcengine ASR/TTS integration, markdown-it, highlight.js, pytest

---

## File Structure

### Existing files to modify
- Modify: `README.md` — 保持项目定位与启动说明和当前产品一致
- Modify: `frontend/src/router/index.ts` — 从多页面路由收敛为单页 interview 入口
- Modify: `frontend/src/App.vue` — 保持根 RouterView，不再承载多页面壳逻辑
- Modify: `backend/app/main.py` — 注册新的 interview API 路由
- Modify: `backend/app/api/__init__.py` — 导出 interview 路由
- Modify: `backend/app/core/config.py` — 增加 interview 所需配置项

### Frontend files to create
- Create: `frontend/src/pages/interview/InterviewPage.vue` — 单页聊天主界面
- Create: `frontend/src/components/chat/InterviewHeader.vue` — 标题、说明、模式切换容器
- Create: `frontend/src/components/chat/ModeSwitch.vue` — 文字 / 语音模式切换控件
- Create: `frontend/src/components/chat/MessageList.vue` — 聊天消息列表
- Create: `frontend/src/components/chat/MessageBubble.vue` — 单条消息气泡，支持 markdown
- Create: `frontend/src/components/chat/ComposerBar.vue` — 输入框、发送、清空入口
- Create: `frontend/src/components/chat/StatusPanel.vue` — 当前状态、主题、命中标签展示
- Create: `frontend/src/components/chat/VoiceControls.vue` — 麦克风、播报开关、语音状态
- Create: `frontend/src/composables/useInterviewSession.ts` — 统一管理消息、发送状态、清空会话
- Create: `frontend/src/composables/useVoiceMode.ts` — 统一管理语音模式本地状态
- Create: `frontend/src/services/chat.ts` — 前端请求后端 interview API
- Create: `frontend/src/types/interview.ts` — 前端消息、状态、来源标签类型

### Backend files to create
- Create: `backend/app/api/interview.py` — 面试聊天接口
- Create: `backend/app/schemas/interview.py` — 聊天请求与响应模型
- Create: `backend/app/services/persona.py` — persona prompt 组装
- Create: `backend/app/services/retrieval.py` — 基础检索服务
- Create: `backend/app/services/memory.py` — recent turns buffer 存取
- Create: `backend/app/services/memory_summary.py` — session summary 生成与读取
- Create: `backend/app/services/memory_writeback.py` — 高价值回答筛选与沉淀
- Create: `backend/app/services/knowledge_loader.py` — 载入 `knowledge/` 中的资料
- Create: `backend/app/services/answer_pipeline.py` — 串联 persona / retrieval / memory / generation
- Create: `backend/tests/test_interview_api.py` — API 行为测试
- Create: `backend/tests/test_persona.py` — persona 约束测试
- Create: `backend/tests/test_retrieval.py` — retrieval 测试
- Create: `backend/tests/test_memory_layers.py` — recent turns / summary / write-back 测试

### Knowledge and voice integration files
- Create: `knowledge/resume.md` — 简历资料样例
- Create: `knowledge/projects.md` — 项目资料样例
- Create: `knowledge/notes.md` — 技术笔记样例
- Create: `knowledge/interview_qa.md` — 面试问答样例
- Create: `services/voice/README.md` — 记录现有火山语音项目的接入边界与后续迁移方式

---

### Task 1: 收敛前端路由为单页 interview 入口

**Files:**
- Modify: `frontend/src/router/index.ts`
- Create: `frontend/src/pages/interview/InterviewPage.vue`

- [ ] **Step 1: Write the failing route test by defining the expected route shape in the browser entry file**

```ts
// expected route shape after this task
[
  {
    path: '/',
    name: 'interview',
    component: InterviewPage
  }
]
```

- [ ] **Step 2: Run the frontend app boot command to verify the new page does not exist yet**

Run: `pnpm --filter web dev`
Expected: FAIL or compile error after route import is added because `frontend/src/pages/interview/InterviewPage.vue` does not exist yet

- [ ] **Step 3: Replace `frontend/src/router/index.ts` with a single-route configuration**

```ts
import { createRouter, createWebHistory } from 'vue-router'
import InterviewPage from '../pages/interview/InterviewPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'interview',
      component: InterviewPage
    }
  ]
})

export default router
```

- [ ] **Step 4: Create a minimal `frontend/src/pages/interview/InterviewPage.vue` component**

```vue
<template>
  <main class="min-h-screen bg-slate-950 text-slate-100">
    <section class="mx-auto flex min-h-screen max-w-6xl items-center justify-center px-6 py-12">
      <div class="rounded-3xl border border-white/10 bg-white/5 p-10 shadow-soft backdrop-blur">
        <h1 class="text-3xl font-semibold">AI Interview Twin</h1>
        <p class="mt-3 max-w-xl text-sm text-slate-300">
          A single-page interview chat that will support text and voice conversations.
        </p>
      </div>
    </section>
  </main>
</template>
```

- [ ] **Step 5: Run the frontend app to verify the single interview page renders**

Run: `pnpm --filter web dev`
Expected: PASS and the dev server serves `/` with the `AI Interview Twin` heading

- [ ] **Step 6: Commit**

```bash
git add frontend/src/router/index.ts frontend/src/pages/interview/InterviewPage.vue
git commit -m "feat: route app to interview landing page"
```

### Task 2: Build the chat page shell and interaction types

**Files:**
- Create: `frontend/src/types/interview.ts`
- Create: `frontend/src/components/chat/InterviewHeader.vue`
- Create: `frontend/src/components/chat/ModeSwitch.vue`
- Create: `frontend/src/components/chat/StatusPanel.vue`
- Create: `frontend/src/components/chat/ComposerBar.vue`
- Modify: `frontend/src/pages/interview/InterviewPage.vue`

- [ ] **Step 1: Write the failing type definitions that the page will need**

```ts
export type InterviewMode = 'text' | 'voice'
export type InterviewStatus = 'idle' | 'listening' | 'transcribing' | 'retrieving' | 'thinking' | 'responding'

export interface SourceTag {
  label: string
  kind: 'resume' | 'project' | 'note' | 'memory'
}

export interface InterviewMessage {
  id: string
  role: 'interviewer' | 'assistant'
  content: string
  sources: SourceTag[]
}
```

- [ ] **Step 2: Create `frontend/src/types/interview.ts`**

```ts
export type InterviewMode = 'text' | 'voice'
export type InterviewStatus = 'idle' | 'listening' | 'transcribing' | 'retrieving' | 'thinking' | 'responding'

export interface SourceTag {
  label: string
  kind: 'resume' | 'project' | 'note' | 'memory'
}

export interface InterviewMessage {
  id: string
  role: 'interviewer' | 'assistant'
  content: string
  sources: SourceTag[]
}
```

- [ ] **Step 3: Create `frontend/src/components/chat/ModeSwitch.vue`**

```vue
<script setup lang="ts">
import type { InterviewMode } from '../../types/interview'

defineProps<{
  modelValue: InterviewMode
}>()

const emit = defineEmits<{
  'update:modelValue': [InterviewMode]
}>()

const options: InterviewMode[] = ['text', 'voice']
</script>

<template>
  <div class="inline-flex rounded-full border border-white/10 bg-white/5 p-1">
    <button
      v-for="option in options"
      :key="option"
      class="rounded-full px-4 py-2 text-sm capitalize transition"
      :class="modelValue === option ? 'bg-violet-500 text-white' : 'text-slate-300 hover:text-white'"
      @click="emit('update:modelValue', option)"
    >
      {{ option }}
    </button>
  </div>
</template>
```

- [ ] **Step 4: Create `frontend/src/components/chat/InterviewHeader.vue`**

```vue
<script setup lang="ts">
import ModeSwitch from './ModeSwitch.vue'
import type { InterviewMode } from '../../types/interview'

defineProps<{
  mode: InterviewMode
}>()

const emit = defineEmits<{
  'update:mode': [InterviewMode]
}>()
</script>

<template>
  <header class="flex flex-col gap-4 rounded-3xl border border-white/10 bg-white/5 p-6 shadow-soft backdrop-blur md:flex-row md:items-center md:justify-between">
    <div>
      <p class="text-xs uppercase tracking-[0.3em] text-violet-300">AI Interview Twin</p>
      <h1 class="mt-2 text-3xl font-semibold text-white">Talk to my digital interview self</h1>
      <p class="mt-2 max-w-2xl text-sm text-slate-300">
        Ask about projects, trade-offs, technical depth, and delivery decisions through text or voice.
      </p>
    </div>
    <ModeSwitch :model-value="mode" @update:model-value="emit('update:mode', $event)" />
  </header>
</template>
```

- [ ] **Step 5: Create `frontend/src/components/chat/StatusPanel.vue`**

```vue
<script setup lang="ts">
import type { InterviewStatus, SourceTag } from '../../types/interview'

defineProps<{
  status: InterviewStatus
  topic: string
  activeSources: SourceTag[]
}>()
</script>

<template>
  <aside class="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-soft backdrop-blur">
    <p class="text-xs uppercase tracking-[0.3em] text-slate-400">Session status</p>
    <div class="mt-4 space-y-4 text-sm text-slate-200">
      <div>
        <p class="text-slate-400">Current state</p>
        <p class="mt-1 font-medium capitalize text-white">{{ status }}</p>
      </div>
      <div>
        <p class="text-slate-400">Current topic</p>
        <p class="mt-1 text-white">{{ topic }}</p>
      </div>
      <div>
        <p class="text-slate-400">Active sources</p>
        <div class="mt-2 flex flex-wrap gap-2">
          <span
            v-for="source in activeSources"
            :key="`${source.kind}-${source.label}`"
            class="rounded-full border border-violet-400/30 bg-violet-500/10 px-3 py-1 text-xs text-violet-200"
          >
            {{ source.label }}
          </span>
        </div>
      </div>
    </div>
  </aside>
</template>
```

- [ ] **Step 6: Create `frontend/src/components/chat/ComposerBar.vue`**

```vue
<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  disabled: boolean
}>()

const emit = defineEmits<{
  submit: [string]
  clear: []
}>()

const draft = ref('')

const handleSubmit = () => {
  const value = draft.value.trim()
  if (!value || props.disabled) {
    return
  }

  emit('submit', value)
  draft.value = ''
}

watch(
  () => props.disabled,
  (disabled) => {
    if (disabled) {
      draft.value = draft.value.trimStart()
    }
  }
)
</script>

<template>
  <div class="rounded-3xl border border-white/10 bg-white/5 p-4 shadow-soft backdrop-blur">
    <label class="sr-only" for="interview-input">Interview question</label>
    <textarea
      id="interview-input"
      v-model="draft"
      rows="4"
      class="w-full resize-none rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-slate-100 outline-none placeholder:text-slate-500"
      placeholder="Ask about projects, architecture choices, AI memory design, or delivery trade-offs..."
      :disabled="disabled"
    />
    <div class="mt-4 flex items-center justify-between gap-3">
      <button
        class="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:text-white"
        type="button"
        @click="emit('clear')"
      >
        New interview
      </button>
      <button
        class="rounded-full bg-violet-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-violet-400 disabled:cursor-not-allowed disabled:bg-violet-500/40"
        type="button"
        :disabled="disabled"
        @click="handleSubmit"
      >
        Send question
      </button>
    </div>
  </div>
</template>
```

- [ ] **Step 7: Replace `frontend/src/pages/interview/InterviewPage.vue` with the shell composition**

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'
import ComposerBar from '../../components/chat/ComposerBar.vue'
import InterviewHeader from '../../components/chat/InterviewHeader.vue'
import StatusPanel from '../../components/chat/StatusPanel.vue'
import type { InterviewMode, InterviewStatus, SourceTag } from '../../types/interview'

const mode = ref<InterviewMode>('text')
const status = ref<InterviewStatus>('idle')
const topic = ref('Introduce yourself and ask about one highlighted project.')
const activeSources = ref<SourceTag[]>([
  { label: 'resume', kind: 'resume' },
  { label: 'memory-summary', kind: 'memory' }
])
const messages = ref([
  {
    id: 'welcome',
    role: 'assistant' as const,
    content:
      'Hi, I am the interview twin. Ask me about project delivery, architecture trade-offs, AI memory design, or technical depth.',
    sources: []
  }
])

const isBusy = computed(() => status.value !== 'idle')

const handleSubmit = (question: string) => {
  messages.value.push({
    id: crypto.randomUUID(),
    role: 'interviewer',
    content: question,
    sources: []
  })
  status.value = 'thinking'
}

const handleClear = () => {
  messages.value = [messages.value[0]]
  status.value = 'idle'
  topic.value = 'Introduce yourself and ask about one highlighted project.'
}
</script>

<template>
  <main class="min-h-screen bg-slate-950 text-slate-100">
    <section class="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-6 py-8">
      <InterviewHeader :mode="mode" @update:mode="mode = $event" />
      <div class="grid flex-1 gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div class="space-y-6">
          <section class="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-soft backdrop-blur">
            <div class="space-y-4">
              <article
                v-for="message in messages"
                :key="message.id"
                class="rounded-2xl border border-white/10 px-5 py-4"
              >
                <p class="text-xs uppercase tracking-[0.3em] text-slate-400">
                  {{ message.role === 'assistant' ? 'Interview twin' : 'Interviewer' }}
                </p>
                <p class="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-100">
                  {{ message.content }}
                </p>
              </article>
            </div>
          </section>
          <ComposerBar :disabled="isBusy" @submit="handleSubmit" @clear="handleClear" />
        </div>
        <StatusPanel :status="status" :topic="topic" :active-sources="activeSources" />
      </div>
    </section>
  </main>
</template>
```

- [ ] **Step 8: Run the frontend build to verify the chat shell compiles**

Run: `pnpm --filter web build`
Expected: PASS and Vite emits a production bundle without type errors

- [ ] **Step 9: Commit**

```bash
git add frontend/src/types/interview.ts frontend/src/components/chat/InterviewHeader.vue frontend/src/components/chat/ModeSwitch.vue frontend/src/components/chat/StatusPanel.vue frontend/src/components/chat/ComposerBar.vue frontend/src/pages/interview/InterviewPage.vue
git commit -m "feat: add interview chat page shell"
```

### Task 3: Add message rendering, markdown support, and session composable

**Files:**
- Create: `frontend/src/components/chat/MessageBubble.vue`
- Create: `frontend/src/components/chat/MessageList.vue`
- Create: `frontend/src/composables/useInterviewSession.ts`
- Create: `frontend/src/services/chat.ts`
- Modify: `frontend/package.json`
- Modify: `frontend/src/pages/interview/InterviewPage.vue`

- [ ] **Step 1: Add the frontend dependencies required for markdown rendering**

```json
{
  "dependencies": {
    "highlight.js": "^11.11.1",
    "markdown-it": "^14.1.0",
    "vue": "^3.5.13",
    "vue-router": "^4.5.1"
  }
}
```

- [ ] **Step 2: Update `frontend/package.json` dependencies**

```json
{
  "name": "web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "highlight.js": "^11.11.1",
    "markdown-it": "^14.1.0",
    "vue": "^3.5.13",
    "vue-router": "^4.5.1"
  },
  "devDependencies": {
    "@types/node": "^22.15.21",
    "@vitejs/plugin-vue": "^5.2.4",
    "autoprefixer": "^10.4.21",
    "postcss": "^8.5.3",
    "tailwindcss": "^3.4.17",
    "typescript": "^5.8.3",
    "vite": "^5.4.19",
    "vue-tsc": "^2.2.10"
  }
}
```

- [ ] **Step 3: Install dependencies**

Run: `pnpm install`
Expected: PASS and lockfile updates with `markdown-it` and `highlight.js`

- [ ] **Step 4: Create `frontend/src/services/chat.ts` with the API contract**

```ts
import type { InterviewMessage } from '../types/interview'

export interface ChatRequest {
  sessionId: string
  message: string
}

export interface ChatResponse {
  reply: InterviewMessage
  topic: string
}

export const sendInterviewMessage = async ({ sessionId, message }: ChatRequest): Promise<ChatResponse> => {
  const response = await fetch('/api/interview/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ session_id: sessionId, message })
  })

  if (!response.ok) {
    throw new Error('Interview chat request failed')
  }

  return response.json() as Promise<ChatResponse>
}
```

- [ ] **Step 5: Create `frontend/src/composables/useInterviewSession.ts`**

```ts
import { ref } from 'vue'
import { sendInterviewMessage } from '../services/chat'
import type { InterviewMessage, InterviewStatus, SourceTag } from '../types/interview'

const createWelcomeMessage = (): InterviewMessage => ({
  id: 'welcome',
  role: 'assistant',
  content:
    'Hi, I am the interview twin. Ask me about project delivery, architecture trade-offs, AI memory design, or technical depth.',
  sources: []
})

export const useInterviewSession = () => {
  const sessionId = ref(crypto.randomUUID())
  const status = ref<InterviewStatus>('idle')
  const topic = ref('Introduce yourself and ask about one highlighted project.')
  const activeSources = ref<SourceTag[]>([])
  const messages = ref<InterviewMessage[]>([createWelcomeMessage()])

  const send = async (question: string) => {
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'interviewer',
      content: question,
      sources: []
    })

    status.value = 'retrieving'

    try {
      const result = await sendInterviewMessage({
        sessionId: sessionId.value,
        message: question
      })

      messages.value.push(result.reply)
      topic.value = result.topic
      activeSources.value = result.reply.sources
      status.value = 'idle'
    } catch (error) {
      status.value = 'idle'
      messages.value.push({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'The interview twin could not answer just now. Please try again.',
        sources: []
      })
      throw error
    }
  }

  const reset = () => {
    sessionId.value = crypto.randomUUID()
    status.value = 'idle'
    topic.value = 'Introduce yourself and ask about one highlighted project.'
    activeSources.value = []
    messages.value = [createWelcomeMessage()]
  }

  return {
    activeSources,
    messages,
    reset,
    send,
    sessionId,
    status,
    topic
  }
}
```

- [ ] **Step 6: Create `frontend/src/components/chat/MessageBubble.vue`**

```vue
<script setup lang="ts">
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import { computed } from 'vue'
import type { InterviewMessage } from '../../types/interview'

const props = defineProps<{
  message: InterviewMessage
}>()

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  highlight(code, language) {
    if (language && hljs.getLanguage(language)) {
      return `<pre class="hljs rounded-2xl bg-slate-950/80 p-4"><code>${hljs.highlight(code, { language }).value}</code></pre>`
    }

    return `<pre class="hljs rounded-2xl bg-slate-950/80 p-4"><code>${markdown.utils.escapeHtml(code)}</code></pre>`
  }
})

const renderedContent = computed(() => markdown.render(props.message.content))
const isAssistant = computed(() => props.message.role === 'assistant')
</script>

<template>
  <article
    class="rounded-2xl border px-5 py-4"
    :class="isAssistant ? 'border-violet-400/20 bg-violet-500/10' : 'border-white/10 bg-slate-950/50'"
  >
    <p class="text-xs uppercase tracking-[0.3em] text-slate-400">
      {{ isAssistant ? 'Interview twin' : 'Interviewer' }}
    </p>
    <div class="prose prose-invert mt-3 max-w-none text-sm leading-7" v-html="renderedContent" />
    <div v-if="message.sources.length" class="mt-4 flex flex-wrap gap-2">
      <span
        v-for="source in message.sources"
        :key="`${source.kind}-${source.label}`"
        class="rounded-full border border-violet-400/30 bg-violet-500/10 px-3 py-1 text-xs text-violet-200"
      >
        {{ source.label }}
      </span>
    </div>
  </article>
</template>
```

- [ ] **Step 7: Create `frontend/src/components/chat/MessageList.vue`**

```vue
<script setup lang="ts">
import MessageBubble from './MessageBubble.vue'
import type { InterviewMessage } from '../../types/interview'

defineProps<{
  messages: InterviewMessage[]
}>()
</script>

<template>
  <section class="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-soft backdrop-blur">
    <div class="space-y-4">
      <MessageBubble v-for="message in messages" :key="message.id" :message="message" />
    </div>
  </section>
</template>
```

- [ ] **Step 8: Replace `frontend/src/pages/interview/InterviewPage.vue` to use the composable and message list**

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'
import ComposerBar from '../../components/chat/ComposerBar.vue'
import InterviewHeader from '../../components/chat/InterviewHeader.vue'
import MessageList from '../../components/chat/MessageList.vue'
import StatusPanel from '../../components/chat/StatusPanel.vue'
import { useInterviewSession } from '../../composables/useInterviewSession'
import type { InterviewMode } from '../../types/interview'

const mode = ref<InterviewMode>('text')
const { activeSources, messages, reset, send, status, topic } = useInterviewSession()

const isBusy = computed(() => status.value !== 'idle')

const handleSubmit = async (question: string) => {
  await send(question)
}
</script>

<template>
  <main class="min-h-screen bg-slate-950 text-slate-100">
    <section class="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-6 py-8">
      <InterviewHeader :mode="mode" @update:mode="mode = $event" />
      <div class="grid flex-1 gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div class="space-y-6">
          <MessageList :messages="messages" />
          <ComposerBar :disabled="isBusy" @submit="handleSubmit" @clear="reset" />
        </div>
        <StatusPanel :status="status" :topic="topic" :active-sources="activeSources" />
      </div>
    </section>
  </main>
</template>
```

- [ ] **Step 9: Run the frontend build to verify markdown and composables compile**

Run: `pnpm --filter web build`
Expected: PASS and the build completes after adding markdown-it and highlight.js

- [ ] **Step 10: Commit**

```bash
git add frontend/package.json pnpm-lock.yaml frontend/src/services/chat.ts frontend/src/composables/useInterviewSession.ts frontend/src/components/chat/MessageBubble.vue frontend/src/components/chat/MessageList.vue frontend/src/pages/interview/InterviewPage.vue
git commit -m "feat: add interview message rendering and session state"
```

### Task 4: Add voice-mode controls without changing the main chat pipeline

**Files:**
- Create: `frontend/src/components/chat/VoiceControls.vue`
- Create: `frontend/src/composables/useVoiceMode.ts`
- Modify: `frontend/src/pages/interview/InterviewPage.vue`

- [ ] **Step 1: Create `frontend/src/composables/useVoiceMode.ts`**

```ts
import { computed, ref } from 'vue'
import type { InterviewMode, InterviewStatus } from '../types/interview'

export const useVoiceMode = (mode: { value: InterviewMode }) => {
  const speechEnabled = ref(true)
  const localVoiceStatus = ref<InterviewStatus>('idle')

  const canUseVoice = computed(() => mode.value === 'voice')

  const startListening = () => {
    if (!canUseVoice.value) {
      return
    }

    localVoiceStatus.value = 'listening'
  }

  const stopListening = () => {
    localVoiceStatus.value = 'idle'
  }

  const setTranscribing = () => {
    localVoiceStatus.value = 'transcribing'
  }

  return {
    canUseVoice,
    localVoiceStatus,
    setTranscribing,
    speechEnabled,
    startListening,
    stopListening
  }
}
```

- [ ] **Step 2: Create `frontend/src/components/chat/VoiceControls.vue`**

```vue
<script setup lang="ts">
import type { InterviewStatus } from '../../types/interview'

defineProps<{
  enabled: boolean
  speechEnabled: boolean
  status: InterviewStatus
}>()

const emit = defineEmits<{
  toggleSpeech: []
  start: []
  stop: []
}>()
</script>

<template>
  <div class="rounded-3xl border border-white/10 bg-white/5 p-4 shadow-soft backdrop-blur">
    <div class="flex flex-wrap items-center gap-3">
      <button
        class="rounded-full bg-violet-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-violet-400 disabled:cursor-not-allowed disabled:bg-violet-500/40"
        type="button"
        :disabled="!enabled || status === 'listening'"
        @click="emit('start')"
      >
        Start voice
      </button>
      <button
        class="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:text-white"
        type="button"
        :disabled="!enabled || status === 'idle'"
        @click="emit('stop')"
      >
        Stop voice
      </button>
      <button
        class="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:text-white"
        type="button"
        @click="emit('toggleSpeech')"
      >
        {{ speechEnabled ? 'Disable voice reply' : 'Enable voice reply' }}
      </button>
    </div>
    <p class="mt-3 text-xs text-slate-400">
      Voice mode will connect to the existing Volcengine ASR / TTS project while reusing the same interview session state.
    </p>
  </div>
</template>
```

- [ ] **Step 3: Modify `frontend/src/pages/interview/InterviewPage.vue` to include voice controls**

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'
import ComposerBar from '../../components/chat/ComposerBar.vue'
import InterviewHeader from '../../components/chat/InterviewHeader.vue'
import MessageList from '../../components/chat/MessageList.vue'
import StatusPanel from '../../components/chat/StatusPanel.vue'
import VoiceControls from '../../components/chat/VoiceControls.vue'
import { useInterviewSession } from '../../composables/useInterviewSession'
import { useVoiceMode } from '../../composables/useVoiceMode'
import type { InterviewMode } from '../../types/interview'

const mode = ref<InterviewMode>('text')
const { activeSources, messages, reset, send, status, topic } = useInterviewSession()
const { canUseVoice, localVoiceStatus, speechEnabled, startListening, stopListening } = useVoiceMode(mode)

const displayStatus = computed(() => (mode.value === 'voice' && localVoiceStatus.value !== 'idle' ? localVoiceStatus.value : status.value))
const isBusy = computed(() => displayStatus.value !== 'idle')

const handleSubmit = async (question: string) => {
  await send(question)
}
</script>

<template>
  <main class="min-h-screen bg-slate-950 text-slate-100">
    <section class="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-6 py-8">
      <InterviewHeader :mode="mode" @update:mode="mode = $event" />
      <div class="grid flex-1 gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div class="space-y-6">
          <MessageList :messages="messages" />
          <VoiceControls
            :enabled="canUseVoice"
            :speech-enabled="speechEnabled"
            :status="localVoiceStatus"
            @start="startListening"
            @stop="stopListening"
            @toggle-speech="speechEnabled = !speechEnabled"
          />
          <ComposerBar :disabled="isBusy" @submit="handleSubmit" @clear="reset" />
        </div>
        <StatusPanel :status="displayStatus" :topic="topic" :active-sources="activeSources" />
      </div>
    </section>
  </main>
</template>
```

- [ ] **Step 4: Run the frontend build to verify voice controls compile**

Run: `pnpm --filter web build`
Expected: PASS and the page shows text / voice mode switching support at compile time

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/chat/VoiceControls.vue frontend/src/composables/useVoiceMode.ts frontend/src/pages/interview/InterviewPage.vue
git commit -m "feat: add voice mode controls to interview page"
```

### Task 5: Add backend interview schemas and a failing API test

**Files:**
- Create: `backend/app/schemas/interview.py`
- Create: `backend/app/api/interview.py`
- Create: `backend/tests/test_interview_api.py`
- Modify: `backend/app/api/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the failing API test in `backend/tests/test_interview_api.py`**

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_interview_chat_returns_reply_payload() -> None:
    response = client.post(
        "/api/interview/chat",
        json={"session_id": "session-1", "message": "Tell me about your strongest project."},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reply"]["role"] == "assistant"
    assert data["topic"]
```

- [ ] **Step 2: Run the backend API test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_interview_api.py -v`
Expected: FAIL with 404 or import error because the interview route does not exist yet

- [ ] **Step 3: Create `backend/app/schemas/interview.py`**

```python
from pydantic import BaseModel


class SourceTag(BaseModel):
    label: str
    kind: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatReply(BaseModel):
    id: str
    role: str
    content: str
    sources: list[SourceTag]


class ChatResponse(BaseModel):
    reply: ChatReply
    topic: str
```

- [ ] **Step 4: Create a temporary interview route in `backend/app/api/interview.py`**

```python
from uuid import uuid4

from fastapi import APIRouter

from app.schemas.interview import ChatReply, ChatRequest, ChatResponse, SourceTag

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(
        reply=ChatReply(
            id=str(uuid4()),
            role="assistant",
            content=f"Interview twin placeholder reply to: {request.message}",
            sources=[SourceTag(label="resume", kind="resume")],
        ),
        topic="project deep dive",
    )
```

- [ ] **Step 5: Update `backend/app/api/__init__.py` to export the new router**

```python
from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.interview import router as interview_router

router = APIRouter()
router.include_router(health_router)
router.include_router(interview_router)
```

- [ ] **Step 6: Confirm `backend/app/main.py` still mounts the API router at `/api`**

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

- [ ] **Step 7: Run the backend API test to verify it passes with the placeholder response**

Run: `cd backend && poetry run pytest tests/test_interview_api.py -v`
Expected: PASS and the POST `/api/interview/chat` test succeeds

- [ ] **Step 8: Commit**

```bash
git add backend/app/schemas/interview.py backend/app/api/interview.py backend/app/api/__init__.py backend/tests/test_interview_api.py
git commit -m "feat: add interview chat api scaffold"
```

### Task 6: Add persona and knowledge loading with tests

**Files:**
- Create: `knowledge/resume.md`
- Create: `knowledge/projects.md`
- Create: `knowledge/notes.md`
- Create: `knowledge/interview_qa.md`
- Create: `backend/app/services/knowledge_loader.py`
- Create: `backend/app/services/persona.py`
- Create: `backend/tests/test_persona.py`

- [ ] **Step 1: Write the failing tests in `backend/tests/test_persona.py`**

```python
from app.services.knowledge_loader import load_knowledge_documents
from app.services.persona import build_persona_prompt


def test_load_knowledge_documents_reads_markdown_sources() -> None:
    documents = load_knowledge_documents()

    assert len(documents) >= 4
    assert any(document["slug"] == "resume" for document in documents)


def test_build_persona_prompt_mentions_truthfulness_and_candidate_identity() -> None:
    prompt = build_persona_prompt()

    assert "electronic version of the candidate" in prompt
    assert "Do not invent experience" in prompt
```

- [ ] **Step 2: Run the persona tests to verify they fail**

Run: `cd backend && poetry run pytest tests/test_persona.py -v`
Expected: FAIL because the services and knowledge files do not exist yet

- [ ] **Step 3: Create the knowledge source files**

```md
# resume

- Candidate profile summary goes here.
- Replace this file with the real resume content before demo day.
```

```md
# projects

- Project highlight one.
- Project highlight two.
```

```md
# notes

- Technical notes and design reflections.
```

```md
# interview qa

- Common interview questions and refined answers.
```

- [ ] **Step 4: Create `backend/app/services/knowledge_loader.py`**

```python
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parents[4] / "knowledge"


def load_knowledge_documents() -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []

    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        documents.append(
            {
                "slug": path.stem,
                "content": path.read_text(encoding="utf-8").strip(),
            }
        )

    return documents
```

- [ ] **Step 5: Create `backend/app/services/persona.py`**

```python
from app.services.knowledge_loader import load_knowledge_documents


def build_persona_prompt() -> str:
    documents = load_knowledge_documents()
    available_sources = ", ".join(document["slug"] for document in documents)

    return (
        "You are the electronic version of the candidate. "
        "Answer as the candidate, prioritize real experience, and explain technical reasoning only when it stays grounded in the candidate materials. "
        "Do not invent experience, ownership, or delivery history. "
        f"Available sources: {available_sources}."
    )
```

- [ ] **Step 6: Run the persona tests to verify they pass**

Run: `cd backend && poetry run pytest tests/test_persona.py -v`
Expected: PASS and both tests succeed

- [ ] **Step 7: Commit**

```bash
git add knowledge/resume.md knowledge/projects.md knowledge/notes.md knowledge/interview_qa.md backend/app/services/knowledge_loader.py backend/app/services/persona.py backend/tests/test_persona.py
git commit -m "feat: add interview knowledge sources and persona prompt"
```

### Task 7: Add retrieval and layered memory services with tests

**Files:**
- Create: `backend/app/services/retrieval.py`
- Create: `backend/app/services/memory.py`
- Create: `backend/app/services/memory_summary.py`
- Create: `backend/app/services/memory_writeback.py`
- Create: `backend/tests/test_retrieval.py`
- Create: `backend/tests/test_memory_layers.py`

- [ ] **Step 1: Write the failing retrieval test in `backend/tests/test_retrieval.py`**

```python
from app.services.retrieval import retrieve_documents


def test_retrieve_documents_prioritizes_matching_sources() -> None:
    results = retrieve_documents("project highlight")

    assert results
    assert results[0]["slug"] == "projects"
```

- [ ] **Step 2: Write the failing memory-layer tests in `backend/tests/test_memory_layers.py`**

```python
from app.services.memory import InMemorySessionStore
from app.services.memory_summary import summarize_session_turns
from app.services.memory_writeback import should_write_memory_candidate


def test_session_store_keeps_recent_turns_only() -> None:
    store = InMemorySessionStore(max_turns=2)
    store.append("session-1", "interviewer", "q1")
    store.append("session-1", "assistant", "a1")
    store.append("session-1", "interviewer", "q2")

    turns = store.get_recent_turns("session-1")
    assert len(turns) == 2
    assert turns[0]["content"] == "a1"


def test_summarize_session_turns_mentions_latest_topic() -> None:
    summary = summarize_session_turns(
        [
            {"role": "interviewer", "content": "Tell me about your Redis usage."},
            {"role": "assistant", "content": "I used Redis for caching and queue coordination."},
        ]
    )

    assert "Redis" in summary


def test_should_write_memory_candidate_filters_short_replies() -> None:
    assert should_write_memory_candidate("short reply") is False
    assert should_write_memory_candidate("This answer explains a project trade-off in enough detail to be reusable later.") is True
```

- [ ] **Step 3: Run the retrieval and memory tests to verify they fail**

Run: `cd backend && poetry run pytest tests/test_retrieval.py tests/test_memory_layers.py -v`
Expected: FAIL because the retrieval and memory services do not exist yet

- [ ] **Step 4: Create `backend/app/services/retrieval.py`**

```python
from app.services.knowledge_loader import load_knowledge_documents


def retrieve_documents(query: str, limit: int = 3) -> list[dict[str, str]]:
    normalized_terms = [term.lower() for term in query.split() if term.strip()]
    scored_documents: list[tuple[int, dict[str, str]]] = []

    for document in load_knowledge_documents():
        haystack = f"{document['slug']} {document['content']}".lower()
        score = sum(1 for term in normalized_terms if term in haystack)
        if score:
            scored_documents.append((score, document))

    scored_documents.sort(key=lambda item: item[0], reverse=True)
    return [document for _, document in scored_documents[:limit]]
```

- [ ] **Step 5: Create `backend/app/services/memory.py`**

```python
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class Turn:
    role: str
    content: str


class InMemorySessionStore:
    def __init__(self, max_turns: int = 6) -> None:
        self.max_turns = max_turns
        self._store: dict[str, list[Turn]] = defaultdict(list)

    def append(self, session_id: str, role: str, content: str) -> None:
        self._store[session_id].append(Turn(role=role, content=content))
        self._store[session_id] = self._store[session_id][-self.max_turns :]

    def get_recent_turns(self, session_id: str) -> list[dict[str, str]]:
        return [turn.__dict__ for turn in self._store[session_id]]
```

- [ ] **Step 6: Create `backend/app/services/memory_summary.py`**

```python
def summarize_session_turns(turns: list[dict[str, str]]) -> str:
    if not turns:
        return "No active interview topic yet."

    latest_user_turn = next((turn for turn in reversed(turns) if turn["role"] == "interviewer"), turns[-1])
    latest_assistant_turn = next((turn for turn in reversed(turns) if turn["role"] == "assistant"), turns[-1])

    return (
        f"Current focus: {latest_user_turn['content']}\n"
        f"Latest answer summary: {latest_assistant_turn['content']}"
    )
```

- [ ] **Step 7: Create `backend/app/services/memory_writeback.py`**

```python
def should_write_memory_candidate(content: str) -> bool:
    return len(content.split()) >= 8
```

- [ ] **Step 8: Run the retrieval and memory tests to verify they pass**

Run: `cd backend && poetry run pytest tests/test_retrieval.py tests/test_memory_layers.py -v`
Expected: PASS and all memory-layer tests succeed

- [ ] **Step 9: Commit**

```bash
git add backend/app/services/retrieval.py backend/app/services/memory.py backend/app/services/memory_summary.py backend/app/services/memory_writeback.py backend/tests/test_retrieval.py backend/tests/test_memory_layers.py
git commit -m "feat: add retrieval and layered memory services"
```

### Task 8: Build the answer pipeline and connect it to the API

**Files:**
- Create: `backend/app/services/answer_pipeline.py`
- Modify: `backend/app/api/interview.py`
- Modify: `backend/tests/test_interview_api.py`

- [ ] **Step 1: Replace the API test with assertions for retrieved sources and topic updates**

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_interview_chat_returns_sources_and_topic() -> None:
    response = client.post(
        "/api/interview/chat",
        json={"session_id": "session-1", "message": "Tell me about a project highlight and the trade-offs."},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reply"]["role"] == "assistant"
    assert data["reply"]["sources"]
    assert data["topic"]
```

- [ ] **Step 2: Run the API test to verify it fails against the placeholder route**

Run: `cd backend && poetry run pytest tests/test_interview_api.py -v`
Expected: FAIL because the placeholder route does not produce pipeline-driven data

- [ ] **Step 3: Create `backend/app/services/answer_pipeline.py`**

```python
from uuid import uuid4

from app.schemas.interview import ChatReply, ChatResponse, SourceTag
from app.services.memory import InMemorySessionStore
from app.services.memory_summary import summarize_session_turns
from app.services.memory_writeback import should_write_memory_candidate
from app.services.persona import build_persona_prompt
from app.services.retrieval import retrieve_documents

SESSION_STORE = InMemorySessionStore(max_turns=6)
MEMORY_KNOWLEDGE: list[dict[str, str]] = []


def build_interview_response(session_id: str, message: str) -> ChatResponse:
    SESSION_STORE.append(session_id, "interviewer", message)
    recent_turns = SESSION_STORE.get_recent_turns(session_id)
    session_summary = summarize_session_turns(recent_turns)
    retrieved = retrieve_documents(message)
    persona = build_persona_prompt()

    source_tags = [SourceTag(label=document["slug"], kind="memory" if document["slug"].startswith("memory-") else document["slug"]) for document in retrieved]
    grounded_context = "\n\n".join(document["content"] for document in retrieved)
    reply_text = (
        "I will answer as the candidate based on the retrieved materials.\n\n"
        f"Persona: {persona}\n\n"
        f"Session summary: {session_summary}\n\n"
        f"Grounded context: {grounded_context}"
    )

    SESSION_STORE.append(session_id, "assistant", reply_text)

    if should_write_memory_candidate(reply_text):
        MEMORY_KNOWLEDGE.append(
            {
                "slug": f"memory-{len(MEMORY_KNOWLEDGE) + 1}",
                "content": reply_text,
            }
        )

    topic = retrieved[0]["slug"] if retrieved else "general interview"

    return ChatResponse(
        reply=ChatReply(
            id=str(uuid4()),
            role="assistant",
            content=reply_text,
            sources=source_tags,
        ),
        topic=topic,
    )
```

- [ ] **Step 4: Update `backend/app/api/interview.py` to call the pipeline**

```python
from fastapi import APIRouter

from app.schemas.interview import ChatRequest, ChatResponse
from app.services.answer_pipeline import build_interview_response

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return build_interview_response(request.session_id, request.message)
```

- [ ] **Step 5: Run the API test to verify the pipeline-backed route passes**

Run: `cd backend && poetry run pytest tests/test_interview_api.py -v`
Expected: PASS and the response includes a topic plus at least one source tag

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/answer_pipeline.py backend/app/api/interview.py backend/tests/test_interview_api.py
git commit -m "feat: connect interview api to answer pipeline"
```

### Task 9: Align the frontend request flow with the backend API and verify the app end to end

**Files:**
- Modify: `frontend/src/services/chat.ts`
- Modify: `frontend/src/types/interview.ts`
- Modify: `frontend/src/composables/useInterviewSession.ts`
- Modify: `frontend/src/pages/interview/InterviewPage.vue`

- [ ] **Step 1: Update the frontend types so they match the API payload exactly**

```ts
export type InterviewMode = 'text' | 'voice'
export type InterviewStatus = 'idle' | 'listening' | 'transcribing' | 'retrieving' | 'thinking' | 'responding'

export interface SourceTag {
  label: string
  kind: string
}

export interface InterviewMessage {
  id: string
  role: 'interviewer' | 'assistant'
  content: string
  sources: SourceTag[]
}
```

- [ ] **Step 2: Modify `frontend/src/types/interview.ts`**

```ts
export type InterviewMode = 'text' | 'voice'
export type InterviewStatus = 'idle' | 'listening' | 'transcribing' | 'retrieving' | 'thinking' | 'responding'

export interface SourceTag {
  label: string
  kind: string
}

export interface InterviewMessage {
  id: string
  role: 'interviewer' | 'assistant'
  content: string
  sources: SourceTag[]
}
```

- [ ] **Step 3: Modify `frontend/src/services/chat.ts` to return the exact API response type**

```ts
import type { InterviewMessage } from '../types/interview'

export interface ChatRequest {
  sessionId: string
  message: string
}

export interface ChatResponse {
  reply: InterviewMessage
  topic: string
}

export const sendInterviewMessage = async ({ sessionId, message }: ChatRequest): Promise<ChatResponse> => {
  const response = await fetch('/api/interview/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ session_id: sessionId, message })
  })

  if (!response.ok) {
    throw new Error('Interview chat request failed')
  }

  return response.json() as Promise<ChatResponse>
}
```

- [ ] **Step 4: Modify `frontend/src/composables/useInterviewSession.ts` so the UI reflects backend processing states**

```ts
import { ref } from 'vue'
import { sendInterviewMessage } from '../services/chat'
import type { InterviewMessage, InterviewStatus, SourceTag } from '../types/interview'

const createWelcomeMessage = (): InterviewMessage => ({
  id: 'welcome',
  role: 'assistant',
  content:
    'Hi, I am the interview twin. Ask me about project delivery, architecture trade-offs, AI memory design, or technical depth.',
  sources: []
})

export const useInterviewSession = () => {
  const sessionId = ref(crypto.randomUUID())
  const status = ref<InterviewStatus>('idle')
  const topic = ref('Introduce yourself and ask about one highlighted project.')
  const activeSources = ref<SourceTag[]>([])
  const messages = ref<InterviewMessage[]>([createWelcomeMessage()])

  const send = async (question: string) => {
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'interviewer',
      content: question,
      sources: []
    })

    status.value = 'retrieving'
    const result = await sendInterviewMessage({
      sessionId: sessionId.value,
      message: question
    })
    status.value = 'responding'

    messages.value.push(result.reply)
    topic.value = result.topic
    activeSources.value = result.reply.sources
    status.value = 'idle'
  }

  const reset = () => {
    sessionId.value = crypto.randomUUID()
    status.value = 'idle'
    topic.value = 'Introduce yourself and ask about one highlighted project.'
    activeSources.value = []
    messages.value = [createWelcomeMessage()]
  }

  return {
    activeSources,
    messages,
    reset,
    send,
    sessionId,
    status,
    topic
  }
}
```

- [ ] **Step 5: Keep `frontend/src/pages/interview/InterviewPage.vue` wired to the same composables and controls**

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'
import ComposerBar from '../../components/chat/ComposerBar.vue'
import InterviewHeader from '../../components/chat/InterviewHeader.vue'
import MessageList from '../../components/chat/MessageList.vue'
import StatusPanel from '../../components/chat/StatusPanel.vue'
import VoiceControls from '../../components/chat/VoiceControls.vue'
import { useInterviewSession } from '../../composables/useInterviewSession'
import { useVoiceMode } from '../../composables/useVoiceMode'
import type { InterviewMode } from '../../types/interview'

const mode = ref<InterviewMode>('text')
const { activeSources, messages, reset, send, status, topic } = useInterviewSession()
const { canUseVoice, localVoiceStatus, speechEnabled, startListening, stopListening } = useVoiceMode(mode)

const displayStatus = computed(() => (mode.value === 'voice' && localVoiceStatus.value !== 'idle' ? localVoiceStatus.value : status.value))
const isBusy = computed(() => displayStatus.value !== 'idle')

const handleSubmit = async (question: string) => {
  await send(question)
}
</script>

<template>
  <main class="min-h-screen bg-slate-950 text-slate-100">
    <section class="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-6 py-8">
      <InterviewHeader :mode="mode" @update:mode="mode = $event" />
      <div class="grid flex-1 gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div class="space-y-6">
          <MessageList :messages="messages" />
          <VoiceControls
            :enabled="canUseVoice"
            :speech-enabled="speechEnabled"
            :status="localVoiceStatus"
            @start="startListening"
            @stop="stopListening"
            @toggle-speech="speechEnabled = !speechEnabled"
          />
          <ComposerBar :disabled="isBusy" @submit="handleSubmit" @clear="reset" />
        </div>
        <StatusPanel :status="displayStatus" :topic="topic" :active-sources="activeSources" />
      </div>
    </section>
  </main>
</template>
```

- [ ] **Step 6: Run both backend tests and frontend build to verify the integrated text flow**

Run: `cd backend && poetry run pytest tests/test_interview_api.py tests/test_persona.py tests/test_retrieval.py tests/test_memory_layers.py -v && cd ../.. && pnpm --filter web build`
Expected: PASS and both the backend test suite and frontend production build succeed

- [ ] **Step 7: Start the frontend and backend, then verify the UI manually in a browser**

Run: `pnpm --filter web dev`
Expected: PASS and the interview page loads in the browser

Run: `cd backend && poetry run uvicorn app.main:app --reload`
Expected: PASS and the API serves on the configured port

Manual verification:
- Open `/`
- Ask a text question like `Tell me about a project highlight and the trade-offs.`
- Confirm the assistant answer appears in the message list
- Confirm the status panel updates topic and source tags
- Switch from text mode to voice mode and confirm the controls update without clearing the session

- [ ] **Step 8: Commit**

```bash
git add frontend/src/types/interview.ts frontend/src/services/chat.ts frontend/src/composables/useInterviewSession.ts frontend/src/pages/interview/InterviewPage.vue
git commit -m "feat: wire interview page to backend chat flow"
```

### Task 10: Document voice integration boundaries and final verification

**Files:**
- Create: `services/voice/README.md`
- Modify: `README.md`

- [ ] **Step 1: Write the failing check by listing the expected voice integration doc**

```text
services/voice/README.md
```

- [ ] **Step 2: Create `services/voice/README.md`**

```md
# Voice Integration Boundary

This directory is reserved for the existing Volcengine real-time ASR / TTS project.

## Responsibilities

- Capture microphone audio in voice mode
- Stream speech to Volcengine ASR
- Return the recognized text to the shared interview session pipeline
- Convert the assistant reply into speech with Volcengine TTS

## Boundary with `backend`

- `backend` owns persona, retrieval, recent turns, session summary, selective memory write-back, and answer generation
- `services/voice` owns audio transport and speech synthesis / recognition
- Both text and voice paths must share the same `session_id` and interview history
```

- [ ] **Step 3: Update `README.md` to include the voice boundary and knowledge files in the structure section**

```md
# AI Interview Twin

## Overview

This project is a single-page AI interview twin for portfolio and interview demos.
It lets interviewers chat with a digital version of the candidate through text or voice.

## Structure

- `frontend`: single-page Vue frontend for the interview chat experience
- `backend`: FastAPI backend for persona, retrieval, memory, and answer generation
- `services/voice`: voice integration layer adapted from the existing Volcengine ASR/TTS project
- `knowledge/`: candidate resume, project materials, notes, and interview Q&A sources
- `shared/*`: shared packages reserved for future reuse

## Commands

### Frontend

```bash
pnpm install
pnpm dev:web
```

### Backend

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```
```

- [ ] **Step 4: Run the final verification commands**

Run: `cd backend && poetry run pytest tests/test_interview_api.py tests/test_persona.py tests/test_retrieval.py tests/test_memory_layers.py -v && cd ../.. && pnpm --filter web build`
Expected: PASS and all backend tests plus the frontend build succeed

- [ ] **Step 5: Commit**

```bash
git add README.md services/voice/README.md
git commit -m "docs: capture voice integration boundary"
```

---

## Self-Review

- Spec coverage check:
  - 单页产品与路由收敛：Task 1, Task 2
  - 聊天区、状态区、模式切换、文字/语音共享：Task 2, Task 3, Task 4, Task 9
  - persona / retrieval / layered memory / selective write-back：Task 6, Task 7, Task 8
  - answer guardrail and interview pipeline shape：Task 6, Task 8
  - knowledge sources and voice boundary: Task 6, Task 10
  - manual UI verification: Task 9, Task 10
- Placeholder scan: no TBD/TODO placeholders remain in executable tasks
- Type consistency check:
  - Frontend `InterviewMessage`, `SourceTag`, `InterviewStatus` stay consistent across Task 2, Task 3, Task 4, Task 9
  - Backend `ChatRequest`, `ChatReply`, `ChatResponse` stay consistent across Task 5 and Task 8
  - Memory service names (`InMemorySessionStore`, `summarize_session_turns`, `should_write_memory_candidate`) stay consistent across Task 7 and Task 8
