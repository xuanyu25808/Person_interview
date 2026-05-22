# Interview Landing State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first-question landing state to the interview page that shows a centered welcome block and inline input before switching into the normal chat layout after the first submission.

**Architecture:** Keep the change localized to the existing interview page flow. Derive a landing/chat mode flag from store state, remove the seeded welcome message so the landing view owns the greeting copy, and reuse `TerminalBottomBar.vue` in two placements that are conditionally rendered based on whether the conversation has started.

**Tech Stack:** Vue 3, Pinia, TypeScript, Vitest, Vue Test Utils

---

## File map

- Modify: `frontend/src/store/interview/index.ts` — remove the seeded welcome message and expose a derived `hasStarted` flag based on real user/assistant messages.
- Modify: `frontend/src/pages/interview/InterviewPage.vue` — add the landing layout, switch between center input and bottom input, and add lightweight transition-aware styles.
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.vue` — render the status block only after conversation start so the landing view stays clean.
- Create: `frontend/src/pages/interview/InterviewPage.test.ts` — cover landing state and post-submit layout switching.
- Modify: `frontend/src/store/interview/index.test.ts` — update tests for the empty initial message list and `hasStarted` behavior.
- Test: `frontend/src/pages/interview/components/TerminalChatPanel.test.ts` — keep citation behavior passing with the updated props contract.

### Task 1: Update interview store state model

**Files:**
- Modify: `frontend/src/store/interview/index.ts`
- Modify: `frontend/src/store/interview/index.test.ts`

- [ ] **Step 1: Write the failing store test for the new initial state**

```ts
it('starts on the landing state before any question is sent', () => {
  const store = useInterviewStore()

  expect(store.messages).toEqual([])
  expect(store.hasStarted).toBe(false)
})
```

- [ ] **Step 2: Write the failing store test for transition into chat mode**

```ts
it('marks the conversation as started after the first question is sent', async () => {
  const store = useInterviewStore()

  await store.send('介绍一下你的代表项目')

  expect(store.hasStarted).toBe(true)
  expect(store.messages[0].role).toBe('interviewer')
})
```

- [ ] **Step 3: Run the store tests to verify failure**

Run: `pnpm --dir frontend vitest run src/store/interview/index.test.ts`
Expected: FAIL because the store still seeds a welcome message and does not expose `hasStarted`.

- [ ] **Step 4: Implement the minimal store changes**

```ts
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { sendInterviewMessage } from './api'
import type { InterviewMessage, InterviewMode, InterviewStatus } from './types'

const sessionId = () => crypto.randomUUID()

