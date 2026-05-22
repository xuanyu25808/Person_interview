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

export interface InterviewMessage {
  id: string
  role: 'interviewer' | 'assistant'
  content: string
  sources: MessageCitation[]
  createdAt: string
}
