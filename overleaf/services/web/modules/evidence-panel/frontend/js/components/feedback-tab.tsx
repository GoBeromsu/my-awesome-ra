import React from 'react'
import { FeedbackProvider } from '../context/feedback-context'
import FeedbackPanel from './feedback-panel'

/**
 * Feedback tab wrapper that provides context to the panel.
 */
function FeedbackTab() {
  return (
    <FeedbackProvider>
      <FeedbackPanel />
    </FeedbackProvider>
  )
}

export default React.memo(FeedbackTab)
