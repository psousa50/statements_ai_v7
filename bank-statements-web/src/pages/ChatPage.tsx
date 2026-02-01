import { useState, useRef, useEffect } from 'react'
import { useChat } from '../services/hooks/useChat'
import { ChatMessage } from '../types/Chat'
import './ChatPage.css'

const SUGGESTED_QUESTIONS = [
  'How much did I spend on groceries last month?',
  'What are my biggest expense categories?',
  'Show me my recurring subscriptions',
  'How does my spending compare month over month?',
]

export const ChatPage = () => {
  const { messages, isStreaming, error, sendMessage, clearHistory } = useChat()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isStreaming) {
      sendMessage(input.trim())
      setInput('')
    }
  }

  const handleSuggestedQuestion = (question: string) => {
    if (!isStreaming) {
      sendMessage(question)
    }
  }

  return (
    <div className="chat-page">
      <header className="page-header">
        <div className="header-content">
          <div>
            <h1>AI Assistant</h1>
            <p className="page-description">Ask questions about your transactions, spending patterns, and more</p>
          </div>
          {messages.length > 0 && (
            <button className="clear-button" onClick={clearHistory} disabled={isStreaming}>
              Clear Chat
            </button>
          )}
        </div>
      </header>

      <main className="chat-container">
        {messages.length === 0 ? (
          <div className="welcome-container">
            <div className="welcome-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <h2>How can I help you today?</h2>
            <p>Ask me anything about your financial data</p>
            <div className="suggested-questions">
              {SUGGESTED_QUESTIONS.map((question, idx) => (
                <button key={idx} className="suggested-question" onClick={() => handleSuggestedQuestion(question)}>
                  {question}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages-container">
            {messages.map((msg, idx) => (
              <MessageBubble key={idx} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}

        {error && <div className="error-banner">{error}</div>}

        <form className="input-container" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            disabled={isStreaming}
            className="chat-input"
          />
          <button type="submit" disabled={isStreaming || !input.trim()} className="send-button">
            {isStreaming ? (
              <span className="loading-dots">
                <span>.</span>
                <span>.</span>
                <span>.</span>
              </span>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13" />
                <path d="M22 2l-7 20-4-9-9-4 20-7z" />
              </svg>
            )}
          </button>
        </form>
      </main>
    </div>
  )
}

const MessageBubble = ({ message }: { message: ChatMessage }) => {
  const isUser = message.role === 'user'

  return (
    <div className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-content">
        {message.content || (message.isStreaming && <span className="streaming-cursor" />)}
      </div>
    </div>
  )
}
