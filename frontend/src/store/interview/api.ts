import type { InterviewMessage, InterviewMode, MessageCitation } from './types'

export interface ChatRequest {
  messages: Array<{
    role: 'interviewer' | 'assistant'
    content: string
  }>
  mode: InterviewMode
}

export interface ChatResponse {
  reply: InterviewMessage
}

const isCitation = (value: unknown): value is MessageCitation => {
  if (!value || typeof value !== 'object') {
    return false
  }

  const citation = value as Record<string, unknown>
  return (
    typeof citation.title === 'string' &&
    typeof citation.url === 'string' &&
    typeof citation.snippet === 'string' &&
    typeof citation.kind === 'string'
  )
}

const isInterviewMessage = (value: unknown): value is InterviewMessage => {
  if (!value || typeof value !== 'object') {
    return false
  }

  const message = value as Record<string, unknown>
  return (
    typeof message.id === 'string' &&
    (message.role === 'assistant' || message.role === 'interviewer') &&
    typeof message.content === 'string' &&
    Array.isArray(message.sources) &&
    message.sources.every(isCitation) &&
    typeof message.createdAt === 'string'
  )
}

export const sendInterviewMessage = async ({ messages, mode }: ChatRequest): Promise<ChatResponse> => {
  const response = await fetch('/api/interview/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages: messages.map((message) => ({
        role: message.role,
        content: message.content,
      })),
      mode,
    }),
  })

  if (!response.ok) {
    throw new Error('Interview chat request failed')
  }

  const payload = (await response.json()) as { reply?: unknown }
  if (!isInterviewMessage(payload.reply)) {
    throw new Error('Interview chat payload has invalid reply shape')
  }

  return {
    reply: payload.reply,
  }
}
