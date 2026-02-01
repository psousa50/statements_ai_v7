import { ChatMessage, ChatResponseChunk } from '../types/Chat'

export interface ChatClient {
  sendMessage(message: string, history: ChatMessage[], onChunk: (chunk: ChatResponseChunk) => void): Promise<void>
}

export function createChatClient(baseUrl: string): ChatClient {
  return {
    async sendMessage(
      message: string,
      history: ChatMessage[],
      onChunk: (chunk: ChatResponseChunk) => void
    ): Promise<void> {
      const response = await fetch(`${baseUrl}/api/v1/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          message,
          history: history.map((m) => ({ role: m.role, content: m.content })),
        }),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Unknown error' }))
        throw new Error(error.message || `HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let buffer = ''
      let done = false

      while (!done) {
        const result = await reader.read()
        done = result.done

        if (result.value) {
          buffer += decoder.decode(result.value, { stream: true })

          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const chunk = JSON.parse(line.slice(6)) as ChatResponseChunk
                onChunk(chunk)
              } catch {
                console.error('Failed to parse SSE chunk:', line)
              }
            }
          }
        }
      }

      if (buffer.startsWith('data: ')) {
        try {
          const chunk = JSON.parse(buffer.slice(6)) as ChatResponseChunk
          onChunk(chunk)
        } catch {
          console.error('Failed to parse final SSE chunk:', buffer)
        }
      }
    },
  }
}
