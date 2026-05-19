<template>
  <aside class="status-panel">
    <div class="status-inner">
      <h2 class="panel-title">TELEMETRY_STREAM</h2>

      <div class="status-stack">
        <div class="status-card">
          <div class="status-card-left">
            <span class="status-dot status-dot-green"></span>
            <span class="status-label">状态</span>
          </div>
          <span class="status-value status-value-green">{{ statusText }}</span>
        </div>

        <div class="status-card">
          <div class="status-card-left">
            <span class="status-dot status-dot-blue"></span>
            <span class="status-label">话题</span>
          </div>
          <span class="status-value status-value-blue">{{ topicText }}</span>
        </div>

        <div class="preview-card"></div>
      </div>

      <div class="parameter-section">
        <h3 class="parameter-title">ACTIVE_PARAMETERS</h3>
        <div class="parameter-list">
          <span class="parameter-chip">模式：{{ modeLabel }}</span>
          <span class="parameter-chip">来源：{{ activeSources.length }}</span>
          <span class="parameter-chip">消息：{{ messagesCount }}</span>
          <span class="parameter-chip">语音播报：{{ speechEnabled ? '开启' : '关闭' }}</span>
        </div>
      </div>

      <div class="mini-map">
        <div class="mini-map-overlay"></div>
        <div class="mini-map-tag">当前节点</div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { InterviewMode, InterviewStatus, SourceTag } from '../../../store/interview/types'

const props = defineProps<{
  activeSources: SourceTag[]
  messagesCount: number
  mode: InterviewMode
  speechEnabled: boolean
  status: InterviewStatus
  topic: string
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
const modeLabel = computed(() => (props.mode === 'voice' ? '语音模式' : '文字模式'))
const topicText = computed(() => props.topic.replace(/\s+/g, '_').slice(0, 24))
</script>

<style scoped>
.status-panel {
  position: fixed;
  top: 128px;
  right: 32px;
  z-index: 20;
  display: none;
  width: 320px;
  max-height: calc(100vh - 160px);
  flex-direction: column;
  padding: 24px;
  overflow-y: auto;
  background: rgba(239, 244, 255, 0.95);
  border: 1px solid rgba(189, 200, 206, 0.2);
  border-radius: 24px;
  box-shadow: 0 12px 30px rgba(11, 28, 48, 0.08);
  backdrop-filter: blur(12px);
}

@media (min-width: 1280px) {
  .status-panel {
    display: flex;
  }
}

.status-inner {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.panel-title {
  margin: 0;
  padding: 0 8px 8px;
  border-bottom: 1px solid #bdc8ce;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.1em;
  color: #00647c;
}

.status-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #ffffff;
  border: 1px solid rgba(189, 200, 206, 0.4);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(11, 28, 48, 0.05);
}

.status-card-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot-green {
  background: #006c4a;
  box-shadow: 0 0 12px rgba(0, 108, 74, 0.3);
}

.status-dot-blue {
  background: #007f9d;
  box-shadow: 0 0 12px rgba(0, 100, 124, 0.2);
}

.status-label,
.status-value,
.parameter-title,
.parameter-chip,
.mini-map-tag {
  font-family: 'JetBrains Mono', monospace;
}

.status-label {
  font-size: 12px;
  line-height: 1;
  color: #0b1c30;
}

.status-value {
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
}

.status-value-green {
  color: #006c4a;
}

.status-value-blue {
  color: #00647c;
  text-transform: uppercase;
}

.preview-card {
  aspect-ratio: 16 / 9;
  border: 1px solid rgba(189, 200, 206, 0.4);
  border-radius: 16px;
  background:
    radial-gradient(circle at center, rgba(0, 100, 124, 0.18), transparent 42%),
    linear-gradient(135deg, #dce9ff, #eff4ff);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.parameter-section {
  padding: 16px 8px 0;
}

.parameter-title {
  margin: 0 0 16px;
  font-size: 10px;
  line-height: 1;
  color: #3e484d;
}

.parameter-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.parameter-chip {
  padding: 6px 12px;
  background: rgba(211, 228, 254, 0.4);
  border: 1px solid rgba(189, 200, 206, 0.4);
  border-radius: 9999px;
  font-size: 11px;
  line-height: 1;
  color: #0b1c30;
}

.mini-map {
  position: relative;
  height: 128px;
  overflow: hidden;
  border: 1px solid rgba(189, 200, 206, 0.4);
  border-radius: 16px;
  background:
    linear-gradient(to right, rgba(0, 100, 124, 0.08) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0, 100, 124, 0.08) 1px, transparent 1px),
    #eff4ff;
  background-size: 28px 28px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.mini-map-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 100, 124, 0.05);
}

.mini-map-tag {
  position: absolute;
  left: 8px;
  bottom: 8px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(189, 200, 206, 0.3);
  border-radius: 9999px;
  font-size: 9px;
  line-height: 1;
  color: #00647c;
}
</style>
