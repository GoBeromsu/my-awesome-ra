import React, { useCallback } from 'react'
import classNames from 'classnames'
import MaterialIcon from '@/shared/components/material-icon'
import { ReferenceItemMenu } from './reference-item-menu'
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

    // Display name: citeKey only (clean, like file tree)
    const displayName = paper.citeKey

    // Icon based on status
    const getIcon = () => {
      if (paper.indexStatus === 'indexed') return 'check_circle'
      if (paper.indexStatus === 'indexing') return 'sync'
      if (paper.indexStatus === 'error') return 'error'
      return 'description' // default file icon
    }

    const getIconClass = () => {
      if (paper.indexStatus === 'indexed') return 'icon-indexed'
      if (paper.indexStatus === 'indexing') return 'icon-indexing'
      if (paper.indexStatus === 'error') return 'icon-error'
      return ''
    }

    // File tree pattern: menu only renders when selected (JSX conditional)
    const hasMenu = isSelected

    return (
      <li
        role="treeitem"
        className={classNames({ selected: isSelected })}
        aria-selected={isSelected}
        aria-label={displayName}
        tabIndex={0}
      >
        <div className="entity" role="presentation">
          <div
            className="entity-name entity-name-react"
            role="presentation"
            onClick={handleSelect}
          >
            {/* Icons + Name area (file-tree-entity-details pattern) */}
            <div className="file-tree-entity-details">
              <MaterialIcon
                type={getIcon()}
                className={classNames('file-tree-icon', 'unfilled', getIconClass(), {
                  'icon-spin': isProcessing,
                })}
              />
              <div className="item-name-button">
                <span title={displayName}>{displayName}</span>
              </div>
            </div>

            {/* Menu - only render when selected (file tree pattern) */}
            {hasMenu && (
              <div className="menu-button btn-group">
                <ReferenceItemMenu
                  paper={paper}
                  onIndex={handleIndex}
                  onReindex={handleReindex}
                  onRemove={handleRemove}
                  onUploadPdf={onUploadPdf}
                  disabled={disabled || isProcessing}
                />
              </div>
            )}
          </div>
        </div>
      </li>
    )
  }
)

export default ReferenceTreeItem
