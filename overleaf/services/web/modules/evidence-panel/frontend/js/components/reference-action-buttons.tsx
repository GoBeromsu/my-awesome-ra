import React, { useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import OLIconButton from '@/shared/components/ol/ol-icon-button'
import OLTooltip from '@/shared/components/ol/ol-tooltip'
import type { ReferencePaper } from '../context/references-panel-context'

interface ReferenceActionButtonsProps {
  paper: ReferencePaper
  onIndex?: () => void
  onReindex?: () => void
  onRemove?: () => void
  onUploadPdf?: () => void
  disabled?: boolean
}

export const ReferenceActionButtons: React.FC<ReferenceActionButtonsProps> = ({
  paper,
  onIndex,
  onReindex,
  onRemove,
  onUploadPdf,
  disabled = false,
}) => {
  const { t } = useTranslation()

  const handleClick = useCallback(
    (handler?: () => void) => (e: React.MouseEvent) => {
      e.stopPropagation()
      handler?.()
    },
    []
  )

  // No PDF - show upload button
  if (!paper.hasPdf) {
    return (
      <div className="reference-actions">
        <OLTooltip
          id="action-upload-pdf"
          description={t('upload_pdf')}
          overlayProps={{ placement: 'top' }}
        >
          <span>
            <OLIconButton
              icon="upload_file"
              accessibilityLabel={t('upload_pdf')}
              variant="secondary"
              size="sm"
              onClick={handleClick(onUploadPdf)}
              disabled={disabled}
            />
          </span>
        </OLTooltip>
      </div>
    )
  }

  // PDF + indexed - show reindex and remove
  if (paper.indexStatus === 'indexed') {
    return (
      <div className="reference-actions">
        <OLTooltip
          id="action-reindex"
          description={t('reindex_document')}
          overlayProps={{ placement: 'top' }}
        >
          <span>
            <OLIconButton
              icon="refresh"
              accessibilityLabel={t('reindex_document')}
              variant="secondary"
              size="sm"
              onClick={handleClick(onReindex)}
              disabled={disabled}
            />
          </span>
        </OLTooltip>
        <OLTooltip
          id="action-remove"
          description={t('remove_from_index')}
          overlayProps={{ placement: 'top' }}
        >
          <span>
            <OLIconButton
              icon="delete"
              accessibilityLabel={t('remove_from_index')}
              variant="danger-ghost"
              size="sm"
              onClick={handleClick(onRemove)}
              disabled={disabled}
            />
          </span>
        </OLTooltip>
      </div>
    )
  }

  // PDF + error - show retry
  if (paper.indexStatus === 'error') {
    return (
      <div className="reference-actions">
        <OLTooltip
          id="action-retry"
          description={t('retry_indexing')}
          overlayProps={{ placement: 'top' }}
        >
          <span>
            <OLIconButton
              icon="refresh"
              accessibilityLabel={t('retry_indexing')}
              variant="secondary"
              size="sm"
              onClick={handleClick(onIndex)}
              disabled={disabled}
            />
          </span>
        </OLTooltip>
      </div>
    )
  }

  // PDF + none (not indexed) - show index button
  if (paper.indexStatus === 'none') {
    return (
      <div className="reference-actions">
        <OLTooltip
          id="action-index"
          description={t('index_document')}
          overlayProps={{ placement: 'top' }}
        >
          <span>
            <OLIconButton
              icon="bolt"
              accessibilityLabel={t('index_document')}
              variant="primary"
              size="sm"
              onClick={handleClick(onIndex)}
              disabled={disabled}
            />
          </span>
        </OLTooltip>
      </div>
    )
  }

  // Indexing - no buttons (processing)
  return null
}

export default ReferenceActionButtons
