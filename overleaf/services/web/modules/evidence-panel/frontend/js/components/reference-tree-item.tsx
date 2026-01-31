import React, { useCallback } from 'react'
import classNames from 'classnames'
import MaterialIcon from '@/shared/components/material-icon'
import { ReferenceStatusIcons } from './reference-status-icons'
import { ReferenceActionButtons } from './reference-action-buttons'
import {
  ReferencePaper,
  useReferencesPanelContext,
} from '../context/references-panel-context'

interface ReferenceTreeItemProps {
  paper: ReferencePaper
  onIndex?: (paper: ReferencePaper) => void
  onReindex?: (paper: ReferencePaper) => void
  onRemove?: (paper: ReferencePaper) => void
  onUploadPdf?: () => void
  disabled?: boolean
}

export const ReferenceTreeItem: React.FC<ReferenceTreeItemProps> = React.memo(
  function ReferenceTreeItem({
    paper,
    onIndex,
    onReindex,
    onRemove,
    onUploadPdf,
    disabled = false,
  }) {
    const { selectedDocId, setSelectedDocId } = useReferencesPanelContext()

    const documentKey = paper.documentId || paper.citeKey
    const isSelected = selectedDocId === documentKey
    const isProcessing = paper.indexStatus === 'indexing'

    const handleSelect = useCallback(() => {
      setSelectedDocId(isSelected ? null : documentKey)
    }, [setSelectedDocId, isSelected, documentKey])

    const handleIndex = useCallback(() => {
      onIndex?.(paper)
    }, [onIndex, paper])

    const handleReindex = useCallback(() => {
      onReindex?.(paper)
    }, [onReindex, paper])

    const handleRemove = useCallback(() => {
      onRemove?.(paper)
    }, [onRemove, paper])

    const displayName = paper.citeKey

    return (
      <li
        role="treeitem"
        className={classNames('reference-tree-item', { selected: isSelected })}
        aria-selected={isSelected}
        aria-label={displayName}
        tabIndex={0}
      >
        <div className="entity" role="presentation">
          {/* Single row: Name + Status icons + Action buttons */}
          <div
            className="entity-name entity-name-react"
            role="presentation"
            onClick={handleSelect}
          >
            <div className="file-tree-entity-details">
              <MaterialIcon
                type="description"
                className="file-tree-icon unfilled"
              />
              <div className="item-name-button">
                <span title={displayName}>{displayName}</span>
              </div>
              {/* Status icons always visible */}
              <ReferenceStatusIcons
                hasPdf={paper.hasPdf}
                indexStatus={paper.indexStatus}
              />
            </div>
            {/* Action buttons always visible */}
            <ReferenceActionButtons
              paper={paper}
              onIndex={handleIndex}
              onReindex={handleReindex}
              onRemove={handleRemove}
              onUploadPdf={onUploadPdf}
              disabled={disabled || isProcessing}
            />
          </div>
        </div>
      </li>
    )
  }
)

export default ReferenceTreeItem
