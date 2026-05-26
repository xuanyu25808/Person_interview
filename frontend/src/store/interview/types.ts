export type InterviewMode = 'text' | 'voice'

export type InterviewStatus =
  | 'idle'
  | 'listening'
  | 'transcribing'
  | 'retrieving'
  | 'thinking'
  | 'responding'

export interface MessageCitation {
  title: string
  url: string
  snippet: string
  kind: string
}

export interface InterviewThinking {
  phase: 'retrieving' | 'thinking' | 'responding'
  summary: string
  updatedAt: string
}

export interface InterviewMessage {
  id: string
  role: 'interviewer' | 'assistant'
  content: string
  sources: MessageCitation[]
  createdAt: string
  state?: 'streaming' | 'done' | 'error'
  thinking?: InterviewThinking | null
}

export interface InterviewRequestError {
  statusCode: number
  message: string
}

export interface InterviewStreamEvent {
  type: 'status' | 'thinking' | 'delta' | 'sources' | 'done' | 'error'
  status?: 'retrieving' | 'thinking' | 'responding' | 'done' | 'error'
  thinking?: InterviewThinking | null
  delta?: string | null
  sources?: MessageCitation[] | null
  replyId?: string | null
  createdAt?: string | null
  error?: string | null
}
