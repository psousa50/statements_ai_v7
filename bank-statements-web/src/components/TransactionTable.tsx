import { format } from 'date-fns'
import { Category, Transaction } from '../types/Transaction'

interface TransactionTableProps {
  transactions: Transaction[]
  categories: Category[]
  loading: boolean
  onCategorize?: (transactionId: string, categoryId?: string) => void
}

export const TransactionTable = ({ transactions, categories, loading, onCategorize }: TransactionTableProps) => {
  if (loading) {
    return <div className="loading">Loading transactions...</div>
  }

  if (transactions.length === 0) {
    return <div className="no-data">No transactions found. Add one to get started!</div>
  }

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy')
    } catch (_error) {
      return dateString
    }
  }

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  // Helper function to get category name by ID
  const getCategoryName = (categoryId?: string) => {
    if (!categoryId) return 'Uncategorized'
    const category = categories.find((c) => c.id === categoryId)
    return category ? category.name : 'Unknown Category'
  }

  // Helper function to get status display text
  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'UNCATEGORIZED':
        return 'Uncategorized'
      case 'categorized':
        return 'Categorized'
      case 'failure':
        return 'Failed'
      default:
        return status
    }
  }

  return (
    <div className="transaction-table">
      <h2>Transactions</h2>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Amount</th>
            <th>Category</th>
            <th>Status</th>
            {onCategorize && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {transactions.map((transaction) => (
            <tr key={transaction.id}>
              <td>{formatDate(transaction.date)}</td>
              <td>{transaction.description}</td>
              <td className={transaction.amount < 0 ? 'negative' : 'positive'}>{formatAmount(transaction.amount)}</td>
              <td>{getCategoryName(transaction.category_id)}</td>
              <td>{getStatusDisplay(transaction.categorization_status)}</td>
              {onCategorize && (
                <td>
                  <select
                    value={transaction.category_id || ''}
                    onChange={(e) => {
                      const categoryId = e.target.value || undefined
                      onCategorize(transaction.id, categoryId)
                    }}
                  >
                    <option value="">-- Select Category --</option>
                    {categories.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
