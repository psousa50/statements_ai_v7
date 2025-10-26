import { useEffect } from 'react'

export interface ToastProps {
  message: string
  type?: 'success' | 'error' | 'info'
  duration?: number
  onClose: () => void
  onUndo?: () => void
}

export const Toast = ({ message, type = 'success', duration = 4000, onClose, onUndo }: ToastProps) => {
  useEffect(() => {
    const timer = setTimeout(onClose, duration)
    return () => clearTimeout(timer)
  }, [duration, onClose])

  const handleUndo = () => {
    onUndo?.()
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
      {onUndo && (
        <div className="toast-actions">
          <button className="toast-undo" onClick={handleUndo}>
            Undo
          </button>
        </div>
      )}
    </div>
  )
}
