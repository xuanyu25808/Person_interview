<template>
  <header class="terminal-top-bar">
    <div class="brand">AI_TWIN_INTERVIEWER :: Jonathan_V2.5</div>
    <div class="mode-switch">
      <button
        class="mode-button"
        :class="{ active: mode === 'text' }"
        type="button"
        @click="$emit('update:mode', 'text')"
      >
        [文字模式]
      </button>
      <button
        class="mode-button"
        :class="{ active: mode === 'voice' }"
        type="button"
        @click="$emit('update:mode', 'voice')"
      >
        [语音模式]
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import type { InterviewMode } from '../../../store/interview/types'

defineProps<{
  mode: InterviewMode
}>()

defineEmits<{
  'update:mode': [value: InterviewMode]
}>()
</script>

<style scoped>
.terminal-top-bar {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  margin-bottom: 48px;
  background: #ffffff;
  border-bottom: 1px solid #bdc8ce;
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.28em;
  color: #00647c;
}

.mode-switch {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(239, 244, 255, 0.7);
  border: 1px solid rgba(189, 200, 206, 0.3);
  border-radius: 9999px;
  backdrop-filter: blur(12px);
}

.mode-button {
  padding: 6px 16px;
  border: 0;
  border-radius: 9999px;
  background: transparent;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  color: #3e484d;
  transition: all 0.2s ease;
}

.mode-button.active {
  background: #00647c;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 100, 124, 0.18);
}

.mode-button:not(.active):hover {
  color: #00647c;
}
</style>
