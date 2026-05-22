import { createMockReply } from './mock'
import type { InterviewMessage, MessageCitation } from './types'

export interface ChatRequest {
  sessionId: string
  message: string
  history: Array<{
    role: 'interviewer' | 'assistant'
    content: string
  }>
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

export const sendInterviewMessage = async ({ sessionId, message, history }: ChatRequest): Promise<ChatResponse> => {
  try {
    const response = await fetch('/api/interview/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        history: history.map((turn) => ({
          role: turn.role,
          content: turn.content,
        })),
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
  } catch {
    return createMockReply(message)
  }
}
