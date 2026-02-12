import { useState, FormEvent, useEffect, useCallback } from 'react'
import { Category, Account, TransactionCreate, Transaction } from '../types/Transaction'
import { CategorySelector } from './CategorySelector'
import { AccountSelector } from './AccountSelector'
import { useApi } from '../api/ApiContext'
import { EnhancementPreviewResponse } from '../api/TransactionClient'
import './TransactionForm.css'

interface TransactionFormProps {
  onSubmit: (transaction: TransactionCreate) => Promise<void>
  categories: Category[]
  accounts: Account[]
  isLoading: boolean
  initialTransaction?: Transaction
}

export const TransactionForm = ({
  onSubmit,
  categories,
  accounts,
  isLoading,
  initialTransaction,
}: TransactionFormProps) => {
  const api = useApi()
  const isEditing = !!initialTransaction
  const [date, setDate] = useState<string>(initialTransaction?.date || '')
  const [description, setDescription] = useState<string>(initialTransaction?.description || '')
  const [amount, setAmount] = useState<string>(initialTransaction?.amount.toString() || '')
  const [accountId, setAccountId] = useState<string>(initialTransaction?.account_id || '')
  const [categoryId, setCategoryId] = useState<string>(initialTransaction?.category_id || '')
  const [counterpartyAccountId, setCounterpartyAccountId] = useState<string>(
    initialTransaction?.counterparty_account_id || ''
  )
  const [preview, setPreview] = useState<EnhancementPreviewResponse | null>(null)

  const fetchPreview = useCallback(async () => {
    if (isEditing || !description.trim()) {
      setPreview(null)
      return
    }

    try {
      const previewResponse = await api.transactions.previewEnhancement({
        description: description.trim(),
        amount: amount ? parseFloat(amount) : undefined,
        transaction_date: date || undefined,
      })
      setPreview(previewResponse)
    } catch (error) {
      setPreview(null)
    }
  }, [description, amount, date, accountId, api.transactions, isEditing])

  useEffect(() => {
    if (isEditing) {
      return
    }

    const timer = setTimeout(() => {
      fetchPreview()
    }, 500)

    return () => clearTimeout(timer)
  }, [fetchPreview, isEditing])

  useEffect(() => {
    if (preview && preview.matched) {
      if (preview.category_id) {
        setCategoryId(preview.category_id)
      }
      if (preview.counterparty_account_id) {
        setCounterpartyAccountId(preview.counterparty_account_id)
      }
    } else if (preview && !preview.matched) {
      setCategoryId('')
      setCounterpartyAccountId('')
    }
  }, [preview])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    if (!date || !description || !amount || !accountId) {
      alert('Please fill in all required fields')
      return
    }

    const amountValue = parseFloat(amount)
    if (isNaN(amountValue)) {
      alert('Amount must be a valid number')
      return
    }

    const transaction: TransactionCreate = {
      date,
      description,
      amount: amountValue,
      account_id: accountId,
      category_id: categoryId || undefined,
      counterparty_account_id: counterpartyAccountId || undefined,
    }

    await onSubmit(transaction)

    if (!isEditing) {
      setDate('')
      setDescription('')
      setAmount('')
      setAccountId('')
      setCategoryId('')
      setCounterpartyAccountId('')
      setPreview(null)
    }
  }

  return (
    <div className="transaction-form">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="date">Date</label>
          <input type="date" id="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <input
            type="text"
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="amount">Amount</label>
          <input
            type="number"
            id="amount"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="account">Account *</label>
          <AccountSelector
            accounts={accounts}
            selectedAccountId={accountId}
            onAccountChange={setAccountId}
            placeholder="Select an account"
          />
        </div>

        <div className="form-group">
          <label htmlFor="counterparty">Counterparty Account (optional)</label>
          <AccountSelector
            accounts={accounts}
            selectedAccountId={counterpartyAccountId}
            onAccountChange={setCounterpartyAccountId}
            placeholder="Select counterparty account for transfers"
          />
        </div>

        <div className="form-group">
          <label htmlFor="category">Category (optional)</label>
          <CategorySelector
            categories={categories}
            selectedCategoryId={categoryId}
            onCategoryChange={(id) => setCategoryId(id || '')}
            placeholder="Select a category"
            allowClear={true}
            multiple={false}
          />
        </div>

        <button type="submit" disabled={isLoading}>
          {isLoading ? (isEditing ? 'Updating...' : 'Adding...') : isEditing ? 'Update Transaction' : 'Add Transaction'}
        </button>
      </form>
    </div>
  )
}
