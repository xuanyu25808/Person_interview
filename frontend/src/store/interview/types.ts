export type InterviewMode = 'text' | 'voice'

export type InterviewStatus =
  | 'idle'
  | 'listening'
  | 'transcribing'
  | 'retrieving'
  | 'thinking'
  | 'responding'

export interface SourceTag {
  label: string
  kind: 'resume' | 'project' | 'note' | 'memory'
}

export interface InterviewMessage {
  id: string
  role: 'interviewer' | 'assistant'
  content: string
  sources: SourceTag[]
  createdAt: string
}
