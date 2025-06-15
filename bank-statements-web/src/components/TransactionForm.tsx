import { useState, FormEvent } from 'react'
import { Category, TransactionCreate } from '../types/Transaction'
import { CategorySelector } from './CategorySelector'

interface TransactionFormProps {
  onSubmit: (transaction: TransactionCreate) => Promise<void>
  categories: Category[]
  isLoading: boolean
}

export const TransactionForm = ({ onSubmit, categories, isLoading }: TransactionFormProps) => {
  const [date, setDate] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [amount, setAmount] = useState<string>('')
  const [categoryId, setCategoryId] = useState<string>('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    if (!date || !description || !amount) {
      alert('Please fill in all fields')
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
      category_id: categoryId || undefined,
    }

    await onSubmit(transaction)

    // Reset form
    setDate('')
    setDescription('')
    setAmount('')
    setCategoryId('')
  }

  return (
    <div className="transaction-form">
      <h2>Add Transaction</h2>
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
