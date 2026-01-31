import { expect } from 'chai'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import sinon from 'sinon'
import fetchMock from 'fetch-mock'
import React from 'react'

import {
  renderWithReferencesContext,
  createMockPaper,
  createMockPapers,
} from '../helpers/references-providers'
import { ReferencesPanel } from '../../../../frontend/js/components/references-panel'

describe('References Panel', function () {
  beforeEach(function () {
    fetchMock.removeRoutes().clearHistory()
  })

  afterEach(function () {
    fetchMock.removeRoutes().clearHistory()
    sinon.restore()
  })

  describe('Empty State', function () {
    it('shows empty state when no papers', function () {
      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: { papers: [], isLoading: false },
      })

      expect(screen.getByText('no_references')).to.exist
      expect(screen.getByText('upload_pdfs_hint')).to.exist
    })

    it('shows upload button in empty state', function () {
      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: { papers: [], isLoading: false },
      })

      expect(screen.getByRole('button', { name: /upload_pdfs/i })).to.exist
    })
  })

  describe('Loading State', function () {
    it('shows loading spinner when loading with no papers', function () {
      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: { papers: [], isLoading: true },
      })

      expect(screen.getByText('loading_references')).to.exist
    })
  })

  describe('Papers List', function () {
    it('renders list of papers', function () {
      const papers = createMockPapers(3)

      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: { papers, isLoading: false },
      })

      expect(screen.getByRole('tree')).to.exist
    })

    it('shows correct indexed count in header', function () {
      const papers = [
        createMockPaper({ indexStatus: 'indexed' }),
        createMockPaper({ citeKey: 'Paper2', indexStatus: 'indexed' }),
        createMockPaper({ citeKey: 'Paper3', indexStatus: 'none' }),
      ]

      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: { papers, isLoading: false },
      })

      // 2 indexed out of 3 total
      expect(screen.getByText('2/3')).to.exist
    })

    it('shows processing indicator when papers are indexing', function () {
      const papers = [
        createMockPaper({ indexStatus: 'indexing' }),
      ]

      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: { papers, isLoading: false },
      })

      // Should have sync icon spinning
      const syncIcon = document.querySelector('.icon-spin')
      expect(syncIcon).to.exist
    })
  })

  describe('Error State', function () {
    it('shows error banner when error exists', function () {
      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: {
          papers: [],
          isLoading: false,
          error: 'Failed to fetch documents',
        },
      })

      expect(screen.getByText('Failed to fetch documents')).to.exist
    })
  })

  describe('Header Actions', function () {
    it('has upload button in header', function () {
      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: { papers: createMockPapers(1), isLoading: false },
      })

      const uploadButton = screen.getByLabelText('upload_pdf_files')
      expect(uploadButton).to.exist
    })

    it('has refresh button in header', function () {
      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: { papers: createMockPapers(1), isLoading: false },
      })

      const refreshButton = screen.getByLabelText('refresh_list')
      expect(refreshButton).to.exist
    })

    it('calls refreshAll when refresh button clicked', async function () {
      const refreshAll = sinon.stub().resolves()

      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: {
          papers: createMockPapers(1),
          isLoading: false,
          refreshAll,
        },
      })

      const refreshButton = screen.getByLabelText('refresh_list')
      fireEvent.click(refreshButton)

      expect(refreshAll.calledOnce).to.be.true
    })

    it('disables refresh button when loading', function () {
      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: {
          papers: createMockPapers(1),
          isLoading: true,
        },
      })

      const refreshButton = screen.getByLabelText('refresh_list')
      expect(refreshButton.hasAttribute('disabled')).to.be.true
    })
  })

  describe('Accessibility', function () {
    it('has proper tree role on papers list', function () {
      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: { papers: createMockPapers(2), isLoading: false },
      })

      expect(screen.getByRole('tree')).to.exist
    })

    it('has aria-label on papers list', function () {
      renderWithReferencesContext(<ReferencesPanel />, {
        contextValue: { papers: createMockPapers(1), isLoading: false },
      })

      const tree = screen.getByRole('tree')
      expect(tree.getAttribute('aria-label')).to.equal('reference_library')
    })
  })
})
