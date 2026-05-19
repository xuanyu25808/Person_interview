<template>
  <footer class="terminal-bottom-bar">
    <div class="input-wrap">
      <div class="input-shell">
        <input
          :value="draft"
          class="command-input"
          type="text"
          placeholder="请输入你的面试问题..."
          @input="$emit('update:draft', ($event.target as HTMLInputElement).value)"
          @keyup.enter="$emit('submit')"
        />
        <div class="input-actions">
          <button class="icon-button" type="button" @click="$emit('clear')">重置</button>
          <button class="icon-button" type="button" @click="$emit('toggle-speech')">
            {{ speechEnabled ? '播报开' : '播报关' }}
          </button>
          <button class="icon-button icon-button-mic" type="button" @click="voiceEnabled ? $emit('stop-voice') : $emit('start-voice')">
            {{ voiceEnabled ? '停麦' : '开麦' }}
          </button>
        </div>
      </div>
    </div>

    <div class="right-actions">
      <div class="side-buttons">
        <button class="circle-button circle-button-danger" type="button" title="开始新一轮" @click="$emit('clear')">↻</button>
        <button class="circle-button circle-button-primary" type="button" title="切换播报" @click="$emit('toggle-speech')">🔊</button>
      </div>
      <button class="send-button" type="button" :disabled="disabled" @click="$emit('submit')">发送同步</button>
    </div>
  </footer>
</template>

<script setup lang="ts">
defineProps<{
  disabled: boolean
  draft: string
  speechEnabled: boolean
  voiceEnabled: boolean
}>()

defineEmits<{
  clear: []
  'start-voice': []
  stop: []
  'stop-voice': []
  submit: []
  'toggle-speech': []
  'update:draft': [value: string]
}>()
</script>

<style scoped>
.terminal-bottom-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 88px;
  padding: 0 32px;
  margin-bottom: 24px;
  background: #ffffff;
  border: 1px solid rgba(189, 200, 206, 0.3);
  border-radius: 9999px;
  box-shadow: 0 12px 30px rgba(11, 28, 48, 0.08);
  backdrop-filter: blur(12px);
}

.input-wrap {
  flex: 1;
  position: relative;
}

.input-shell {
  position: relative;
  display: flex;
  align-items: center;
}

.command-input {
  width: 100%;
  padding: 12px 140px 12px 24px;
  background: #eff4ff;
  border: 1px solid rgba(189, 200, 206, 0.3);
  border-radius: 24px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  line-height: 22px;
  color: #0b1c30;
  outline: none;
  transition: all 0.2s ease;
}

.command-input::placeholder {
  color: #6e797e;
}

.command-input:focus {
  border-color: #00647c;
  box-shadow: 0 0 0 2px rgba(0, 100, 124, 0.12);
}

.input-actions {
  position: absolute;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-button {
  padding: 0;
  border: 0;
  background: transparent;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  line-height: 1;
  color: #3e484d;
}

.icon-button:hover {
  color: #00647c;
}

.icon-button-mic {
  color: #006c4a;
}

.right-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: 24px;
}

.side-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.circle-button {
  width: 40px;
  height: 40px;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  font-size: 18px;
  transition: all 0.2s ease;
}

.circle-button-danger {
  border: 1px solid rgba(186, 26, 26, 0.2);
  color: #ba1a1a;
}

.circle-button-danger:hover {
  background: rgba(186, 26, 26, 0.08);
}

.circle-button-primary {
  border: 1px solid rgba(0, 100, 124, 0.2);
  color: #00647c;
}

.circle-button-primary:hover {
  background: rgba(0, 100, 124, 0.08);
}

.send-button {
  padding: 12px 32px;
  border: 0;
  border-radius: 24px;
  background: #00647c;
  box-shadow: 0 8px 24px rgba(0, 100, 124, 0.2);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #ffffff;
  transition: all 0.2s ease;
}

.send-button:hover:not(:disabled) {
  filter: brightness(1.08);
}

.send-button:disabled {
  opacity: 0.65;
}
</style>
