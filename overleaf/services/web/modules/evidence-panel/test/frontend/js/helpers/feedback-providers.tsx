import React, { ReactNode } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import {
  FeedbackContextValue,
  AnalysisStatus,
  DocumentAnalysis,
  AnalysisProgress,
} from '../../../../frontend/js/context/feedback-context'

// Create a mock context for testing
const FeedbackContext = React.createContext<FeedbackContextValue | null>(null)

const defaultProgress: AnalysisProgress = {
  totalSections: 0,
  completedSections: 0,
  currentSection: null,
}

const defaultAnalysis: DocumentAnalysis = {
  overallSummary: 'Test summary',
  sectionReports: [],
  consistencyIssues: [],
  totalFeedbackCount: 0,
  severityCounts: { critical: 0, warning: 0, info: 0 },
}

const defaultContextValue: FeedbackContextValue = {
  status: 'idle' as AnalysisStatus,
  progress: defaultProgress,
  analysis: null,
  error: null,
  expandedSections: new Set<string>(),
  analyzeDocument: async () => {},
  clearAnalysis: () => {},
  toggleSection: () => {},
  expandAllSections: () => {},
  collapseAllSections: () => {},
}

interface FeedbackProviderWrapperProps {
  children: ReactNode
  value?: Partial<FeedbackContextValue>
}

export function FeedbackProviderWrapper({
  children,
  value = {},
}: FeedbackProviderWrapperProps) {
  const contextValue = { ...defaultContextValue, ...value }
  return (
    <FeedbackContext.Provider value={contextValue}>
      {children}
    </FeedbackContext.Provider>
  )
}

export function renderWithFeedbackContext(
  component: React.ReactElement,
  options: {
    contextValue?: Partial<FeedbackContextValue>
    renderOptions?: RenderOptions
  } = {}
) {
  const { contextValue = {}, renderOptions = {} } = options
  return render(component, {
    wrapper: ({ children }) => (
      <FeedbackProviderWrapper value={contextValue}>
        {children}
      </FeedbackProviderWrapper>
    ),
    ...renderOptions,
  })
}

export function createMockFeedbackItem(overrides = {}) {
  return {
    type: 'clarity',
    severity: 'info' as const,
    message: 'Test feedback message',
    suggestion: 'Test suggestion',
    evidenceIds: ['doc1'],
    location: 'line 10',
    ...overrides,
  }
}

export function createMockSectionReport(overrides = {}) {
  return {
    sectionTitle: 'Introduction',
    feedback: [createMockFeedbackItem()],
    summary: 'Section looks good.',
    evidenceUsed: ['doc1'],
    ...overrides,
  }
}

export function createMockAnalysis(overrides = {}): DocumentAnalysis {
  return {
    ...defaultAnalysis,
    sectionReports: [createMockSectionReport()],
    totalFeedbackCount: 1,
    severityCounts: { critical: 0, warning: 0, info: 1 },
    ...overrides,
  }
}
