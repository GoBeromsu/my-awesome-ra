import React, {
  createContext,
  useContext,
  useCallback,
  useMemo,
  useState,
  useEffect,
  FC,
  ReactNode,
} from 'react'
import { useBibEntries, BibEntry } from '../hooks/use-bib-entries'
import {
  useDocumentsApi,
  IndexedDocument,
} from '../hooks/use-documents-api'
import {
  IndexStatus,
  mapDocumentStatusToIndexStatus,
} from '../utils/status-mapping'
import { useReferencesContext } from '@/features/ide-react/context/references-context'

export type { IndexStatus }

export interface ReferencePaper {
  citeKey: string
  title?: string
  authors?: string
  year?: string
  hasPdf: boolean
  pdfFileId?: string
  pdfFilename?: string
  indexStatus: IndexStatus
  documentId?: string
  chunkCount?: number
  error?: string
}

export interface ReferencesPanelContextValue {
  papers: ReferencePaper[]
  isLoading: boolean
  error: string | null
  selectedDocId: string | null
  setSelectedDocId: (docId: string | null) => void
  refreshAll: () => Promise<void>
  indexPaper: (citeKey: string, file: File) => Promise<void>
  reindexPaper: (documentId: string) => Promise<void>
  removePaper: (documentId: string) => Promise<void>
  uploadPdf: (file: File, citeKey?: string) => Promise<string | null>
}

export const ReferencesPanelContext = createContext<
  ReferencesPanelContextValue | undefined
>(undefined)

interface ReferencesPanelProviderProps {
  children: ReactNode
}

/**
 * Creates lookup maps for matching indexed documents by citeKey and title
 */
function createDocumentLookupMaps(indexedDocs: IndexedDocument[]): {
  byCiteKey: Map<string, IndexedDocument>
  byTitle: Map<string, IndexedDocument>
} {
  const byCiteKey = new Map<string, IndexedDocument>()
  const byTitle = new Map<string, IndexedDocument>()

  for (const doc of indexedDocs) {
    if (doc.citeKey) {
      byCiteKey.set(doc.citeKey.toLowerCase(), doc)
    }
    const titleKey = doc.title.toLowerCase().replace(/\.pdf$/i, '')
    byTitle.set(titleKey, doc)
  }

  return { byCiteKey, byTitle }
}

/**
 * Finds matching indexed document for a cite key
 */
function findMatchingDocument(
  citeKey: string,
  lookupMaps: ReturnType<typeof createDocumentLookupMaps>
): IndexedDocument | undefined {
  const citeKeyLower = citeKey.toLowerCase()
  return (
    lookupMaps.byCiteKey.get(citeKeyLower) ||
    lookupMaps.byTitle.get(citeKeyLower)
  )
}

/**
 * Converts a bib entry with optional indexed document to a ReferencePaper
 */
function createPaperFromBibEntry(
  entry: BibEntry,
  indexedDoc: IndexedDocument | undefined
): ReferencePaper {
  return {
    citeKey: entry.citeKey,
    title: entry.title,
    authors: entry.authors,
    year: entry.year,
    hasPdf: entry.hasPdf,
    pdfFileId: entry.pdfFileId,
    pdfFilename: entry.pdfFilename,
    indexStatus: mapDocumentStatusToIndexStatus(indexedDoc?.status),
    documentId: indexedDoc?.documentId,
    chunkCount: indexedDoc?.chunkCount,
    error: indexedDoc?.message,
  }
}

/**
 * Converts an orphan indexed document to a ReferencePaper
 */
function createPaperFromOrphanDoc(doc: IndexedDocument): ReferencePaper {
  return {
    citeKey: doc.citeKey || doc.title,
    title: doc.title,
    hasPdf: true,
    indexStatus: mapDocumentStatusToIndexStatus(doc.status),
    documentId: doc.documentId,
    chunkCount: doc.chunkCount,
    error: doc.message,
  }
}

export const ReferencesPanelProvider: FC<ReferencesPanelProviderProps> = ({
  children,
}) => {
  const { referenceKeys, indexAllReferences } = useReferencesContext()
  const { bibEntries, refresh: refreshBibEntries } = useBibEntries(referenceKeys)
  const {
    documents: indexedDocs,
    isLoading: apiLoading,
    error: apiError,
    fetchDocuments,
    uploadDocument,
    reindexDocument,
    removeDocument,
  } = useDocumentsApi()

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)

  // Sync error from API hook
  useEffect(() => {
    if (apiError) setError(apiError)
  }, [apiError])

  // Initial load
  useEffect(() => {
    const init = async () => {
      setIsLoading(true)
      await fetchDocuments()
      setIsLoading(false)
    }
    init()
  }, [fetchDocuments])

  const refreshAll = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      await indexAllReferences(false)
      refreshBibEntries()
      await fetchDocuments()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Refresh failed'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [indexAllReferences, refreshBibEntries, fetchDocuments])

  const uploadPdf = useCallback(
    async (file: File, citeKey?: string): Promise<string | null> => {
      return uploadDocument(file, citeKey)
    },
    [uploadDocument]
  )

  const indexPaper = useCallback(
    async (citeKey: string, file: File): Promise<void> => {
      await uploadDocument(file, citeKey)
    },
    [uploadDocument]
  )

  const reindexPaper = useCallback(
    async (documentId: string): Promise<void> => {
      await reindexDocument(documentId)
    },
    [reindexDocument]
  )

  const removePaper = useCallback(
    async (documentId: string): Promise<void> => {
      await removeDocument(documentId)
    },
    [removeDocument]
  )

  // Merge bib entries with indexed documents
  const papers = useMemo<ReferencePaper[]>(() => {
    const lookupMaps = createDocumentLookupMaps(indexedDocs)

    // Build papers from bib entries
    const papersFromBib = bibEntries.map(entry => {
      const indexedDoc = findMatchingDocument(entry.citeKey, lookupMaps)
      return createPaperFromBibEntry(entry, indexedDoc)
    })

    // Find orphan indexed docs (not matched to any bib entry)
    const bibCiteKeys = new Set(
      bibEntries.map(e => e.citeKey.toLowerCase())
    )
    const orphanDocs = indexedDocs.filter(doc => {
      const citeKeyMatch =
        doc.citeKey && bibCiteKeys.has(doc.citeKey.toLowerCase())
      const titleMatch = bibCiteKeys.has(
        doc.title.toLowerCase().replace(/\.pdf$/i, '')
      )
      return !citeKeyMatch && !titleMatch
    })

    const orphanPapers = orphanDocs.map(createPaperFromOrphanDoc)

    return [...papersFromBib, ...orphanPapers]
  }, [bibEntries, indexedDocs])

  const value = useMemo<ReferencesPanelContextValue>(
    () => ({
      papers,
      isLoading: isLoading || apiLoading,
      error,
      selectedDocId,
      setSelectedDocId,
      refreshAll,
      indexPaper,
      reindexPaper,
      removePaper,
      uploadPdf,
    }),
    [
      papers,
      isLoading,
      apiLoading,
      error,
      selectedDocId,
      refreshAll,
      indexPaper,
      reindexPaper,
      removePaper,
      uploadPdf,
    ]
  )

  return (
    <ReferencesPanelContext.Provider value={value}>
      {children}
    </ReferencesPanelContext.Provider>
  )
}

export function useReferencesPanelContext(): ReferencesPanelContextValue {
  const context = useContext(ReferencesPanelContext)
  if (!context) {
    throw new Error(
      'useReferencesPanelContext must be used within a ReferencesPanelProvider'
    )
  }
  return context
}
