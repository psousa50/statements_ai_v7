import React, { useState, useEffect, useMemo } from 'react'
import { statementClient, StatementResponse } from '../api/StatementClient'
import { ConfirmationModal } from '../components/ConfirmationModal'
import { Toast } from '../components/Toast'
import { ActionIconButton } from '../components/ActionIconButton'
import DeleteIcon from '@mui/icons-material/Delete'
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore'
import './StatementsPage.css'

type SortField = 'filename' | 'account' | 'date_range'
type SortDirection = 'asc' | 'desc'

export const Statements: React.FC = () => {
  const [statements, setStatements] = useState<StatementResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortField, setSortField] = useState<SortField>('date_range')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [secondarySortField, setSecondarySortField] = useState<SortField | null>(null)
  const [secondarySortDirection, setSecondarySortDirection] = useState<SortDirection>('desc')
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
    const ext = filename.split('.').pop()?.toLowerCase()
    return ext ? ext.toUpperCase() : 'FILE'
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSecondarySortField(sortField)
      setSecondarySortDirection(sortDirection)
      setSortField(field)
      setSortDirection(field === 'filename' || field === 'account' ? 'asc' : 'desc')
    }
  }

  const sortedStatements = useMemo(() => {
    const getValue = (statement: StatementResponse, field: SortField): string => {
      switch (field) {
        case 'filename':
          return statement.filename.toLowerCase()
        case 'account':
          return statement.account_name.toLowerCase()
        case 'date_range':
          return statement.date_from || ''
      }
    }

    const compare = (aVal: string, bVal: string, direction: SortDirection): number => {
      if (aVal < bVal) return direction === 'asc' ? -1 : 1
      if (aVal > bVal) return direction === 'asc' ? 1 : -1
      return 0
    }

    return [...statements].sort((a, b) => {
      const primaryResult = compare(getValue(a, sortField), getValue(b, sortField), sortDirection)

      if (primaryResult !== 0 || !secondarySortField) {
        return primaryResult
      }

      return compare(getValue(a, secondarySortField), getValue(b, secondarySortField), secondarySortDirection)
    })
  }, [statements, sortField, sortDirection, secondarySortField, secondarySortDirection])

  const SortableHeader = ({
    field,
    children,
  }: {
    field: SortField
    children: React.ReactNode
  }) => {
    const isActive = sortField === field
    const direction = isActive ? sortDirection : undefined

    return (
      <th className={`sortable-header ${isActive ? 'active' : ''}`} onClick={() => handleSort(field)}>
        <div className="header-content">
          <span>{children}</span>
          <span className="sort-indicator">
            {!isActive && <UnfoldMoreIcon fontSize="small" />}
            {isActive && direction === 'asc' && <ArrowUpwardIcon fontSize="small" />}
            {isActive && direction === 'desc' && <ArrowDownwardIcon fontSize="small" />}
          </span>
        </div>
      </th>
    )
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
                <SortableHeader field="filename">Filename</SortableHeader>
                <SortableHeader field="account">Account</SortableHeader>
                <th>Type</th>
                <th>Transactions</th>
                <SortableHeader field="date_range">Date Range</SortableHeader>
                <th>Uploaded</th>
                <th style={{ textAlign: 'center', width: '80px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedStatements.map((statement) => (
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
