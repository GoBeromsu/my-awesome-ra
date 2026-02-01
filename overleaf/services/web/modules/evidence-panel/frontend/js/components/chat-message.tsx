import React, { memo } from 'react'
import MaterialIcon from '@/shared/components/material-icon'
import ChatSources from './chat-sources'
import type { ChatMessage as ChatMessageType } from '../context/chat-context'

interface ChatMessageProps {
  message: ChatMessageType
}

function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const timeString = message.timestamp.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div className={`chat-message chat-message--${message.role}`}>
      <div className="chat-message-avatar">
        <MaterialIcon type={isUser ? 'person' : 'smart_toy'} />
      </div>
      <div className="chat-message-content">
        <div className="chat-message-bubble">
          <p className="chat-message-text">{message.content}</p>
        </div>
        {message.sources && message.sources.length > 0 && (
          <ChatSources sources={message.sources} />
        )}
        <span className="chat-message-time">{timeString}</span>
      </div>
    </div>
  )
}

export default memo(ChatMessage)
