import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'

/**
 * Feedback item from API response.
 */
export interface FeedbackItem {
  type: string
  severity: 'info' | 'warning' | 'critical'
  message: string
  suggestion?: string
  evidenceIds: string[]
  location?: string
}

/**
 * Analysis result (simplified).
 */
export interface AnalysisResult {
  feedback: FeedbackItem[]
  summary: string
  evidenceUsed: string[]
}

export type AnalysisStatus = 'idle' | 'analyzing' | 'success' | 'error'

export interface FeedbackContextValue {
  status: AnalysisStatus
  result: AnalysisResult | null
  error: string | null
  analyzeContent: (content: string) => Promise<void>
  clearAnalysis: () => void
}

const FeedbackContext = createContext<FeedbackContextValue | null>(null)

const API_BASE_URL = 'http://localhost:8000'

/**
 * Transform snake_case API response to camelCase.
 */
function transformResponse(data: unknown): AnalysisResult {
  const raw = data as Record<string, unknown>
  const feedbackRaw = (raw.feedback as Array<Record<string, unknown>>) || []

  return {
    feedback: feedbackRaw.map((f) => ({
      type: (f.type as string) || '',
      severity: (f.severity as 'info' | 'warning' | 'critical') || 'info',
      message: (f.message as string) || '',
      suggestion: f.suggestion as string | undefined,
      evidenceIds: (f.evidence_ids as string[]) || [],
      location: f.location as string | undefined,
    })),
    summary: (raw.summary as string) || '',
    evidenceUsed: (raw.evidence_used as string[]) || [],
  }
}

interface FeedbackProviderProps {
  children: ReactNode
}

export function FeedbackProvider({ children }: FeedbackProviderProps) {
  const [status, setStatus] = useState<AnalysisStatus>('idle')
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const analyzeContent = useCallback(async (content: string) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    setStatus('analyzing')
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/feedback/analyze-section`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: content }),
        signal: abortControllerRef.current.signal,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(
          (errorData as Record<string, string>).detail ||
            `Analysis failed: ${response.status}`
        )
      }

      const data: unknown = await response.json()
      setResult(transformResponse(data))
      setStatus('success')
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return
      }
      setError(err instanceof Error ? err.message : 'Analysis failed')
      setStatus('error')
    }
  }, [])

  const clearAnalysis = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    setStatus('idle')
    setResult(null)
    setError(null)
  }, [])

  const value = useMemo<FeedbackContextValue>(
    () => ({ status, result, error, analyzeContent, clearAnalysis }),
    [status, result, error, analyzeContent, clearAnalysis]
  )

  return (
    <FeedbackContext.Provider value={value}>
      {children}
    </FeedbackContext.Provider>
  )
}

export function useFeedbackContext(): FeedbackContextValue {
  const context = useContext(FeedbackContext)
  if (!context) {
    throw new Error('useFeedbackContext must be used within FeedbackProvider')
  }
  return context
}
