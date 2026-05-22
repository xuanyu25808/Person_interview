<template>
  <section class="chat-panel">
    <div ref="scrollContainer" class="chat-scroll">
      <div
        v-for="(message, messageIndex) in messages"
        :key="message.id"
        class="message-block"
        :class="[
          {
            'message-block-user': message.role === 'interviewer',
            'message-block-ai': message.role === 'assistant',
            marginBotom: messageIndex === messages.length - 1,
          }
        ]"
        :data-message-id="message.id"
        :data-message-role="message.role"
      >
        <div class="message-meta" :class="message.role === 'interviewer' ? 'message-meta-user' : 'message-meta-ai'">
          <span class="message-icon">{{ message.role === 'interviewer' ? '◉' : '◆' }}</span>
          <span>{{ message.role === 'interviewer' ? '面试官输入' : '谢流星AI输出' }}</span>
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
                <a
                  class="citation-link"
                  :href="source.url"
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  {{ source.url }}
                </a>
                <p class="citation-snippet">{{ source.snippet }}</p>
              </li>
            </ul>
          </section>
        </div>
      </div>
      <!-- <div class="scroll-spacer" aria-hidden="true"></div> -->
    </div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import type { InterviewMessage } from '../../../store/interview/types'

const props = defineProps<{
  messages: InterviewMessage[]
}>()

const scrollContainer = ref<HTMLDivElement | null>(null)

const scrollToBottom = () => {
  const container = scrollContainer.value
  if (!container) {
    return
  }

  const nextTop = container.scrollHeight - container.clientHeight
  container.scrollTo({
    top: Math.max(0, nextTop),
    behavior: 'smooth',
  })
}

watch(
  () => props.messages.length,
  async (messageCount, previousMessageCount) => {
    if (messageCount <= previousMessageCount) {
      return
    }

    await nextTick()
    scrollToBottom()
  },
  { flush: 'post' },
)

defineExpose({
  scrollToBottom,
})
</script>

<style scoped>
.chat-panel {
  flex: 1;
  width: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
  background: transparent;
  height: 100%;
}

.chat-scroll {
  /* max-height: calc(100vh - 200px); */
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0 32px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.chat-scroll::-webkit-scrollbar {
  display: none;
}

.message-block {
  max-width: 768px;
  min-width: 768px;
  margin-top: 40px;
  &.marginBotom{
    margin-bottom: 20px;
  }
}

.message-block-user {
  margin-left: auto;
}

.scroll-spacer {
  height: clamp(160px, 24vh, 280px);
  width: 100%;
  flex-shrink: 0;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.1em;
}

.message-meta-ai {
  margin-left: 8px;
  color: #00647c;
}

.message-meta-user {
  justify-content: flex-end;
  margin-right: 8px;
  color: #3e484d;
}

.message-icon {
  font-size: 14px;
}

.message-card {
  border: 1px solid rgba(189, 200, 206, 0.3);
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 100, 124, 0.08);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.message-card:hover {
  box-shadow: 0 10px 30px rgba(0, 100, 124, 0.1);
}

.message-card-ai {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
}

.message-card-user {
  background: rgba(0, 100, 124, 0.05);
  border-color: rgba(0, 100, 124, 0.2);
  box-shadow: inset 0 0 0 1px rgba(0, 100, 124, 0.04);
}

.message-content {
  margin: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  line-height: 24px;
  color: #0b1c30;
  white-space: pre-wrap;
}

.message-citations {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(189, 200, 206, 0.3);
}

.message-citations-title {
  margin: 0 0 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #3e484d;
}

.message-citations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.citation-card {
  padding: 12px 14px;
  border: 1px solid rgba(189, 200, 206, 0.35);
  border-radius: 16px;
  background: rgba(239, 244, 255, 0.78);
}

.citation-title {
  margin: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: #0b1c30;
}

.citation-link {
  display: inline-block;
  margin-top: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  line-height: 18px;
  color: #00647c;
  word-break: break-all;
}

.citation-snippet {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 20px;
  color: #3e484d;
}
</style>
