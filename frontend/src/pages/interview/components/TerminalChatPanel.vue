<template>
  <section class="chat-panel">
    <div class="chat-scroll">
      <div
        v-for="message in messages"
        :key="message.id"
        class="message-block"
        :class="message.role === 'interviewer' ? 'message-block-user' : 'message-block-ai'"
      >
        <div class="message-meta" :class="message.role === 'interviewer' ? 'message-meta-user' : 'message-meta-ai'">
          <span class="message-icon">{{ message.role === 'interviewer' ? '◉' : '◆' }}</span>
          <span>{{ message.role === 'interviewer' ? '候选人输入' : 'AI 核心输出' }}</span>
        </div>

        <div class="message-card" :class="message.role === 'interviewer' ? 'message-card-user' : 'message-card-ai'">
          <p class="message-content">{{ message.content }}</p>
          <div v-if="message.sources.length" class="message-sources">
            <span v-for="source in message.sources" :key="`${message.id}-${source.label}`" class="source-tag">
              {{ source.label }}
            </span>
          </div>
        </div>
      </div>

      <div class="message-block thinking-block">
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
  idle: '等待新的面试问题输入...',
  listening: '正在监听语音输入...',
  transcribing: '正在将语音转换为文本...',
  retrieving: '正在检索候选人相关资料...',
  thinking: '正在生成回答结构与论证顺序...',
  responding: '正在输出本轮回答内容...',
}

const statusText = computed(() => statusTextMap[props.status])
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
}

.chat-scroll {
  width: 100%;
  max-width: 800px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 32px 32px 16px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.chat-scroll::-webkit-scrollbar {
  display: none;
}

.message-block {
  max-width: 768px;
  margin-bottom: 40px;
}

.message-block-user {
  margin-left: auto;
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

.message-sources {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.source-tag {
  padding: 6px 12px;
  border: 1px solid rgba(189, 200, 206, 0.4);
  border-radius: 9999px;
  background: rgba(239, 244, 255, 0.75);
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  line-height: 1;
  color: #3e484d;
}

.thinking-block {
  max-width: 800px;
  margin-bottom: 16px;
}

.thinking-card {
  box-shadow: none;
}

.thinking-text {
  margin: 0 0 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  line-height: 22px;
  font-style: italic;
  color: rgba(0, 100, 124, 0.8);
}

.code-card {
  padding: 24px;
  background: #eff4ff;
  border: 1px solid rgba(189, 200, 206, 0.3);
  border-radius: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.code-card-header,
.code-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  line-height: 16px;
  color: #3e484d;
}

.code-block {
  margin: 16px 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  line-height: 22px;
  color: #006c4a;
  white-space: pre-wrap;
}
</style>
