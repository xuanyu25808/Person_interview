<template>
  <main class="interview-page">
    <div class="page-shell">
      <div class="scanline"></div>
      <div class="workspace-area">
        <div class="chat-column" :class="{ 'chat-column-started': store.hasStarted }">
          <transition name="landing-fade" mode="out-in">
            <section v-if="!store.hasStarted" key="landing" class="landing-shell">
              <div class="landing-card">
                <h1 class="landing-title">欢迎来到谢流星演示页</h1>
                <p class="landing-copy">
                  略略略
                </p>
                <div class="landing-input-wrap">
                  <p v-if="statusLabel" class="status-banner">{{ statusLabel }}</p>
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
              <TerminalChatPanel
                ref="chatPanelRef"
                :messages="store.messages"
              />
            </section>
          </transition>

          <transition name="bottom-bar-slide">
            <div v-if="store.hasStarted" class="bottom-bar-wrap">
              <p v-if="statusLabel" class="status-banner status-banner-chat">{{ statusLabel }}</p>
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

<script setup lang="ts">
import { computed } from 'vue'
import { useInterviewStore } from '../../store/interview'
import TerminalBottomBar from './components/TerminalBottomBar.vue'
import TerminalChatPanel from './components/TerminalChatPanel.vue'

const store = useInterviewStore()

const statusLabel = computed(() => {
  if (store.displayStatus === 'retrieving') {
    return '正在检索资料'
  }
  if (store.displayStatus === 'thinking') {
    return '正在思考'
  }
  if (store.displayStatus === 'responding') {
    return '正在生成回答'
  }
  return ''
})
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

.chat-shell {
  display: flex;
  flex-direction: column;
  align-items: center;
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

.status-banner {
  margin: 0 0 12px;
  padding: 10px 14px;
  border: 1px solid rgba(0, 100, 124, 0.14);
  border-radius: 14px;
  background: rgba(0, 100, 124, 0.05);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #00647c;
  text-align: center;
}

.status-banner-chat {
  margin-bottom: 14px;
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

@media (max-width: 1279px) {
  .landing-shell {
    padding: 24px;
  }

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
