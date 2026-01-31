import type { DocumentStatus } from '../hooks/use-documents-api'

export type IndexStatus = 'none' | 'indexing' | 'indexed' | 'error'

/**
 * Maps internal document status to UI-facing index status
 */
export function mapDocumentStatusToIndexStatus(
  status: DocumentStatus | undefined
): IndexStatus {
  if (!status) return 'none'

  switch (status) {
    case 'processing':
      return 'indexing'
    case 'indexed':
      return 'indexed'
    case 'error':
      return 'error'
    default:
      return 'none'
  }
}
