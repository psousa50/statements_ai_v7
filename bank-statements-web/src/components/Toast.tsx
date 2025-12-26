import { useEffect } from 'react'

export interface ToastAction {
  label: string
  onClick: () => void
}

export interface ToastProps {
  message: string
  type?: 'success' | 'error' | 'info'
  duration?: number
  onClose: () => void
  onUndo?: () => void
  action?: ToastAction
}

export const Toast = ({ message, type = 'success', duration = 4000, onClose, onUndo, action }: ToastProps) => {
  useEffect(() => {
    const timer = setTimeout(onClose, duration)
    return () => clearTimeout(timer)
  }, [duration, onClose])

  const handleUndo = () => {
    onUndo?.()
    onClose()
  }

  const handleAction = () => {
    action?.onClick()
    onClose()
  }

  return (
    <div className={`toast toast-${type}`}>
      <div className="toast-header">
        <span className="toast-icon">
          {type === 'success' && '✓'}
          {type === 'error' && '✗'}
          {type === 'info' && 'ℹ'}
        </span>
        <span className="toast-message">{message}</span>
        <button className="toast-close" onClick={onClose}>
          ×
        </button>
      </div>
      {(onUndo || action) && (
        <div className="toast-actions">
          {onUndo && (
            <button className="toast-undo" onClick={handleUndo}>
              Undo
            </button>
          )}
          {action && (
            <button className="toast-action" onClick={handleAction}>
              {action.label}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
