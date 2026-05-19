<template>
  <main class="interview-page">
    <div class="page-shell">
      <div class="scanline"></div>
      <TerminalTopBar :mode="store.mode" @update:mode="store.setMode" />

      <div class="workspace-area">
        <div class="chat-column">
          <TerminalChatPanel :messages="store.messages" :status="store.displayStatus" />
          <div class="bottom-bar-wrap">
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

        <TerminalStatusPanel
          :active-sources="store.activeSources"
          :messages-count="store.messages.length"
          :mode="store.mode"
          :speech-enabled="store.speechEnabled"
          :status="store.displayStatus"
          :topic="store.topic"
        />
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import TerminalBottomBar from './components/TerminalBottomBar.vue'
import TerminalChatPanel from './components/TerminalChatPanel.vue'
import TerminalStatusPanel from './components/TerminalStatusPanel.vue'
import TerminalTopBar from './components/TerminalTopBar.vue'
import { useInterviewStore } from '../../store/interview'

const store = useInterviewStore()
</script>

<style scoped>
.interview-page {
  width: 100%;
  min-width: 100%;
  height: 100vh;
  min-height: 100vh;
  background: #f8f9ff;
  color: #0b1c30;
  overflow: hidden;
}

.page-shell {
  position: relative;
  width: 100%;
  min-width: 100%;
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-height: 100vh;
  overflow: hidden;
}

.page-shell::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.scanline {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: rgba(0, 100, 124, 0.05);
  pointer-events: none;
  z-index: 5;
  animation: scan 6s linear infinite;
}

.workspace-area {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.chat-column {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 0;
  overflow: hidden;
}

.bottom-bar-wrap {
  width: 100%;
  max-width: 800px;
  flex-shrink: 0;
  margin-bottom: 24px;
}

@media (max-width: 1279px) {
  .bottom-bar-wrap {
    max-width: none;
    margin: 0 24px 24px;
  }
}

@keyframes scan {
  from {
    top: 0;
  }

  to {
    top: 100%;
  }
}
</style>
