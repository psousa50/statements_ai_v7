import { useState, useCallback } from 'react'
import { ChatMessage, ChatResponseChunk } from '../../types/Chat'
import { useApi } from '../../api/ApiContext'

export function useChat() {
  const { chatClient } = useApi()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isStreaming) return

      setError(null)

      const userMessage: ChatMessage = { role: 'user', content: text }
      const assistantMessage: ChatMessage = { role: 'assistant', content: '', isStreaming: true }

      setMessages((prev) => [...prev, userMessage, assistantMessage])
      setIsStreaming(true)

      try {
        let fullContent = ''
        const history = messages.slice()

        await chatClient.sendMessage(text, history, (chunk: ChatResponseChunk) => {
          if (chunk.type === 'text' && chunk.content) {
            fullContent += chunk.content
            setMessages((prev) => {
              const updated = [...prev]
              const lastIdx = updated.length - 1
              if (updated[lastIdx]?.role === 'assistant') {
                updated[lastIdx] = { ...updated[lastIdx], content: fullContent }
              }
              return updated
            })
          } else if (chunk.type === 'data' && chunk.data) {
            setMessages((prev) => {
              const updated = [...prev]
              const lastIdx = updated.length - 1
              if (updated[lastIdx]?.role === 'assistant') {
                updated[lastIdx] = { ...updated[lastIdx], data: chunk.data }
              }
              return updated
            })
          } else if (chunk.type === 'error' && chunk.content) {
            setError(chunk.content)
          }
        })

        setMessages((prev) => {
          const updated = [...prev]
          const lastIdx = updated.length - 1
          if (updated[lastIdx]?.role === 'assistant') {
            updated[lastIdx] = { ...updated[lastIdx], isStreaming: false }
          }
          return updated
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to send message')
        setMessages((prev) => prev.slice(0, -1))
      } finally {
        setIsStreaming(false)
      }
    },
    [chatClient, messages, isStreaming]
  )

  const clearHistory = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  return {
    messages,
    isStreaming,
    error,
    sendMessage,
    clearHistory,
  }
}
