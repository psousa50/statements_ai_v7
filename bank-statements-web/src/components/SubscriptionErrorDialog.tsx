import { ApiError } from '../types/ApiError'

interface SubscriptionErrorDialogProps {
  error: ApiError
  onClose: () => void
}

export const SubscriptionErrorDialog = ({ error, onClose }: SubscriptionErrorDialogProps) => {
  const details = error.details as { feature?: string; limit?: number; used?: number }

  const handleUpgrade = () => {
    onClose()
    window.location.href = '/settings/billing'
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose()
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} onKeyDown={handleKeyPress}>
        <div className="modal-header">
          <h2>Upgrade Required</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <p>{error.message}</p>
          {details.feature && (
            <div className="subscription-details">
              <p>
                <strong>Feature:</strong> {formatFeatureName(details.feature)}
              </p>
              {details.limit !== undefined && details.used !== undefined && (
                <p>
                  <strong>Usage:</strong> {details.used} / {details.limit}
                </p>
              )}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="button-secondary" onClick={onClose}>
            Close
          </button>
          <button className="button-primary" onClick={handleUpgrade} autoFocus>
            View Plans
          </button>
        </div>
      </div>
    </div>
  )
}

function formatFeatureName(feature: string): string {
  return feature
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
