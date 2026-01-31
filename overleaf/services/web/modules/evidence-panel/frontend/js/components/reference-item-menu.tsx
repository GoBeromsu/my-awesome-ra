import React, { useCallback, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import MaterialIcon from '@/shared/components/material-icon'
import {
  Dropdown,
  DropdownToggle,
  DropdownMenu,
  DropdownItem,
  DropdownDivider,
} from '@/shared/components/dropdown/dropdown-menu'
import { ReferencePaper } from '../context/references-panel-context'

interface ReferenceItemMenuProps {
  paper: ReferencePaper
  onIndex?: () => void
  onReindex?: () => void
  onRemove?: () => void
  onUploadPdf?: () => void
  disabled?: boolean
}

export const ReferenceItemMenu: React.FC<ReferenceItemMenuProps> = React.memo(
  function ReferenceItemMenu({
    paper,
    onIndex,
    onReindex,
    onRemove,
    onUploadPdf,
    disabled = false,
  }) {
    const { t } = useTranslation()
    const menuButtonRef = useRef<HTMLButtonElement>(null)
    const [showMenu, setShowMenu] = useState(false)

    const handleToggle = useCallback(
      (nextShow: boolean) => {
        if (!disabled) {
          setShowMenu(nextShow)
        }
      },
      [disabled]
    )

    const handleIndex = useCallback(
      (e: React.MouseEvent) => {
        e.stopPropagation()
        setShowMenu(false)
        onIndex?.()
      },
      [onIndex]
    )

    const handleReindex = useCallback(
      (e: React.MouseEvent) => {
        e.stopPropagation()
        setShowMenu(false)
        onReindex?.()
      },
      [onReindex]
    )

    const handleRemove = useCallback(
      (e: React.MouseEvent) => {
        e.stopPropagation()
        setShowMenu(false)
        onRemove?.()
      },
      [onRemove]
    )

    const handleUploadPdf = useCallback(
      (e: React.MouseEvent) => {
        e.stopPropagation()
        setShowMenu(false)
        onUploadPdf?.()
      },
      [onUploadPdf]
    )

    const isProcessing = paper.indexStatus === 'indexing'

    // No wrapper div - parent provides "menu-button btn-group" wrapper
    return (
      <Dropdown show={showMenu} onToggle={handleToggle} align="end">
        <DropdownToggle
          as="button"
          className="entity-menu-toggle btn btn-sm"
          ref={menuButtonRef}
          disabled={disabled || isProcessing}
          aria-haspopup="true"
          aria-label={t('open_action_menu', { name: paper.title || paper.citeKey })}
        >
          <MaterialIcon type="more_vert" />
        </DropdownToggle>
        <DropdownMenu>
          <ReferenceMenuItems
            paper={paper}
            onIndex={handleIndex}
            onReindex={handleReindex}
            onRemove={handleRemove}
            onUploadPdf={handleUploadPdf}
            disabled={disabled}
          />
        </DropdownMenu>
      </Dropdown>
    )
  }
)

interface ReferenceMenuItemsProps {
  paper: ReferencePaper
  onIndex?: (e: React.MouseEvent) => void
  onReindex?: (e: React.MouseEvent) => void
  onRemove?: (e: React.MouseEvent) => void
  onUploadPdf?: (e: React.MouseEvent) => void
  disabled?: boolean
}

const ReferenceMenuItems: React.FC<ReferenceMenuItemsProps> = ({
  paper,
  onIndex,
  onReindex,
  onRemove,
  onUploadPdf,
  disabled = false,
}) => {
  const { t } = useTranslation()

  return (
    <>
      {/* Upload PDF if no PDF available */}
      {!paper.hasPdf && onUploadPdf && (
        <li role="none">
          <DropdownItem
            leadingIcon="upload_file"
            onClick={onUploadPdf}
            disabled={disabled}
          >
            {t('upload_pdf')}
          </DropdownItem>
        </li>
      )}

      {/* Index if not indexed and has PDF */}
      {paper.indexStatus === 'none' && paper.hasPdf && onIndex && (
        <li role="none">
          <DropdownItem
            leadingIcon="add_circle_outline"
            onClick={onIndex}
            disabled={disabled}
          >
            {t('index_document')}
          </DropdownItem>
        </li>
      )}

      {/* Reindex if already indexed */}
      {paper.indexStatus === 'indexed' && onReindex && (
        <li role="none">
          <DropdownItem
            leadingIcon="refresh"
            onClick={onReindex}
            disabled={disabled}
          >
            {t('reindex_document')}
          </DropdownItem>
        </li>
      )}

      {/* Retry if error */}
      {paper.indexStatus === 'error' && paper.hasPdf && onIndex && (
        <li role="none">
          <DropdownItem
            leadingIcon="refresh"
            onClick={onIndex}
            disabled={disabled}
          >
            {t('retry_indexing')}
          </DropdownItem>
        </li>
      )}

      {/* Remove from index (only if indexed) */}
      {paper.indexStatus === 'indexed' && onRemove && (
        <>
          <DropdownDivider />
          <li role="none">
            <DropdownItem
              leadingIcon="delete"
              onClick={onRemove}
              disabled={disabled}
              className="dropdown-item--danger"
            >
              {t('remove_from_index')}
            </DropdownItem>
          </li>
        </>
      )}
    </>
  )
}

export default ReferenceItemMenu
