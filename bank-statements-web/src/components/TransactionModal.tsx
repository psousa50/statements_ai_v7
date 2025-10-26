import { useState, useEffect } from 'react'
import { Category, Account, TransactionCreate, Transaction } from '../types/Transaction'
import { TransactionForm } from './TransactionForm'

interface TransactionModalProps {
  isOpen: boolean
  categories: Category[]
  accounts: Account[]
  onSave: (transaction: TransactionCreate) => Promise<Transaction | null>
  onClose: () => void
}

export const TransactionModal = ({ isOpen, categories, accounts, onSave, onClose }: TransactionModalProps) => {
  const [saving, setSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      setSuccessMessage(null)
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleSave = async (transaction: TransactionCreate) => {
    setSaving(true)
    try {
      const createdTransaction = await onSave(transaction)

      if (createdTransaction) {
        if (createdTransaction.category_id && !transaction.category_id) {
          const category = categories.find((c) => c.id === createdTransaction.category_id)
          setSuccessMessage(
            `Transaction created! Category auto-assigned by rule: ${category?.name || 'Unknown Category'}`
          )
        } else if (createdTransaction.category_id) {
          setSuccessMessage('Transaction created successfully!')
        } else {
          setSuccessMessage('Transaction created! No matching rule found - you can categorize it manually.')
        }

        setTimeout(() => {
          onClose()
        }, 2000)
      }
    } catch (error) {
      console.error('Failed to create transaction:', error)
      alert('Failed to create transaction. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose()
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose} onKeyDown={handleKeyPress}>
      <div className="modal-content transaction-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add New Transaction</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          {successMessage ? (
            <div className="success-message">
              <div className="success-icon">✓</div>
              <p>{successMessage}</p>
            </div>
          ) : (
            <TransactionForm onSubmit={handleSave} categories={categories} accounts={accounts} isLoading={saving} />
          )}
        </div>
      </div>
    </div>
  )
}
