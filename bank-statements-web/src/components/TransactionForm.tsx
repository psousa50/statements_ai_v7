import { useState, FormEvent } from 'react'
import { Category, Account, TransactionCreate } from '../types/Transaction'
import { CategorySelector } from './CategorySelector'
import { AccountSelector } from './AccountSelector'

interface TransactionFormProps {
  onSubmit: (transaction: TransactionCreate) => Promise<void>
  categories: Category[]
  accounts: Account[]
  isLoading: boolean
}

export const TransactionForm = ({ onSubmit, categories, accounts, isLoading }: TransactionFormProps) => {
  const [date, setDate] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [amount, setAmount] = useState<string>('')
  const [accountId, setAccountId] = useState<string>('')
  const [categoryId, setCategoryId] = useState<string>('')
  const [counterpartyAccountId, setCounterpartyAccountId] = useState<string>('')

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
