export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  data?: Record<string, unknown>
  isStreaming?: boolean
}

export interface ChatMessageRequest {
  message: string
  history: { role: string; content: string }[]
}

export interface ChatResponseChunk {
  type: 'text' | 'data' | 'done' | 'error'
  content?: string
  data?: Record<string, unknown>
  function?: string
}
