import React, { memo, useState, useCallback, type KeyboardEvent } from 'react'
import MaterialIcon from '@/shared/components/material-icon'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Ask a question about your references...',
}: ChatInputProps) {
  const [value, setValue] = useState('')

  const handleSend = useCallback(() => {
    const trimmed = value.trim()
    if (trimmed && !disabled) {
      onSend(trimmed)
      setValue('')
    }
  }, [value, disabled, onSend])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  return (
    <div className="chat-input-container">
      <textarea
        className="chat-input-field"
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        aria-label="Chat message input"
      />
      <button
        type="button"
        className="chat-send-btn"
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        aria-label="Send message"
      >
        <MaterialIcon type="send" />
      </button>
    </div>
  )
}

export default memo(ChatInput)
