import React, { memo, useState } from 'react'
import MaterialIcon from '@/shared/components/material-icon'
import type { ChatSource } from '../context/chat-context'

interface ChatSourcesProps {
  sources: ChatSource[]
}

function ChatSourceItem({ source, index }: { source: ChatSource; index: number }) {
  const scorePercent = Math.round(source.score * 100)
  const scoreClass =
    scorePercent >= 80 ? 'high' : scorePercent >= 60 ? 'medium' : 'low'

  return (
    <div className="chat-source-item">
      <div className="chat-source-header">
        <span className="chat-source-number">{index + 1}</span>
        <span className="chat-source-title">
          {source.documentTitle || 'Unknown Document'}
        </span>
        {source.page && (
          <span className="chat-source-page">p.{source.page}</span>
        )}
        <span className={`chat-source-score chat-source-score--${scoreClass}`}>
          {scorePercent}%
        </span>
      </div>
      <blockquote className="chat-source-text">{source.text}</blockquote>
    </div>
  )
}

function ChatSources({ sources }: ChatSourcesProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (sources.length === 0) {
    return null
  }

  return (
    <div className="chat-sources">
      <button
        type="button"
        className="chat-sources-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <MaterialIcon type={isExpanded ? 'expand_less' : 'expand_more'} />
        <span>
          {sources.length} source{sources.length !== 1 ? 's' : ''}
        </span>
      </button>

      {isExpanded && (
        <div className="chat-sources-list">
          {sources.map((source, idx) => (
            <ChatSourceItem key={idx} source={source} index={idx} />
          ))}
        </div>
      )}
    </div>
  )
}

export default memo(ChatSources)
