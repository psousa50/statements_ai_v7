import { useState } from 'react'
import { CategorizationSource } from '../types/TransactionCategorization'
import { Category } from '../types/Transaction'
import { CategorySelector } from './CategorySelector'

interface CreateCategorizationModalProps {
  categories: Category[]
  isOpen: boolean
  onClose: () => void
  onSave: (data: { normalized_description: string; category_id: string; source: CategorizationSource }) => Promise<void>
}

export const CreateCategorizationModal = ({ categories, isOpen, onClose, onSave }: CreateCategorizationModalProps) => {
  const [normalizedDescription, setNormalizedDescription] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!normalizedDescription.trim() || !categoryId) return

    setSaving(true)
    try {
      await onSave({
        normalized_description: normalizedDescription.trim(),
        category_id: categoryId,
        source: CategorizationSource.MANUAL,
      })
      // Reset form
      setNormalizedDescription('')
      setCategoryId('')
    } catch (error) {
      console.error('Failed to create categorization:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleClose = () => {
    // Reset form when closing
    setNormalizedDescription('')
    setCategoryId('')
    setSaving(false)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Create New Categorization Rule</h2>
          <button className="modal-close" onClick={handleClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label htmlFor="description">Normalized Description</label>
            <input
              id="description"
              type="text"
              value={normalizedDescription}
              onChange={(e) => setNormalizedDescription(e.target.value)}
              placeholder="Enter normalized description (e.g., 'amazon.com', 'starbucks')"
              autoFocus
            />
            <div className="form-help-text">
              Enter a normalized description pattern that will match transaction descriptions. This should be a
              simplified, lowercase version of the transaction description.
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="category">Category</label>
            <CategorySelector
              categories={categories}
              selectedCategoryId={categoryId}
              onCategoryChange={(id) => setCategoryId(id || '')}
              placeholder="Select a category"
              allowClear={false}
            />
            <div className="form-help-text">
              Select the category that should be assigned to transactions matching this description.
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="button-secondary" onClick={handleClose} disabled={saving}>
            Cancel
          </button>
          <button
            className="button-primary"
            onClick={handleSave}
            disabled={saving || !normalizedDescription.trim() || !categoryId}
          >
            {saving ? 'Creating...' : 'Create Rule'}
          </button>
        </div>
      </div>
    </div>
  )
}
