import { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import AddIcon from '@mui/icons-material/Add'
import { useTags } from '../services/hooks/useTags'
import { TagModal } from '../components/TagModal'
import { ConfirmationModal } from '../components/ConfirmationModal'
import { Toast, ToastProps } from '../components/Toast'
import { ActionIconButton } from '../components/ActionIconButton'
import { TagWithUsage } from '../types/Transaction'
import './TagsPage.css'

const pluraliseTransactions = (count: number) => `${count} transaction${count === 1 ? '' : 's'}`

export const TagsPage = () => {
  const [editingTag, setEditingTag] = useState<TagWithUsage | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<TagWithUsage | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [toast, setToast] = useState<Omit<ToastProps, 'onClose'> | null>(null)

  const { tags, loading, error, createTag, renameTag, deleteTag, isSaving } = useTags()

  const filteredTags = tags.filter((tag) => tag.name.toLowerCase().includes(searchTerm.toLowerCase()))
  const taggedTransactions = tags.reduce((sum, tag) => sum + tag.transaction_count, 0)
  const unusedCount = tags.filter((tag) => tag.transaction_count === 0).length

  const handleSaveTag = useCallback(
    async (name: string, tagId?: string) => {
      if (tagId) {
        const renamed = await renameTag(tagId, name)
        if (renamed) {
          setToast({ message: `Tag renamed to "${name}"`, type: 'success' })
          setEditingTag(null)
        }
        return
      }

      const created = await createTag(name)
      if (created) {
        setToast({ message: `Tag "${name}" created`, type: 'success' })
        setIsCreating(false)
      }
    },
    [createTag, renameTag]
  )

  const handleConfirmDelete = useCallback(async () => {
    if (!confirmDelete) return

    const deleted = await deleteTag(confirmDelete.id)
    if (deleted) {
      setToast({ message: `Tag "${confirmDelete.name}" deleted`, type: 'success' })
    }
    setConfirmDelete(null)
  }, [confirmDelete, deleteTag])

  const handleCloseModal = useCallback(() => {
    setEditingTag(null)
    setIsCreating(false)
  }, [])

  const deleteMessage = confirmDelete
    ? confirmDelete.transaction_count === 0
      ? `Are you sure you want to delete "${confirmDelete.name}"? This action cannot be undone.`
      : `"${confirmDelete.name}" is used by ${pluraliseTransactions(confirmDelete.transaction_count)}. Deleting it removes the tag from all of them. This action cannot be undone.`
    : ''

  return (
    <div className="tags-page">
      <header className="page-header">
        <h1>Tag Management</h1>
        <p className="page-description">Create, rename, and remove the tags you apply to transactions</p>
      </header>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-value">{tags.length}</div>
          <div className="card-label">Tags</div>
        </div>
        <div className="summary-card">
          <div className="card-value">{taggedTransactions}</div>
          <div className="card-label">Tag assignments</div>
        </div>
        <div className="summary-card">
          <div className="card-value">{unusedCount}</div>
          <div className="card-label">Unused tags</div>
        </div>
      </div>

      <div className="filters-top">
        <div className="filter-section">
          <div className="search-container">
            <input
              type="text"
              placeholder="Search tags..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          <div className="action-buttons">
            <Button
              onClick={() => setIsCreating(true)}
              variant="contained"
              disabled={loading}
              startIcon={<AddIcon />}
              sx={{ textTransform: 'none' }}
            >
              Create Tag
            </Button>
          </div>
        </div>
      </div>

      <div className="tags-content">
        <div className="tags-header">
          <h2>Tags</h2>
          {!loading && (
            <span className="tag-count">
              {searchTerm ? `${filteredTags.length} of ${tags.length}` : tags.length} tags
            </span>
          )}
        </div>

        <div className="tags-table-container">
          {loading ? (
            <div className="loading-message">Loading tags...</div>
          ) : filteredTags.length === 0 ? (
            <div className="empty-message">
              {searchTerm
                ? 'No tags found matching your search.'
                : 'No tags yet. Create one here, or add tags directly to a transaction.'}
            </div>
          ) : (
            <table className="tags-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th style={{ width: '180px' }}>Transactions</th>
                  <th style={{ textAlign: 'center', width: '120px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTags.map((tag) => (
                  <tr key={tag.id}>
                    <td className="tag-name">
                      <span className="tag-chip">{tag.name}</span>
                    </td>
                    <td>
                      {tag.transaction_count === 0 ? (
                        <span className="tag-usage-empty">Unused</span>
                      ) : (
                        <Link className="tag-usage-link" to={`/transactions?tag_ids=${tag.id}`}>
                          {pluraliseTransactions(tag.transaction_count)}
                        </Link>
                      )}
                    </td>
                    <td className="tag-actions">
                      <ActionIconButton
                        onClick={() => setEditingTag(tag)}
                        title="Rename tag"
                        icon={<EditIcon fontSize="small" />}
                        color="primary"
                      />
                      <ActionIconButton
                        onClick={() => setConfirmDelete(tag)}
                        title="Delete tag"
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

      <TagModal
        isOpen={isCreating || !!editingTag}
        tag={editingTag}
        onSave={handleSaveTag}
        onClose={handleCloseModal}
      />

      <ConfirmationModal
        isOpen={!!confirmDelete}
        title="Delete Tag"
        message={deleteMessage}
        confirmText={isSaving ? 'Deleting...' : 'Delete'}
        cancelText="Cancel"
        onConfirm={handleConfirmDelete}
        onCancel={() => setConfirmDelete(null)}
        dangerous={true}
      />

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  )
}
