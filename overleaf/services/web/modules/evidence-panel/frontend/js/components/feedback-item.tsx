import React, { useCallback, useState } from 'react'
import { type FeedbackItem as FeedbackItemType } from '../context/feedback-context'
import MaterialIcon from '@/shared/components/material-icon'

interface FeedbackItemProps {
  item: FeedbackItemType
  index: number
}

const SEVERITY_CONFIG: Record<
  string,
  { icon: string; className: string; label: string }
> = {
  critical: {
    icon: 'error',
    className: 'feedback-item--critical',
    label: 'Critical',
  },
  warning: {
    icon: 'warning',
    className: 'feedback-item--warning',
    label: 'Warning',
  },
  info: {
    icon: 'info',
    className: 'feedback-item--info',
    label: 'Info',
  },
}

const TYPE_LABELS: Record<string, string> = {
  clarity: 'Clarity',
  consistency: 'Consistency',
  reference_support: 'Reference Support',
  structure: 'Structure',
  citation_needed: 'Citation Needed',
}

function FeedbackItemComponent({ item, index }: FeedbackItemProps) {
  const [expanded, setExpanded] = useState(item.severity === 'critical')
  const [copied, setCopied] = useState(false)

  const severityConfig = SEVERITY_CONFIG[item.severity] || SEVERITY_CONFIG.info
  const typeLabel = TYPE_LABELS[item.type] || item.type

  const handleToggle = useCallback(() => {
    setExpanded((prev) => !prev)
  }, [])

  const handleCopySuggestion = useCallback(async () => {
    if (item.suggestion) {
      try {
        await navigator.clipboard.writeText(item.suggestion)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      } catch {
        // Fallback for older browsers
        const textarea = document.createElement('textarea')
        textarea.value = item.suggestion
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }
    }
  }, [item.suggestion])

  return (
    <div
      className={`feedback-item ${severityConfig.className}`}
      role="article"
      aria-label={`${severityConfig.label} feedback: ${item.message.slice(0, 50)}`}
    >
      <button
        className="feedback-item-header"
        onClick={handleToggle}
        aria-expanded={expanded}
        type="button"
      >
        <span className="feedback-item-severity">
          <MaterialIcon type={severityConfig.icon} />
          <span className="feedback-severity-label">{severityConfig.label}</span>
        </span>
        <span className="feedback-item-type">{typeLabel}</span>
        <span className={`feedback-expand-icon ${expanded ? 'expanded' : ''}`}>
          <MaterialIcon type="expand_more" />
        </span>
      </button>

      <div className={`feedback-item-body ${expanded ? 'expanded' : ''}`}>
        <p className="feedback-message">{item.message}</p>

        {item.location && (
          <p className="feedback-location">
            <MaterialIcon type="location_on" />
            {item.location}
          </p>
        )}

        {item.suggestion && (
          <div className="feedback-suggestion">
            <div className="feedback-suggestion-header">
              <MaterialIcon type="lightbulb" />
              <span>Suggestion</span>
              <button
                className="feedback-copy-btn"
                onClick={handleCopySuggestion}
                title="Copy suggestion"
                type="button"
              >
                <MaterialIcon type={copied ? 'check' : 'content_copy'} />
              </button>
            </div>
            <p className="feedback-suggestion-text">{item.suggestion}</p>
          </div>
        )}

        {item.evidenceIds.length > 0 && (
          <div className="feedback-evidence">
            <MaterialIcon type="menu_book" />
            <span className="feedback-evidence-label">Related references:</span>
            {item.evidenceIds.map((id, idx) => (
              <span key={id} className="feedback-evidence-id">
                {id}
                {idx < item.evidenceIds.length - 1 ? ', ' : ''}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default React.memo(FeedbackItemComponent)
