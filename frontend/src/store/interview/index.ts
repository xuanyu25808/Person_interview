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

