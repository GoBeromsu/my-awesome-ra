import React, { useRef, useEffect, useCallback } from 'react'
import { useChatContext } from '../context/chat-context'
import ChatMessage from './chat-message'
import ChatInput from './chat-input'
import MaterialIcon from '@/shared/components/material-icon'
import withErrorBoundary from '@/infrastructure/error-boundary'

const EXAMPLE_QUESTIONS = [
  'What are the main contributions of this paper?',
  'How does this approach compare to prior work?',
  'What datasets were used for evaluation?',
]

function ChatEmpty({ onSelectQuestion }: { onSelectQuestion: (q: string) => void }) {
  return (
    <div className="chat-empty">
      <MaterialIcon type="forum" className="chat-empty-icon" />
      <h3 className="chat-empty-title">Research Assistant</h3>
      <p className="chat-empty-description">
        Ask questions about your uploaded references. I'll search through your
        documents and provide answers with citations.
      </p>
      <div className="chat-empty-suggestions">
        <span className="chat-empty-suggestions-label">Try asking:</span>
        {EXAMPLE_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            type="button"
            className="chat-suggestion-btn"
            onClick={() => onSelectQuestion(q)}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}

function ChatLoading() {
  return (
    <div className="chat-message chat-message--assistant chat-message--loading">
      <div className="chat-message-avatar">
        <MaterialIcon type="smart_toy" />
      </div>
      <div className="chat-message-content">
        <div className="chat-message-bubble">
          <div className="chat-typing-indicator">
            <span />
            <span />
            <span />
          </div>
        </div>
      </div>
    </div>
  )
}

function ChatPanelContent() {
  const { messages, status, error, sendMessage, clearHistory } = useChatContext()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const isLoading = status === 'loading'
  const hasMessages = messages.length > 0

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = useCallback(
    (question: string) => {
      sendMessage(question)
    },
    [sendMessage]
  )

  return (
    <div className="chat-panel">
      <div className="chat-panel-header">
        <h2 className="chat-panel-title">
          <MaterialIcon type="forum" />
          <span>Ask</span>
        </h2>
        {hasMessages && (
          <button
            type="button"
            className="chat-clear-btn"
            onClick={clearHistory}
            title="Clear chat history"
            aria-label="Clear chat history"
          >
            <MaterialIcon type="delete_sweep" />
          </button>
        )}
      </div>

      <div className="chat-messages-container">
        {!hasMessages && !isLoading ? (
          <ChatEmpty onSelectQuestion={handleSend} />
        ) : (
          <div className="chat-messages">
            {messages.map(msg => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {isLoading && <ChatLoading />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {error && (
        <div className="chat-error" role="alert">
          <MaterialIcon type="error" />
          <span>{error}</span>
        </div>
      )}

      <div className="chat-input-section">
        <ChatInput onSend={handleSend} disabled={isLoading} />
      </div>
    </div>
  )
}

function ChatPanelFallback() {
  return (
    <div className="chat-panel">
      <div className="chat-error" role="alert">
        <MaterialIcon type="error" />
        <span>Something went wrong.</span>
      </div>
    </div>
  )
}

const ChatPanelWithBoundary = withErrorBoundary(
  ChatPanelContent,
  () => <ChatPanelFallback />
)

export default React.memo(ChatPanelWithBoundary)
