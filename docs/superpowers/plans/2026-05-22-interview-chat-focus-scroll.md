# Interview Chat Focus Scroll Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the floating status box from the interview chat panel and make each newly submitted interviewer message scroll into the top of the chat viewport.

**Architecture:** Keep scrolling behavior inside the chat page boundary rather than the store. `TerminalChatPanel.vue` becomes a pure message viewport that exposes a DOM-based scroll method, while `InterviewPage.vue` detects newly added interviewer messages and asks the panel to align that specific message to the top. The status telemetry block is deleted entirely so the chat stream only contains real conversation content.

**Tech Stack:** Vue 3, Pinia, TypeScript, Vitest, Vue Test Utils

---

## File map

- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.vue` — remove the status block, add interviewer message anchors, and expose a scroll method.
- Modify: `frontend/src/pages/interview/InterviewPage.vue` — hold a panel ref, watch the latest interviewer message, and trigger smooth top alignment.
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.test.ts` — verify the removed status box and the new interviewer message selector markers.
- Modify: `frontend/src/pages/interview/InterviewPage.test.ts` — verify the page requests scrolling when a new interviewer message is sent.
- Modify: `frontend/src/ui-copy.test.ts` — remove assertions tied to the deleted telemetry copy and keep the new landing/chat copy checks passing.

### Task 1: Simplify the chat panel and expose message scrolling

**Files:**
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.vue`
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.test.ts`

- [ ] **Step 1: Write the failing chat panel test for interviewer anchors**

```ts
it('adds a stable selector to interviewer messages for scroll targeting', () => {
  const wrapper = mount(TerminalChatPanel, {
    props: {
      messages: [interviewerMessage],
    },
  })

  const message = wrapper.get('[data-message-id="user-1"]')
  expect(message.attributes('data-message-role')).toBe('interviewer')
})
```

- [ ] **Step 2: Write the failing chat panel test for the deleted telemetry box**

```ts
it('does not render the telemetry status box', () => {
  const wrapper = mount(TerminalChatPanel, {
    props: {
      messages: [assistantMessage],
    },
  })

  expect(wrapper.text()).not.toContain('AI 核心监测')
  expect(wrapper.text()).not.toContain('TRANSFORMER_BLOCK')
})
```

- [ ] **Step 3: Run the chat panel tests to verify failure**

Run: `cd "C:/Users/DXM-1002/Desktop/xuanyu/xuanyu/frontend" && pnpm vitest run src/pages/interview/components/TerminalChatPanel.test.ts`
Expected: FAIL because the component still requires status props, still renders the telemetry box, and does not include message anchor attributes.

- [ ] **Step 4: Implement the simplified chat panel structure**

```vue
<template>
  <section class="chat-panel">
    <div ref="scrollContainer" class="chat-scroll">
      <div
        v-for="message in messages"
        :key="message.id"
        class="message-block"
        :class="message.role === 'interviewer' ? 'message-block-user' : 'message-block-ai'"
        :data-message-id="message.id"
        :data-message-role="message.role"
      >
        <div class="message-meta" :class="message.role === 'interviewer' ? 'message-meta-user' : 'message-meta-ai'">
          <span class="message-icon">{{ message.role === 'interviewer' ? '◉' : '◆' }}</span>
          <span>{{ message.role === 'interviewer' ? '候选人输入' : 'AI 核心输出' }}</span>
        </div>

        <div class="message-card" :class="message.role === 'interviewer' ? 'message-card-user' : 'message-card-ai'">
          <p class="message-content">{{ message.content }}</p>

          <section v-if="message.role === 'assistant' && message.sources.length" class="message-citations">
            <h3 class="message-citations-title">引用来源</h3>
            <ul class="message-citations-list">
              <li
                v-for="source in message.sources"
                :key="`${message.id}-${source.kind}-${source.title}`"
                class="citation-card"
              >
                <p class="citation-title">{{ source.title }}</p>
                <a class="citation-link" :href="source.url" target="_blank" rel="noreferrer noopener">
                  {{ source.url }}
                </a>
                <p class="citation-snippet">{{ source.snippet }}</p>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { InterviewMessage } from '../../../store/interview/types'

defineProps<{
  messages: InterviewMessage[]
}>()

const scrollContainer = ref<HTMLDivElement | null>(null)

const scrollMessageToTop = (messageId: string) => {
  const container = scrollContainer.value
  if (!container) {
    return
  }

  const target = container.querySelector<HTMLElement>(`[data-message-id="${messageId}"]`)
  if (!target) {
    return
  }

  container.scrollTo({
    top: target.offsetTop,
    behavior: 'smooth',
  })
}

defineExpose({
  scrollMessageToTop,
})
</script>
```

