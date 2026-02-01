import React from 'react'
import { ChatProvider } from '../context/chat-context'
import ChatPanel from './chat-panel'

/**
 * Chat tab wrapper that provides context to the panel.
 */
function ChatTab() {
  return (
    <ChatProvider>
      <ChatPanel />
    </ChatProvider>
  )
}

export default React.memo(ChatTab)
