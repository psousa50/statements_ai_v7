import { useState } from 'react'
import './BulkCategorizeModal.css'

interface ReplaceOption {
  categoryName: string
  count: number
}

interface BulkCategorizeModalProps {
  isOpen: boolean
  categoryName: string
  normalizedDescription: string
  similarCount: number
  replaceOption?: ReplaceOption
  onApplyToSimilar: () => Promise<void>
  onReplaceFromCategory?: () => Promise<void>
  onDismiss: () => void
}

export const BulkCategorizeModal = ({
  isOpen,
  categoryName,
  normalizedDescription,
  similarCount,
  replaceOption,
  onApplyToSimilar,
  onReplaceFromCategory,
  onDismiss,
}: BulkCategorizeModalProps) => {
  const [loadingAction, setLoadingAction] = useState<'similar' | 'replace' | null>(null)

  if (!isOpen) return null

  const handleApplyToSimilar = async () => {
    setLoadingAction('similar')
    try {
      await onApplyToSimilar()
    } finally {
      setLoadingAction(null)
    }
  }

  const handleReplaceFromCategory = async () => {
    if (!onReplaceFromCategory) return
    setLoadingAction('replace')
    try {
      await onReplaceFromCategory()
    } finally {
      setLoadingAction(null)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape' && !loadingAction) {
      onDismiss()
    }
  }

  const isLoading = loadingAction !== null

  return (
    <div className="modal-overlay" onClick={isLoading ? undefined : onDismiss}>
      <div
        className="modal-content bulk-categorize-modal"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        <div className="modal-header">
          <h2>Bulk Categorisation Options</h2>
          <button className="modal-close" onClick={onDismiss} disabled={isLoading}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <p className="bulk-categorize-intro">
            You've applied <strong>"{categoryName}"</strong> to this transaction.
          </p>

          {similarCount > 0 && (
            <div className="bulk-option-card">
              <div className="bulk-option-header">
                <span className="bulk-option-icon">📋</span>
                <span className="bulk-option-title">Apply to similar transactions</span>
              </div>
              <p className="bulk-option-description">
                Apply "{categoryName}" to <strong>{similarCount}</strong> other transaction
                {similarCount === 1 ? '' : 's'} with the same description ("{normalizedDescription}").
              </p>
              <p className="bulk-option-hint">
                Use this when transactions from the same merchant should always have this category.
              </p>
              <div className="bulk-option-action">
                <button className="button-primary" onClick={handleApplyToSimilar} disabled={isLoading}>
                  {loadingAction === 'similar' ? 'Applying...' : `Apply to ${similarCount} similar`}
                </button>
              </div>
            </div>
          )}

          {replaceOption && replaceOption.count > 0 && onReplaceFromCategory && (
            <div className="bulk-option-card">
              <div className="bulk-option-header">
                <span className="bulk-option-icon">🔄</span>
                <span className="bulk-option-title">Replace category</span>
              </div>
              <p className="bulk-option-description">
                Move <strong>{replaceOption.count}</strong> transaction
                {replaceOption.count === 1 ? '' : 's'} from "{replaceOption.categoryName}" to "{categoryName}".
              </p>
              <p className="bulk-option-hint">
                Use this to merge categories or fix miscategorised transactions in bulk.
              </p>
              <div className="bulk-option-action">
                <button className="button-secondary" onClick={handleReplaceFromCategory} disabled={isLoading}>
                  {loadingAction === 'replace'
                    ? 'Replacing...'
                    : `Replace ${replaceOption.count} from ${replaceOption.categoryName}`}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="button-secondary" onClick={onDismiss} disabled={isLoading}>
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
