import { useEffect, useCallback } from 'react'

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
  actions?: ToastAction[]
}

export const Toast = ({ message, type = 'success', duration = 4000, onClose, onUndo, action, actions }: ToastProps) => {
  useEffect(() => {
    const timer = setTimeout(onClose, duration)
    return () => clearTimeout(timer)
  }, [duration, onClose])

  const handleUndo = () => {
    onUndo?.()
    onClose()
  }

  const handleAction = useCallback(
    (actionToRun: ToastAction) => {
      actionToRun.onClick()
      onClose()
    },
    [onClose]
  )

  const allActions = actions || (action ? [action] : [])

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
      {(onUndo || allActions.length > 0) && (
        <div className="toast-actions">
          {onUndo && (
            <button className="toast-undo" onClick={handleUndo}>
              Undo
            </button>
          )}
          {allActions.map((a, index) => (
            <button key={index} className="toast-action" onClick={() => handleAction(a)}>
              {a.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
