import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'

export interface ChatSource {
  text: string
  documentTitle: string | null
  documentId: string | null
  page: number | null
  score: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: ChatSource[]
  timestamp: Date
}

export type ChatStatus = 'idle' | 'loading' | 'error'

export interface ChatContextValue {
  messages: ChatMessage[]
  status: ChatStatus
  error: string | null
  sendMessage: (question: string) => Promise<void>
  clearHistory: () => void
}

const ChatContext = createContext<ChatContextValue | null>(null)

const API_BASE_URL = 'http://localhost:8000'

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

interface ApiResponse {
  answer: string
  sources: Array<{
    text: string
    document_title: string | null
    document_id: string | null
    page: number | null
    score: number
  }>
  question: string
}

function transformSources(
  sources: ApiResponse['sources']
): ChatSource[] {
  return sources.map(s => ({
    text: s.text,
    documentTitle: s.document_title,
    documentId: s.document_id,
    page: s.page,
    score: s.score,
  }))
}

interface ChatProviderProps {
  children: ReactNode
}

export function ChatProvider({ children }: ChatProviderProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [status, setStatus] = useState<ChatStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim()) return

    // Cancel any pending request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    // Add user message
    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: question.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setStatus('loading')
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/chat/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim(), top_k: 5 }),
        signal: abortControllerRef.current.signal,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(
          (errorData as Record<string, string>).detail ||
            `Request failed: ${response.status}`
        )
      }

      const data: ApiResponse = await response.json()

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: data.answer,
        sources: transformSources(data.sources),
        timestamp: new Date(),
      }

      setMessages(prev => [...prev, assistantMessage])
      setStatus('idle')
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return
      }
      setError(err instanceof Error ? err.message : 'Failed to send message')
      setStatus('error')
    }
  }, [])

  const clearHistory = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    setMessages([])
    setStatus('idle')
    setError(null)
  }, [])

  const value = useMemo<ChatContextValue>(
    () => ({ messages, status, error, sendMessage, clearHistory }),
    [messages, status, error, sendMessage, clearHistory]
  )

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  )
}

export function useChatContext(): ChatContextValue {
  const context = useContext(ChatContext)
  if (!context) {
    throw new Error('useChatContext must be used within ChatProvider')
  }
  return context
}