export const useInterviewStore = defineStore('interview', () => {
  const mode = ref<InterviewMode>('text')
  const speechEnabled = ref(true)
  const status = ref<InterviewStatus>('idle')
  const voiceStatus = ref<InterviewStatus>('idle')
  const messages = ref<InterviewMessage[]>([])
  const draft = ref('')
  const currentSessionId = ref(sessionId())

  const hasStarted = computed(() => messages.value.length > 0)
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
    messages.value = []
    draft.value = ''
  }

  return {
    currentSessionId,
    displayStatus,
    draft,
    hasStarted,
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

- [ ] **Step 5: Update the reset test to the new empty-state contract**

```ts
it('reset clears the conversation and returns to the landing state', () => {
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

  expect(store.messages).toEqual([])
  expect(store.hasStarted).toBe(false)
  expect(store.status).toBe('idle')
})
```

- [ ] **Step 6: Re-run the store tests to verify they pass**

Run: `pnpm --dir frontend vitest run src/store/interview/index.test.ts`
Expected: PASS

- [ ] **Step 7: Commit the store change**

```bash
git add frontend/src/store/interview/index.ts frontend/src/store/interview/index.test.ts
git commit -m "feat: add interview landing state store"
```

### Task 2: Add landing layout to the interview page

**Files:**
- Modify: `frontend/src/pages/interview/InterviewPage.vue`
- Create: `frontend/src/pages/interview/InterviewPage.test.ts`

- [ ] **Step 1: Write the failing page test for the landing view**

```ts
it('shows the centered landing welcome before the first question', () => {
  const wrapper = mount(InterviewPage, {
    global: {
      plugins: [createTestingPinia({ stubActions: false })],
    },
  })

  expect(wrapper.text()).toContain('欢迎来到谢流星演示页')
  expect(wrapper.find('.landing-shell').exists()).toBe(true)
  expect(wrapper.find('.bottom-bar-wrap').exists()).toBe(false)
})
```

- [ ] **Step 2: Write the failing page test for switching into chat mode**

```ts
it('moves the input to the bottom after the first submitted question', async () => {
  const wrapper = mount(InterviewPage, {
    global: {
      plugins: [createTestingPinia({ stubActions: false })],
    },
  })
  const store = useInterviewStore()

  await store.send('介绍一下你的代表项目')
  await nextTick()

  expect(wrapper.find('.landing-shell').exists()).toBe(false)
  expect(wrapper.find('.bottom-bar-wrap').exists()).toBe(true)
  expect(wrapper.findComponent({ name: 'TerminalChatPanel' }).exists()).toBe(true)
})
```

- [ ] **Step 3: Run the page test to verify failure**

Run: `pnpm --dir frontend vitest run src/pages/interview/InterviewPage.test.ts`
Expected: FAIL because the landing layout and conditional bottom bar placement do not exist yet.

- [ ] **Step 4: Implement the landing/chat layout switch in `InterviewPage.vue`**

```vue
<template>
  <main class="interview-page">
    <div class="page-shell">
      <div class="scanline"></div>
      <TerminalTopBar :mode="store.mode" @update:mode="store.setMode" />

      <div class="workspace-area">
        <div class="chat-column" :class="{ 'chat-column-started': store.hasStarted }">
          <transition name="landing-fade" mode="out-in">
            <section v-if="!store.hasStarted" key="landing" class="landing-shell">
              <div class="landing-card">
                <h1 class="landing-title">欢迎来到谢流星演示页</h1>
                <p class="landing-copy">
                  你可以直接追问项目经历、架构取舍、技术深度，或者我在工程推进中的判断方式。
                </p>
                <div class="landing-input-wrap">
                  <TerminalBottomBar
                    :disabled="store.isBusy"
                    :draft="store.draft"
                    :speech-enabled="store.speechEnabled"
                    :voice-enabled="store.isVoiceMode && store.voiceStatus !== 'idle'"
                    @clear="store.reset"
                    @start-voice="store.startListening"
                    @stop-voice="store.stopListening"
                    @submit="store.send()"
                    @toggle-speech="store.toggleSpeech"
                    @update:draft="store.setDraft"
                  />
                </div>
              </div>
            </section>

            <section v-else key="chat" class="chat-shell">
              <TerminalChatPanel :messages="store.messages" :status="store.displayStatus" :show-status="store.hasStarted" />
            </section>
          </transition>

          <transition name="bottom-bar-slide">
            <div v-if="store.hasStarted" class="bottom-bar-wrap">
              <TerminalBottomBar
                :disabled="store.isBusy"
                :draft="store.draft"
                :speech-enabled="store.speechEnabled"
                :voice-enabled="store.isVoiceMode && store.voiceStatus !== 'idle'"
                @clear="store.reset"
                @start-voice="store.startListening"
                @stop-voice="store.stopListening"
                @submit="store.send()"
                @toggle-speech="store.toggleSpeech"
                @update:draft="store.setDraft"
              />
            </div>
          </transition>
        </div>
      </div>
    </div>
  </main>
</template>
```

- [ ] **Step 5: Add the landing and transition styles**

```css
.chat-column {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 0;
  overflow: hidden;
}

.chat-column-started {
  justify-content: flex-end;
}

.landing-shell,
.chat-shell {
  width: 100%;
  flex: 1;
  min-height: 0;
}

.landing-shell {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}

.landing-card {
  width: min(100%, 920px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  text-align: center;
}

.landing-title {
  margin: 0;
  font-size: clamp(40px, 5vw, 64px);
  line-height: 1.04;
  letter-spacing: -0.04em;
  color: #0b1c30;
}

.landing-copy {
  max-width: 760px;
  margin: 0;
  font-size: 18px;
  line-height: 32px;
  color: #3e484d;
}

.landing-input-wrap,
.bottom-bar-wrap {
  width: 100%;
  max-width: 800px;
}

.bottom-bar-wrap {
  flex-shrink: 0;
}

.landing-fade-enter-active,
.landing-fade-leave-active,
.bottom-bar-slide-enter-active,
.bottom-bar-slide-leave-active {
  transition: opacity 0.28s ease, transform 0.28s ease;
}

.landing-fade-enter-from,
.landing-fade-leave-to {
  opacity: 0;
  transform: translateY(18px);
}

.bottom-bar-slide-enter-from,
.bottom-bar-slide-leave-to {
  opacity: 0;
  transform: translateY(24px);
}
```

- [ ] **Step 6: Add the page test file with a stable mocked store flow**

```ts
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('../../../store/interview/api', () => ({
  sendInterviewMessage: vi.fn(async () => ({
    reply: {
      id: 'assistant-1',
      role: 'assistant',
      content: 'mock reply',
      sources: [],
      createdAt: '2026-05-22T00:00:00.000Z',
    },
  })),
}))

import InterviewPage from './InterviewPage.vue'
import { useInterviewStore } from '../../../store/interview'

describe('InterviewPage', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('shows the centered landing welcome before the first question', () => {
    const wrapper = mount(InterviewPage)

    expect(wrapper.text()).toContain('欢迎来到谢流星演示页')
    expect(wrapper.find('.landing-shell').exists()).toBe(true)
    expect(wrapper.find('.bottom-bar-wrap').exists()).toBe(false)
  })

  it('moves the input to the bottom after the first submitted question', async () => {
    const wrapper = mount(InterviewPage)
    const store = useInterviewStore()

    await store.send('介绍一下你的代表项目')
    await nextTick()

    expect(wrapper.find('.landing-shell').exists()).toBe(false)
    expect(wrapper.find('.bottom-bar-wrap').exists()).toBe(true)
    expect(wrapper.find('.chat-shell').exists()).toBe(true)
  })
})
```

- [ ] **Step 7: Re-run the page test to verify it passes**

Run: `pnpm --dir frontend vitest run src/pages/interview/InterviewPage.test.ts`
Expected: PASS

- [ ] **Step 8: Commit the page layout change**

```bash
git add frontend/src/pages/interview/InterviewPage.vue frontend/src/pages/interview/InterviewPage.test.ts
git commit -m "feat: add interview landing layout"
```

### Task 3: Keep the chat panel clean before conversation start

**Files:**
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.vue`
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.test.ts`

- [ ] **Step 1: Write the failing chat panel test for hiding the status block**

```ts
it('hides the status block when showStatus is false', () => {
  const wrapper = mount(TerminalChatPanel, {
    props: {
      messages: [],
      status: 'idle',
      showStatus: false,
    },
  })

  expect(wrapper.text()).not.toContain('AI 核心监测')
})
```

- [ ] **Step 2: Run the chat panel test to verify failure**

Run: `pnpm --dir frontend vitest run src/pages/interview/components/TerminalChatPanel.test.ts`
Expected: FAIL because `showStatus` is not a declared prop and the status block always renders.

- [ ] **Step 3: Implement the prop-gated status block**

```vue
<div v-if="showStatus" class="message-block thinking-block">
  <div class="message-meta message-meta-ai">
    <span class="message-icon">◆</span>
    <span>AI 核心监测</span>
  </div>
  <div class="message-card message-card-ai thinking-card">
    <p class="thinking-text">{{ statusText }}</p>
    <div class="code-card">
      <div class="code-card-header">
        <span>代码片段：TRANSFORMER_BLOCK</span>
        <span>复制</span>
      </div>
      <pre class="code-block">class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        assert d_model % num_heads == 0
        # 实现细节已隐藏...</pre>
      <div class="code-footer">
        <span>[知识来源：项目简历分段检索]</span>
        <span>[检索置信度：91%]</span>
      </div>
    </div>
  </div>
</div>
```

```ts
const props = defineProps<{
  messages: InterviewMessage[]
  status: InterviewStatus
  showStatus: boolean
}>()
```

- [ ] **Step 4: Update the existing chat panel tests to pass the new prop**

```ts
const wrapper = mount(TerminalChatPanel, {
  props: {
    messages: [assistantMessage],
    status: 'idle',
    showStatus: true,
  },
})
```

- [ ] **Step 5: Add the new hide-status test case**

```ts
it('hides the status block when showStatus is false', () => {
  const wrapper = mount(TerminalChatPanel, {
    props: {
      messages: [],
      status: 'idle',
      showStatus: false,
    },
  })

  expect(wrapper.text()).not.toContain('AI 核心监测')
})
```

- [ ] **Step 6: Re-run the chat panel test to verify it passes**

Run: `pnpm --dir frontend vitest run src/pages/interview/components/TerminalChatPanel.test.ts`
Expected: PASS

- [ ] **Step 7: Commit the chat panel update**

```bash
git add frontend/src/pages/interview/components/TerminalChatPanel.vue frontend/src/pages/interview/components/TerminalChatPanel.test.ts
git commit -m "feat: hide interview status on landing"
```

### Task 4: Run final verification

**Files:**
- Modify: `frontend/src/pages/interview/InterviewPage.vue`
- Modify: `frontend/src/store/interview/index.ts`
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.vue`
- Create: `frontend/src/pages/interview/InterviewPage.test.ts`
- Modify: `frontend/src/store/interview/index.test.ts`
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.test.ts`

- [ ] **Step 1: Run the full frontend test suite**

Run: `pnpm --dir frontend test`
Expected: PASS with the updated page, store, and chat-panel tests included.

- [ ] **Step 2: Run the frontend build**

Run: `pnpm --dir frontend build`
Expected: PASS and emit the Vite production bundle.

- [ ] **Step 3: Start the frontend dev server for UI verification**

Run: `pnpm --dir frontend dev --host 127.0.0.1 --port 4173`
Expected: Vite dev server starts and prints a local URL at `http://127.0.0.1:4173/`.

- [ ] **Step 4: Verify the landing flow in the browser**

Check in browser:
1. The first load shows only the top bar, centered welcome title/copy, and the centered input.
2. Submitting an empty draft does nothing.
3. Submitting the first question hides the landing view, shows the message list, and places the input bar at the bottom.
4. Clicking reset returns the page to the landing view.

- [ ] **Step 5: Commit the verified feature**

```bash
git add frontend/src/pages/interview/InterviewPage.vue frontend/src/pages/interview/InterviewPage.test.ts frontend/src/pages/interview/components/TerminalChatPanel.vue frontend/src/pages/interview/components/TerminalChatPanel.test.ts frontend/src/store/interview/index.ts frontend/src/store/interview/index.test.ts
git commit -m "feat: add interview landing experience"
```
