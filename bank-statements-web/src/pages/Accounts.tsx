import { useState, useCallback, useRef } from 'react'
import { useAccounts } from '../services/hooks/useAccounts'
import { AccountModal } from '../components/AccountModal'
import { InitialBalanceModal } from '../components/InitialBalanceModal'
import { ConfirmationModal } from '../components/ConfirmationModal'
import { Toast, ToastProps } from '../components/Toast'
import { Account } from '../types/Transaction'
import { ActionIconButton } from '../components/ActionIconButton'
import { formatCurrency } from '../utils/format'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import AddIcon from '@mui/icons-material/Add'
import DownloadIcon from '@mui/icons-material/Download'
import UploadIcon from '@mui/icons-material/Upload'
import { Button } from '@mui/material'
import './AccountsPage.css'

export const AccountsPage = () => {
  const [editingAccount, setEditingAccount] = useState<Account | null>(null)
  const [editingInitialBalance, setEditingInitialBalance] = useState<Account | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [toast, setToast] = useState<Omit<ToastProps, 'onClose'> | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<Account | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const {
    accounts,
    loading,
    error,
    addAccount,
    updateAccount,
    deleteAccount,
    setInitialBalance,
    deleteInitialBalance,
    exportAccounts,
    uploadAccounts,
  } = useAccounts()

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
    async (name: string, currency: string, accountId?: string) => {
      try {
        if (accountId) {
          const updatedAccount = await updateAccount(accountId, name, currency)
          if (updatedAccount) {
            setToast({
              message: `Account "${name}" updated successfully`,
              type: 'success',
            })
            setEditingAccount(null)
          }
        } else {
          const newAccount = await addAccount(name, currency)
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

  const handleEditInitialBalance = useCallback((account: Account) => {
    setEditingInitialBalance(account)
  }, [])

  const handleSaveInitialBalance = useCallback(
    async (accountId: string, balanceDate: string, balanceAmount: number) => {
      const result = await setInitialBalance(accountId, balanceDate, balanceAmount)
      if (result) {
        setToast({
          message: 'Initial balance updated successfully',
          type: 'success',
        })
      } else {
        setToast({
          message: 'Failed to update initial balance. Please try again.',
          type: 'error',
        })
      }
      return result
    },
    [setInitialBalance]
  )

  const handleDeleteInitialBalance = useCallback(
    async (accountId: string) => {
      const success = await deleteInitialBalance(accountId)
      if (success) {
        setToast({
          message: 'Initial balance removed successfully',
          type: 'success',
        })
      } else {
        setToast({
          message: 'Failed to remove initial balance. Please try again.',
          type: 'error',
        })
      }
      return success
    },
    [deleteInitialBalance]
  )

  const handleCloseInitialBalanceModal = useCallback(() => {
    setEditingInitialBalance(null)
  }, [])

  const handleExportAccounts = useCallback(async () => {
    const success = await exportAccounts()
    if (success) {
      setToast({ message: 'Accounts exported successfully', type: 'success' })
    } else {
      setToast({ message: 'Failed to export accounts', type: 'error' })
    }
  }, [exportAccounts])

  const handleUploadClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file) return

      const result = await uploadAccounts(file)
      if (result) {
        setToast({
          message: `Uploaded ${result.total} accounts (${result.created} created, ${result.updated} existing)`,
          type: 'success',
        })
      } else {
        setToast({ message: 'Failed to upload accounts', type: 'error' })
      }

      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    },
    [uploadAccounts]
  )

  const formatInitialBalance = (account: Account): string => {
    if (!account.initial_balance) return '-'
    const amount = formatCurrency(account.initial_balance.balance_amount, account.currency)
    const date = new Date(account.initial_balance.balance_date).toLocaleDateString('en-GB')
    return `${amount} as of ${date}`
  }

  return (
    <div className="accounts-page">
      <header className="page-header">
        <h1>Account Management</h1>
        <p className="page-description">Create, edit, and manage your bank accounts</p>
      </header>

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
            <Button
              onClick={handleExportAccounts}
              variant="outlined"
              disabled={loading}
              startIcon={<DownloadIcon />}
              sx={{ textTransform: 'none' }}
            >
              Download
            </Button>
            <Button
              onClick={handleUploadClick}
              variant="outlined"
              disabled={loading}
              startIcon={<UploadIcon />}
              sx={{ textTransform: 'none' }}
            >
              Upload
            </Button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".csv"
              style={{ display: 'none' }}
            />
            <Button
              onClick={handleCreateAccount}
              variant="contained"
              disabled={loading}
              startIcon={<AddIcon />}
              sx={{ textTransform: 'none' }}
            >
              Create Account
            </Button>
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
              {searchTerm
                ? 'No accounts found matching your search.'
                : 'No accounts found. Create your first account to get started.'}
            </div>
          ) : (
            <table className="accounts-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th style={{ width: '80px' }}>Currency</th>
                  <th className="initial-balance-header">Initial Balance</th>
                  <th style={{ textAlign: 'center', width: '120px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredAccounts.map((account) => (
                  <tr key={account.id}>
                    <td className="account-name">{account.name}</td>
                    <td>{account.currency}</td>
                    <td
                      className="initial-balance-cell"
                      onClick={() => handleEditInitialBalance(account)}
                      title="Click to edit initial balance"
                    >
                      {formatInitialBalance(account)}
                    </td>
                    <td className="account-actions">
                      <ActionIconButton
                        onClick={() => handleEditAccount(account)}
                        title="Edit account"
                        icon={<EditIcon fontSize="small" />}
                        color="primary"
                      />
                      <ActionIconButton
                        onClick={() => handleDeleteAccount(account)}
                        title="Delete account"
                        icon={<DeleteIcon fontSize="small" />}
                        color="error"
                      />
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

      <InitialBalanceModal
        open={!!editingInitialBalance}
        account={editingInitialBalance}
        onSave={handleSaveInitialBalance}
        onDelete={handleDeleteInitialBalance}
        onClose={handleCloseInitialBalanceModal}
      />

      {toast && <Toast message={toast.message} type={toast.type} onClose={handleCloseToast} />}
    </div>
  )
}
