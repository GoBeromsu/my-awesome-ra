import { memo } from 'react'
import { useTranslation } from 'react-i18next'
import MaterialIcon from '@/shared/components/material-icon'
import OLTooltip from '@/shared/components/ol/ol-tooltip'
import OLButton from '@/shared/components/ol/ol-button'

interface EvidenceToggleButtonProps {
  showEvidence: boolean
  onToggle: () => void
  tooltipId?: string
}

function EvidenceToggleButton({
  showEvidence,
  onToggle,
  tooltipId = 'toggle-evidence-tooltip',
}: EvidenceToggleButtonProps): JSX.Element {
  const { t } = useTranslation()
  const description = showEvidence ? t('show_pdf') : t('show_evidence')
  const iconType = showEvidence ? 'picture_as_pdf' : 'format_quote'

  return (
    <OLTooltip
      id={tooltipId}
      description={description}
      overlayProps={{ placement: 'bottom' }}
    >
      <OLButton
        variant="link"
        active={showEvidence}
        className="pdf-toolbar-btn toolbar-item"
        onClick={onToggle}
        aria-pressed={showEvidence}
        aria-label={description}
      >
        <MaterialIcon type={iconType} />
      </OLButton>
    </OLTooltip>
  )
}

export default memo(EvidenceToggleButton)
