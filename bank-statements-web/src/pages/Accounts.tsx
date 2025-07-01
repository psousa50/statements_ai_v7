import { useState, useCallback } from 'react'
import { useAccounts } from '../services/hooks/useAccounts'
import { AccountModal } from '../components/AccountModal'
import { ConfirmationModal } from '../components/ConfirmationModal'
import { Toast, ToastProps } from '../components/Toast'
import { Account } from '../types/Transaction'
import './AccountsPage.css'

export const AccountsPage = () => {
  const [editingAccount, setEditingAccount] = useState<Account | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [toast, setToast] = useState<Omit<ToastProps, 'onClose'> | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<Account | null>(null)

  const { accounts, loading, error, fetchAccounts, addAccount, updateAccount, deleteAccount } = useAccounts()

  // Filter and sort accounts based on search term
  const filteredAccounts = accounts
    .filter((account) => account.name.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => a.name.localeCompare(b.name))

  const handleCreateAccount = useCallback(() => {
    setIsCreating(true)
  }, [])

  const handleEditAccount = useCallback((account: Account) => {
    setEditingAccount(account)
  }, [])

  const handleDeleteAccount = useCallback((account: Account) => {
    setConfirmDelete(account)
  }, [])

  const handleConfirmDelete = useCallback(async () => {
    if (!confirmDelete) return

    const success = await deleteAccount(confirmDelete.id)
    if (success) {
      setToast({
        message: `Account "${confirmDelete.name}" deleted successfully`,
        type: 'success',
      })
    } else {
      setToast({
        message: `Failed to delete account "${confirmDelete.name}". It may be in use by transactions.`,
        type: 'error',
      })
    }

    setConfirmDelete(null)
  }, [confirmDelete, deleteAccount])

  const handleCancelDelete = useCallback(() => {
    setConfirmDelete(null)
  }, [])

  const handleSaveAccount = useCallback(
    async (name: string, accountId?: string) => {
      try {
        if (accountId) {
          // Updating existing account
          const updatedAccount = await updateAccount(accountId, name)
          if (updatedAccount) {
            setToast({
              message: `Account "${name}" updated successfully`,
              type: 'success',
            })
            setEditingAccount(null)
          }
        } else {
          // Creating new account
          const newAccount = await addAccount(name)
          if (newAccount) {
            setToast({
              message: `Account "${name}" created successfully`,
              type: 'success',
            })
            setIsCreating(false)
          }
        }
      } catch (error) {
        console.error('Failed to save account:', error)
        setToast({
          message: 'Failed to save account. Please try again.',
          type: 'error',
        })
      }
    },
    [addAccount, updateAccount]
  )

  const handleCloseModal = useCallback(() => {
    setEditingAccount(null)
    setIsCreating(false)
  }, [])

  const handleCloseToast = useCallback(() => {
    setToast(null)
  }, [])

  return (
    <div className="accounts-page">
      <header className="page-header">
        <h1>Account Management</h1>
        <p className="page-description">Create, edit, and manage your bank accounts</p>
      </header>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-value">{accounts.length}</div>
          <div className="card-label">Total Accounts</div>
        </div>
        <div className="summary-card">
          <div className="card-value">{filteredAccounts.length}</div>
          <div className="card-label">Filtered Accounts</div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="filters-top">
        <div className="filter-section">
          <div className="search-container">
            <input
              type="text"
              placeholder="Search accounts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          <div className="action-buttons">
            <button onClick={handleCreateAccount} className="button-primary" disabled={loading}>
              + Create Account
            </button>
            <button
              onClick={() => fetchAccounts()}
              className="button-secondary"
              disabled={loading}
              title="Refresh accounts"
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="accounts-content">
        <div className="accounts-header">
          <h2>Accounts</h2>
          {!loading && (
            <span className="account-count">
              {searchTerm ? `${filteredAccounts.length} of ${accounts.length}` : accounts.length} accounts
            </span>
          )}
        </div>

        <div className="accounts-table-container">
          {loading ? (
            <div className="loading-message">Loading accounts...</div>
          ) : filteredAccounts.length === 0 ? (
            <div className="empty-message">
              {searchTerm ? 'No accounts found matching your search.' : 'No accounts found. Create your first account to get started.'}
            </div>
          ) : (
            <table className="accounts-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>ID</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredAccounts.map((account) => (
                  <tr key={account.id}>
                    <td className="account-name">{account.name}</td>
                    <td className="account-id">{account.id}</td>
                    <td className="account-actions">
                      <button
                        onClick={() => handleEditAccount(account)}
                        className="button-secondary"
                        title="Edit account"
                      >
                        ✏️ Edit
                      </button>
                      <button
                        onClick={() => handleDeleteAccount(account)}
                        className="button-danger"
                        title="Delete account"
                      >
                        🗑️ Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <AccountModal
        isOpen={isCreating || !!editingAccount}
        account={editingAccount}
        onSave={handleSaveAccount}
        onClose={handleCloseModal}
      />

      <ConfirmationModal
        isOpen={!!confirmDelete}
        title="Delete Account"
        message={`Are you sure you want to delete "${confirmDelete?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        dangerous={true}
      />

      {toast && <Toast message={toast.message} type={toast.type} onClose={handleCloseToast} />}
    </div>
  )
}