- [ ] **Step 5: Update the chat panel test file to the new prop contract**

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
  sources: [],
  createdAt: '2026-05-21T00:00:00.000Z',
}
```

- [ ] **Step 6: Add the new assertions to the chat panel tests**

```ts
it('adds a stable selector to interviewer messages for scroll targeting', () => {
  const wrapper = mount(TerminalChatPanel, {
    props: {
      messages: [interviewerMessage],
    },
  })

  const message = wrapper.get('[data-message-id="user-1"]')
  expect(message.attributes('data-message-role')).toBe('interviewer')
})

it('does not render the telemetry status box', () => {
  const wrapper = mount(TerminalChatPanel, {
    props: {
      messages: [assistantMessage],
    },
  })

  expect(wrapper.text()).not.toContain('AI 核心监测')
  expect(wrapper.text()).not.toContain('TRANSFORMER_BLOCK')
})
```

- [ ] **Step 7: Re-run the chat panel tests to verify they pass**

Run: `cd "C:/Users/DXM-1002/Desktop/xuanyu/xuanyu/frontend" && pnpm vitest run src/pages/interview/components/TerminalChatPanel.test.ts`
Expected: PASS

### Task 2: Trigger top alignment for the latest interviewer message

**Files:**
- Modify: `frontend/src/pages/interview/InterviewPage.vue`
- Modify: `frontend/src/pages/interview/InterviewPage.test.ts`

- [ ] **Step 1: Write the failing page test for scrolling after send**

```ts
it('scrolls the latest interviewer message into view after send', async () => {
  const wrapper = mount(InterviewPage)
  const store = useInterviewStore()
  const chatPanel = wrapper.findComponent({ name: 'TerminalChatPanel' })

  await store.send('介绍一下你的代表项目')
  await nextTick()

  expect(chatPanel.vm.scrollMessageToTop).toHaveBeenCalledWith(store.messages[0].id)
})
```

- [ ] **Step 2: Run the page test to verify failure**

Run: `cd "C:/Users/DXM-1002/Desktop/xuanyu/xuanyu/frontend" && pnpm vitest run src/pages/interview/InterviewPage.test.ts`
Expected: FAIL because `InterviewPage.vue` does not hold a panel ref or trigger scroll requests after new interviewer messages.

- [ ] **Step 3: Implement scroll coordination in `InterviewPage.vue`**

```vue
<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import TerminalBottomBar from './components/TerminalBottomBar.vue'
import TerminalChatPanel from './components/TerminalChatPanel.vue'
import TerminalTopBar from './components/TerminalTopBar.vue'
import { useInterviewStore } from '../../store/interview'

const store = useInterviewStore()
const chatPanelRef = ref<InstanceType<typeof TerminalChatPanel> | null>(null)

const latestInterviewerMessageId = computed(() => {
  for (let index = store.messages.length - 1; index >= 0; index -= 1) {
    const message = store.messages[index]
    if (message.role === 'interviewer') {
      return message.id
    }
  }

  return null
})

watch(latestInterviewerMessageId, async (messageId, previousMessageId) => {
  if (!messageId || messageId === previousMessageId) {
    return
  }

  await nextTick()
  chatPanelRef.value?.scrollMessageToTop(messageId)
})
</script>
```

```vue
<TerminalChatPanel
  ref="chatPanelRef"
  :messages="store.messages"
