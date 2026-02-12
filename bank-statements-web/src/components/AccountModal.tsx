import { useState, useEffect } from 'react'
import { Account } from '../types/Transaction'
import { StyledSelect } from './StyledSelect'

const CURRENCIES = [
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'CHF', symbol: 'CHF', name: 'Swiss Franc' },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen' },
  { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar' },
  { code: 'AUD', symbol: 'A$', name: 'Australian Dollar' },
]

interface AccountModalProps {
  isOpen: boolean
  account: Account | null
  onSave: (name: string, currency: string, accountId?: string) => Promise<void>
  onClose: () => void
}

export const AccountModal = ({ isOpen, account, onSave, onClose }: AccountModalProps) => {
  const [name, setName] = useState('')
  const [currency, setCurrency] = useState('EUR')
  const [saving, setSaving] = useState(false)

  const isEditing = !!account
  const title = isEditing ? 'Edit Account' : 'Create Account'

  useEffect(() => {
    if (isOpen) {
      if (account) {
        setName(account.name)
        setCurrency(account.currency)
      } else {
        setName('')
        setCurrency('EUR')
      }
    }
  }, [isOpen, account])

  if (!isOpen) return null

  const handleSave = async () => {
    const trimmedName = name.trim()
    if (!trimmedName) return

    setSaving(true)
    try {
      await onSave(trimmedName, currency, account?.id)
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
          </div>
          <div className="form-group">
            <label htmlFor="account-currency" className="form-label">
              Currency
            </label>
            <StyledSelect
              id="account-currency"
              value={currency}
              onChange={setCurrency}
              disabled={saving}
              options={CURRENCIES.map((c) => ({
                value: c.code,
                label: `${c.symbol} ${c.code} - ${c.name}`,
              }))}
            />
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
