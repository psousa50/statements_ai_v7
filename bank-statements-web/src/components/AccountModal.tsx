import { useState, useEffect } from 'react'
import { Account } from '../types/Transaction'

interface AccountModalProps {
  isOpen: boolean
  account: Account | null // null for creating, Account object for editing
  onSave: (name: string, accountId?: string) => Promise<void>
  onClose: () => void
}

export const AccountModal = ({ isOpen, account, onSave, onClose }: AccountModalProps) => {
  const [name, setName] = useState('')
  const [saving, setSaving] = useState(false)

  const isEditing = !!account
  const title = isEditing ? 'Edit Account' : 'Create Account'

  useEffect(() => {
    if (isOpen) {
      if (account) {
        // Editing existing account
        setName(account.name)
      } else {
        // Creating new account
        setName('')
      }
    }
  }, [isOpen, account])

  if (!isOpen) return null

  const handleSave = async () => {
    const trimmedName = name.trim()
    if (!trimmedName) return

    setSaving(true)
    try {
      await onSave(trimmedName, account?.id)
      // Don't close modal here - let parent component handle it after successful save
    } catch (error) {
      console.error('Failed to save account:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !saving && name.trim()) {
      handleSave()
    } else if (e.key === 'Escape') {
      onClose()
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label htmlFor="account-name" className="form-label">
              Account Name *
            </label>
            <input
              id="account-name"
              type="text"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Enter account name"
              disabled={saving}
              autoFocus
            />
            <div className="form-help">
              Enter a unique name for the account (e.g., "Checking Account", "Savings Account")
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="button-secondary" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button className="button-primary" onClick={handleSave} disabled={saving || !name.trim()}>
            {saving ? 'Saving...' : isEditing ? 'Update Account' : 'Create Account'}
          </button>
        </div>
      </div>
    </div>
  )
}
