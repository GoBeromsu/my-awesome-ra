import React, { useCallback } from 'react'
import { useFeedbackContext } from '../context/feedback-context'
import FeedbackItem from './feedback-item'
import MaterialIcon from '@/shared/components/material-icon'
import withErrorBoundary from '@/infrastructure/error-boundary'

function FeedbackResults() {
  const { result } = useFeedbackContext()

  if (!result) {
    return null
  }

  const severityCounts = result.feedback.reduce(
    (acc, f) => {
      acc[f.severity] = (acc[f.severity] || 0) + 1
      return acc
    },
    { critical: 0, warning: 0, info: 0 } as Record<string, number>
  )

  return (
    <div className="feedback-results">
      {result.summary && (
        <div className="overall-assessment">
          <h3 className="overall-assessment-title">SUMMARY</h3>
          <p className="overall-assessment-summary">{result.summary}</p>
          <div className="overall-assessment-counts">
            {severityCounts.critical > 0 && (
              <span className="severity-count severity-count--critical">
                <MaterialIcon type="error" />
                {severityCounts.critical} Critical
              </span>
            )}
            {severityCounts.warning > 0 && (
              <span className="severity-count severity-count--warning">
                <MaterialIcon type="warning" />
                {severityCounts.warning} Warnings
              </span>
            )}
            {severityCounts.info > 0 && (
              <span className="severity-count severity-count--info">
                <MaterialIcon type="info" />
                {severityCounts.info} Info
              </span>
            )}
            {result.feedback.length === 0 && (
              <span className="severity-count severity-count--success">
                <MaterialIcon type="check_circle" />
                No issues found
              </span>
            )}
          </div>
        </div>
      )}

      {result.feedback.length > 0 && (
        <div className="feedback-list">
          {result.feedback.map((item, idx) => (
            <FeedbackItem key={idx} item={item} index={idx} />
          ))}
        </div>
      )}
    </div>
  )
}

function FeedbackPanelContent() {
  const { status, error, analyzeContent, clearAnalysis } = useFeedbackContext()

  const handleAnalyze = useCallback(async () => {
    const editorView = (window as unknown as Record<string, unknown>)
      ._ide_editorView as { state?: { doc?: { toString?: () => string } } } | undefined

    const content = editorView?.state?.doc?.toString?.()
    if (!content?.trim()) {
      return
    }

    await analyzeContent(content)
  }, [analyzeContent])

  const isAnalyzing = status === 'analyzing'
  const hasResults = status === 'success'

  return (
    <div className="feedback-panel">
      <div className="feedback-panel-actions">
        <button
          className="feedback-analyze-btn"
          onClick={handleAnalyze}
          disabled={isAnalyzing}
          type="button"
        >
          {isAnalyzing ? (
            <>
              <MaterialIcon type="autorenew" className="analyzing-icon" />
              Analyzing...
            </>
          ) : (
            <>
              <MaterialIcon type="rate_review" />
              Analyze
            </>
          )}
        </button>
        {hasResults && (
          <button
            className="feedback-clear-btn"
            onClick={clearAnalysis}
            title="Clear results"
            type="button"
          >
            <MaterialIcon type="close" />
          </button>
        )}
      </div>

      {error && (
        <div className="feedback-error" role="alert">
          <MaterialIcon type="error" />
          <span>{error}</span>
        </div>
      )}

      <FeedbackResults />

      {status === 'idle' && (
        <div className="feedback-empty">
          <MaterialIcon type="rate_review" className="feedback-empty-icon" />
          <p className="feedback-empty-title">Paper Feedback</p>
          <p className="feedback-empty-description">
            Click "Analyze" to get AI-powered feedback on your paper.
          </p>
        </div>
      )}
    </div>
  )
}

function FeedbackPanelFallback() {
  return (
    <div className="feedback-panel">
      <div className="feedback-error" role="alert">
        <MaterialIcon type="error" />
        <span>Something went wrong.</span>
      </div>
    </div>
  )
}

const FeedbackPanelWithBoundary = withErrorBoundary(
  FeedbackPanelContent,
  () => <FeedbackPanelFallback />
)

export default React.memo(FeedbackPanelWithBoundary)
