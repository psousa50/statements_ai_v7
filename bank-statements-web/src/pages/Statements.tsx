import React, { useState, useEffect } from 'react'
import { statementClient, StatementResponse } from '../api/StatementClient'
import { ConfirmationModal } from '../components/ConfirmationModal'
import { Toast } from '../components/Toast'
import { ActionIconButton } from '../components/ActionIconButton'
import DeleteIcon from '@mui/icons-material/Delete'
import './StatementsPage.css'

export const Statements: React.FC = () => {
  const [statements, setStatements] = useState<StatementResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean
    statement: StatementResponse | null
  }>({ isOpen: false, statement: null })
  const [toast, setToast] = useState<{
    message: string
    type: 'success' | 'error' | 'info'
  } | null>(null)

  useEffect(() => {
    loadStatements()
  }, [])

  const loadStatements = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await statementClient.listStatements()
      setStatements(data)
    } catch (err) {
      setError('Failed to load statements')
      console.error('Error loading statements:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteClick = (statement: StatementResponse) => {
    setDeleteModal({ isOpen: true, statement })
  }

  const handleDeleteConfirm = async () => {
    if (!deleteModal.statement) return

    try {
      const response = await statementClient.deleteStatement(deleteModal.statement.id)
      setToast({ message: response.message, type: 'success' })
      setDeleteModal({ isOpen: false, statement: null })
      loadStatements() // Refresh the list
    } catch (err) {
      setToast({ message: 'Failed to delete statement', type: 'error' })
      console.error('Error deleting statement:', err)
    }
  }

  const handleDeleteCancel = () => {
    setDeleteModal({ isOpen: false, statement: null })
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  }

  const formatFileSize = (filename: string) => {
    // Extract file extension for display
    const ext = filename.split('.').pop()?.toLowerCase()
    return ext ? ext.toUpperCase() : 'FILE'
  }

  if (loading) {
    return (
      <div className="statements-page">
        <div className="statements-header">
          <h1>Statements</h1>
        </div>
        <div className="loading">Loading statements...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="statements-page">
        <div className="statements-header">
          <h1>Statements</h1>
        </div>
        <div className="error-message">{error}</div>
      </div>
    )
  }

  return (
    <div className="statements-page">
      <div className="statements-header">
        <h1>Statements</h1>
        <p className="statements-count">
          {statements.length} statement{statements.length !== 1 ? 's' : ''}
        </p>
      </div>

      {statements.length === 0 ? (
        <div className="empty-state">
          <p>No statements found. Upload a statement to get started.</p>
        </div>
      ) : (
        <div className="statements-table-container">
          <table className="statements-table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Account</th>
                <th>Type</th>
                <th>Transactions</th>
                <th>Date Range</th>
                <th>Uploaded</th>
                <th style={{ textAlign: 'center', width: '80px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {statements.map((statement) => (
                <tr key={statement.id}>
                  <td>
                    <div className="filename-cell">
                      <span className="filename">{statement.filename}</span>
                    </div>
                  </td>
                  <td>
                    <span className="account-name">{statement.account_name}</span>
                  </td>
                  <td>
                    <span className="file-type-badge">{formatFileSize(statement.filename)}</span>
                  </td>
                  <td>
                    <span className="transaction-count">{statement.transaction_count || 0}</span>
                  </td>
                  <td>
                    <div className="date-range">
                      {statement.date_from && statement.date_to ? (
                        <>
                          <span>{formatDate(statement.date_from)}</span>
                          <span className="date-separator">→</span>
                          <span>{formatDate(statement.date_to)}</span>
                        </>
                      ) : (
                        '-'
                      )}
                    </div>
                  </td>
                  <td>
                    <span className="upload-date">{formatDate(statement.created_at)}</span>
                  </td>
                  <td>
                    <div className="actions">
                      <ActionIconButton
                        onClick={() => handleDeleteClick(statement)}
                        title="Delete statement"
                        icon={<DeleteIcon fontSize="small" />}
                        color="error"
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmationModal
        isOpen={deleteModal.isOpen}
        title="Delete Statement"
        message={
          deleteModal.statement
            ? `Are you sure you want to delete statement "${deleteModal.statement.filename}"?\n\nThis will also delete ${deleteModal.statement.transaction_count || 0} associated transactions.\n\nThis action cannot be undone.`
            : ''
        }
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
        confirmText="Delete"
        dangerous={true}
      />

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  )
}
