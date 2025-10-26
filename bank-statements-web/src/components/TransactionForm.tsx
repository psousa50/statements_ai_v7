import { useState, FormEvent, useEffect, useCallback } from 'react'
import { Category, Account, TransactionCreate } from '../types/Transaction'
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
}

export const TransactionForm = ({ onSubmit, categories, accounts, isLoading }: TransactionFormProps) => {
  const api = useApi()
  const [date, setDate] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [amount, setAmount] = useState<string>('')
  const [accountId, setAccountId] = useState<string>('')
  const [categoryId, setCategoryId] = useState<string>('')
  const [counterpartyAccountId, setCounterpartyAccountId] = useState<string>('')
  const [preview, setPreview] = useState<EnhancementPreviewResponse | null>(null)

  const fetchPreview = useCallback(async () => {
    if (!description.trim()) {
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
  }, [description, amount, date, accountId, api.transactions])

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchPreview()
    }, 500)

    return () => clearTimeout(timer)
  }, [fetchPreview])

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

    setDate('')
    setDescription('')
    setAmount('')
    setAccountId('')
    setCategoryId('')
    setCounterpartyAccountId('')
    setPreview(null)
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
            required={true}
          />
        </div>

        <div className="form-group">
          <label htmlFor="counterparty">Counterparty Account (optional)</label>
          <AccountSelector
            accounts={accounts}
            selectedAccountId={counterpartyAccountId}
            onAccountChange={setCounterpartyAccountId}
            placeholder="Select counterparty account for transfers"
            required={false}
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
          {isLoading ? 'Adding...' : 'Add Transaction'}
        </button>
      </form>
    </div>
  )
}
