import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { streamInterviewMessage } from './api'
import type { InterviewMessage, InterviewMode, InterviewRequestError, InterviewStatus, InterviewStreamEvent } from './types'

const sessionId = () => crypto.randomUUID()

const getErrorMessage = (error: unknown) => {
  if (!error || typeof error !== 'object') {
    return '当前后端问答链路暂时不可用，请稍后再试。'
  }

  const requestError = error as InterviewRequestError
  if (requestError.statusCode === 503) {
    return '当前检索或生成服务暂时不可用，请稍后重试。'
  }
  if (typeof requestError.message === 'string' && requestError.message) {
    return requestError.message
  }
  return '当前后端问答链路暂时不可用，请稍后再试。'
}

const createAssistantErrorReply = (error: unknown): InterviewMessage => {
  const requestError = error as Partial<InterviewRequestError> | undefined
  const detail = typeof requestError?.message === 'string' && requestError.message
    ? requestError.message
    : getErrorMessage(error)

  return {
    id: crypto.randomUUID(),
    role: 'assistant',
    content: `我暂时没法基于现有资料给出可靠回答。\n\n原因：${detail}`,
    sources: [],
    createdAt: new Date().toISOString(),
    state: 'error',
    thinking: null,
  }
}

const isStreamStatus = (value: InterviewStreamEvent['status']): value is Exclude<InterviewStatus, 'idle' | 'listening' | 'transcribing'> => {
  return value === 'retrieving' || value === 'thinking' || value === 'responding'
}

export const useInterviewStore = defineStore('interview', () => {
  const mode = ref<InterviewMode>('text')
  const speechEnabled = ref(true)
  const status = ref<InterviewStatus>('idle')
  const voiceStatus = ref<InterviewStatus>('idle')
  const messages = ref<InterviewMessage[]>([])
  const draft = ref('')
  const currentSessionId = ref(sessionId())
  const errorMessage = ref('')

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
      state: 'done',
      thinking: null,
    }

    const assistantMessage: InterviewMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      sources: [],
      createdAt: new Date().toISOString(),
      state: 'streaming',
      thinking: null,
    }

    messages.value.push(userMessage)
    messages.value.push(assistantMessage)
    draft.value = ''
    errorMessage.value = ''
    status.value = 'retrieving'

    try {
      await streamInterviewMessage(
        {
          messages: messages.value
            .filter((message) => message.role === 'interviewer' || (message.role === 'assistant' && message.content.trim()))
            .map((message) => ({
              role: message.role,
              content: message.content,
            })),
          mode: mode.value,
        },
        (event) => {
          const currentAssistant = messages.value.find((message) => message.id === assistantMessage.id)
          if (!currentAssistant) {
            return
          }

          if (event.replyId && currentAssistant.id !== event.replyId) {
            currentAssistant.id = event.replyId
          }
          if (event.createdAt && currentAssistant.createdAt !== event.createdAt) {
            currentAssistant.createdAt = event.createdAt
          }
          if (isStreamStatus(event.status)) {
            status.value = event.status
          }

          if (event.type === 'thinking' && event.thinking) {
            currentAssistant.thinking = event.thinking
          }

          if (event.type === 'delta' && event.delta) {
            currentAssistant.content += event.delta
            currentAssistant.state = 'streaming'
          }

          if (event.type === 'sources' && event.sources) {
            currentAssistant.sources = event.sources
          }

          if (event.type === 'done') {
            currentAssistant.state = 'done'
            status.value = 'idle'
          }

          if (event.type === 'error') {
            currentAssistant.state = 'error'
            currentAssistant.content = `我暂时没法基于现有资料给出可靠回答。\n\n原因：${event.error ?? 'Interview stream failed'}`
            currentAssistant.sources = []
            status.value = 'idle'
          }
        },
      )

      if (assistantMessage.state === 'streaming') {
        assistantMessage.state = 'done'
      }
    } catch (error) {
      messages.value[messages.value.length - 1] = createAssistantErrorReply(error)
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
    errorMessage.value = ''
  }

  return {
    currentSessionId,
    displayStatus,
    draft,
    errorMessage,
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

