import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { createMockReply } from './mock'
import type { InterviewMessage, InterviewMode, InterviewStatus, SourceTag } from './types'

const openingTopic = '建议先从自我介绍或一个代表项目切入。'

const openingSources: SourceTag[] = [
  { label: '简历摘要', kind: 'resume' },
  { label: '项目亮点', kind: 'project' },
]

const createWelcomeMessage = (): InterviewMessage => ({
  id: 'welcome',
  role: 'assistant',
  content:
    '欢迎来到 AI 面试分身演示页。你可以直接追问项目经历、架构取舍、技术深度，或者我在工程推进中的判断方式。',
  sources: openingSources,
  createdAt: new Date().toISOString(),
})

export const useInterviewStore = defineStore('interview', () => {
  const mode = ref<InterviewMode>('text')
  const speechEnabled = ref(true)
  const status = ref<InterviewStatus>('idle')
  const voiceStatus = ref<InterviewStatus>('idle')
  const topic = ref(openingTopic)
  const activeSources = ref<SourceTag[]>(openingSources)
  const messages = ref<InterviewMessage[]>([createWelcomeMessage()])
  const draft = ref('')

  const isBusy = computed(() => status.value !== 'idle')
  const isVoiceMode = computed(() => mode.value === 'voice')
  const displayStatus = computed(() => {
    if (isVoiceMode.value && voiceStatus.value !== 'idle') {
      return voiceStatus.value
    }

    return status.value
  })

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

    messages.value.push({
      id: crypto.randomUUID(),
      role: 'interviewer',
      content: value,
      sources: [],
      createdAt: new Date().toISOString(),
    })

    draft.value = ''
    status.value = 'retrieving'
    await new Promise((resolve) => setTimeout(resolve, 250))
    status.value = 'thinking'

    const payload = await createMockReply(value)

    status.value = 'responding'
    messages.value.push(payload.reply)
    topic.value = payload.topic
    activeSources.value = payload.activeSources

    await new Promise((resolve) => setTimeout(resolve, 200))
    status.value = 'idle'
  }

  const reset = () => {
    status.value = 'idle'
    voiceStatus.value = 'idle'
    topic.value = openingTopic
    activeSources.value = openingSources
    messages.value = [createWelcomeMessage()]
    draft.value = ''
  }

  return {
    activeSources,
    displayStatus,
    draft,
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
    topic,
    voiceStatus,
  }
})
