import { useState, useEffect } from 'react'
import { TransactionCategorization, CategorizationSource } from '../types/TransactionCategorization'
import { Category } from '../types/Transaction'
import { CategorySelector } from './CategorySelector'

interface EditCategorizationModalProps {
  categorization: TransactionCategorization | null
  categories: Category[]
  isOpen: boolean
  onClose: () => void
  onSave: (
    id: string,
    updates: {
      normalized_description: string
      category_id: string
      source: CategorizationSource
    },
    applyToAllSame: boolean
  ) => Promise<void>
}

export const EditCategorizationModal = ({
  categorization,
  categories,
  isOpen,
  onClose,
  onSave,
}: EditCategorizationModalProps) => {
  const [normalizedDescription, setNormalizedDescription] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [applyToAllSame, setApplyToAllSame] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (categorization) {
      setNormalizedDescription(categorization.normalized_description)
      setCategoryId(categorization.category_id)
      setApplyToAllSame(false)
    }
  }, [categorization])

  if (!isOpen || !categorization) return null

  const handleSave = async () => {
    if (!normalizedDescription.trim() || !categoryId) return

    setSaving(true)
    try {
      await onSave(
        categorization.id,
        {
          normalized_description: normalizedDescription.trim(),
          category_id: categoryId,
          source: CategorizationSource.MANUAL,
        },
        applyToAllSame
      )
      // Don't call onClose() here - let the parent component handle it
    } catch (error) {
      console.error('Failed to save categorization:', error)
    } finally {
      setSaving(false)
    }
  }

  const categoryChanged = categoryId !== categorization.category_id

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Edit Categorization Rule</h2>
          <button className="modal-close" onClick={onClose}>
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
              placeholder="Enter normalized description"
            />
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
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input 
                type="checkbox" 
                checked={applyToAllSame} 
                onChange={(e) => setApplyToAllSame(e.target.checked)}
                disabled={!categoryChanged}
              />
              <div className="checkbox-content">
                <span className="checkbox-text">
                  Apply new category to all matching transactions
                </span>
                <span className="checkbox-description">
                  {categoryChanged 
                    ? `This will update the category for all existing transactions that match "${categorization.normalized_description}"`
                    : "Change the category to enable this option"
                  }
                </span>
              </div>
            </label>
          </div>
        </div>

        <div className="modal-footer">
          <button className="button-secondary" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button
            className="button-primary"
            onClick={handleSave}
            disabled={saving || !normalizedDescription.trim() || !categoryId}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}
