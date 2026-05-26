import type {
  InterviewMessage,
  InterviewMode,
  InterviewRequestError,
  InterviewStreamEvent,
  MessageCitation,
} from './types'

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

const isThinking = (value: unknown): boolean => {
  if (!value || typeof value !== 'object') {
    return false
  }

  const thinking = value as Record<string, unknown>
  return (
    (thinking.phase === 'retrieving' || thinking.phase === 'thinking' || thinking.phase === 'responding') &&
    typeof thinking.summary === 'string' &&
    typeof thinking.updatedAt === 'string'
  )
}

const isInterviewStreamEvent = (value: unknown): value is InterviewStreamEvent => {
  if (!value || typeof value !== 'object') {
    return false
  }

  const event = value as Record<string, unknown>
  if (!['status', 'thinking', 'delta', 'sources', 'done', 'error'].includes(String(event.type))) {
    return false
  }
  if (event.status != null && !['retrieving', 'thinking', 'responding', 'done', 'error'].includes(String(event.status))) {
    return false
  }
  if (event.delta != null && typeof event.delta !== 'string') {
    return false
  }
  if (event.replyId != null && typeof event.replyId !== 'string') {
    return false
  }
  if (event.createdAt != null && typeof event.createdAt !== 'string') {
    return false
  }
  if (event.error != null && typeof event.error !== 'string') {
    return false
  }
  if (event.sources != null && (!Array.isArray(event.sources) || !event.sources.every(isCitation))) {
    return false
  }
  if (event.thinking != null && !isThinking(event.thinking)) {
    return false
  }
  return true
}

const toInterviewRequestError = (statusCode: number, message: string): InterviewRequestError => ({
  statusCode,
  message,
})

const parseResponsePayload = (rawBody: string): { detail?: unknown; reply?: unknown } => {
  if (!rawBody.trim()) {
    return {}
  }

  try {
    return JSON.parse(rawBody) as { detail?: unknown; reply?: unknown }
  } catch {
    return {}
  }
}

const createRequestBody = ({ messages, mode }: ChatRequest) => JSON.stringify({
  messages: messages.map((message) => ({
    role: message.role,
    content: message.content,
  })),
  mode,
})

const readErrorResponse = async (response: Response) => {
  const rawBody = await response.text()
  const payload = parseResponsePayload(rawBody)
  return typeof payload.detail === 'string' ? payload.detail : 'Interview chat request failed'
}

export const sendInterviewMessage = async ({ messages, mode }: ChatRequest): Promise<ChatResponse> => {
  const response = await fetch('/api/interview/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: createRequestBody({ messages, mode }),
  })

  const rawBody = await response.text()
  const payload = parseResponsePayload(rawBody)

  if (!response.ok) {
    throw toInterviewRequestError(
      response.status,
      typeof payload.detail === 'string' ? payload.detail : 'Interview chat request failed',
    )
  }

  if (!isInterviewMessage(payload.reply)) {
    throw toInterviewRequestError(500, 'Interview chat payload has invalid reply shape')
  }

  return {
    reply: payload.reply,
  }
}

export const streamInterviewMessage = async (
  request: ChatRequest,
  onEvent: (event: InterviewStreamEvent) => void,
): Promise<void> => {
  const response = await fetch('/api/interview/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: createRequestBody(request),
  })

  if (!response.ok) {
    throw toInterviewRequestError(response.status, await readErrorResponse(response))
  }

  if (!response.body) {
    throw toInterviewRequestError(500, 'Interview stream response body is missing')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done })

    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? ''

    for (const frame of frames) {
      const dataLines = frame
        .split('\n')
        .filter((line) => line.startsWith('data:'))
        .map((line) => line.slice(5).trim())

      if (!dataLines.length) {
        continue
      }

      try {
        const parsed = JSON.parse(dataLines.join('\n')) as unknown
        if (isInterviewStreamEvent(parsed)) {
          onEvent(parsed)
        }
      } catch {
        throw toInterviewRequestError(500, 'Interview stream payload has invalid event shape')
      }
    }

    if (done) {
      break
    }
  }
}