/>
```

- [ ] **Step 4: Replace the page test with a stubbed scroll method assertion**

```ts
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'

const scrollMessageToTop = vi.fn()

vi.mock('./components/TerminalChatPanel.vue', () => ({
  default: defineComponent({
    name: 'TerminalChatPanel',
    props: {
      messages: {
        type: Array,
        required: true,
      },
    },
    setup(_, { expose }) {
      expose({ scrollMessageToTop })
      return () => h('div', { class: 'chat-shell-stub' })
    },
  }),
}))
```

- [ ] **Step 5: Add the page scroll assertion with the stubbed panel**

```ts
it('scrolls the latest interviewer message into view after send', async () => {
  const wrapper = mount(InterviewPage)
  const store = useInterviewStore()

  await store.send('介绍一下你的代表项目')
  await nextTick()

  expect(wrapper.find('.chat-shell').exists()).toBe(true)
  expect(scrollMessageToTop).toHaveBeenCalledWith(store.messages[0].id)
})
```

- [ ] **Step 6: Re-run the page tests to verify they pass**

Run: `cd "C:/Users/DXM-1002/Desktop/xuanyu/xuanyu/frontend" && pnpm vitest run src/pages/interview/InterviewPage.test.ts`
Expected: PASS

### Task 3: Update copy tests and run final verification

**Files:**
- Modify: `frontend/src/ui-copy.test.ts`
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.vue`
- Modify: `frontend/src/pages/interview/InterviewPage.vue`
- Modify: `frontend/src/pages/interview/components/TerminalChatPanel.test.ts`
- Modify: `frontend/src/pages/interview/InterviewPage.test.ts`

- [ ] **Step 1: Update the UI copy regression test to stop asserting deleted telemetry text**

```ts
it('keeps the Chinese interaction copy and avoids old English marketing text', () => {
  const topBar = read('pages/interview/components/TerminalTopBar.vue')
  const bottomBar = read('pages/interview/components/TerminalBottomBar.vue')
  const page = read('pages/interview/InterviewPage.vue')
  const chatPanel = read('pages/interview/components/TerminalChatPanel.vue')

  expect(topBar).toContain('文字模式')
  expect(topBar).toContain('语音模式')
  expect(bottomBar).toContain('请输入你的面试问题')
  expect(page).toContain('谢流星演示页')
  expect(chatPanel).not.toContain('TRANSFORMER_BLOCK')
  expect(`${topBar}\n${bottomBar}\n${page}\n${chatPanel}`).not.toContain('AI Interview Twin')
})
```

- [ ] **Step 2: Run the full frontend test suite**

Run: `cd "C:/Users/DXM-1002/Desktop/xuanyu/xuanyu/frontend" && pnpm test`
Expected: PASS

- [ ] **Step 3: Run the production build**

Run: `cd "C:/Users/DXM-1002/Desktop/xuanyu/xuanyu/frontend" && pnpm build`
Expected: PASS

- [ ] **Step 4: Start the frontend dev server for browser verification**

Run: `cd "C:/Users/DXM-1002/Desktop/xuanyu/xuanyu/frontend" && pnpm dev --host 127.0.0.1 --port 4173`
Expected: local Vite server starts at `http://127.0.0.1:4173/`.

- [ ] **Step 5: Verify the chat behavior in the browser**

Check in browser:
1. The landing page still shows the welcome title and centered input before the first question.
2. After the first question, the telemetry/status box is gone.
3. After each submitted question, the newly added interviewer message aligns to the top of the chat viewport.
4. Assistant replies do not yank the scroll position away from that aligned question.
5. Reset still returns to the landing screen.

- [ ] **Step 6: Commit the verified change**

```bash
git add frontend/src/pages/interview/components/TerminalChatPanel.vue frontend/src/pages/interview/InterviewPage.vue frontend/src/pages/interview/components/TerminalChatPanel.test.ts frontend/src/pages/interview/InterviewPage.test.ts frontend/src/ui-copy.test.ts
git commit -m "feat: focus interview chat on latest question"
```
