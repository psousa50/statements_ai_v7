import { useState, useEffect, useMemo } from 'react'
import { Category } from '../types/Transaction'
import { CategorySelector } from './CategorySelector'

interface CategoryModalProps {
  isOpen: boolean
  category: Category | null // null for creating, Category object for editing
  parentId?: string // When creating a subcategory
  categories: Category[]
  onSave: (name: string, parentId?: string, categoryId?: string) => Promise<void>
  onClose: () => void
}

export const CategoryModal = ({ isOpen, category, parentId, categories, onSave, onClose }: CategoryModalProps) => {
  const [name, setName] = useState('')
  const [selectedParentId, setSelectedParentId] = useState<string | undefined>(undefined)
  const [saving, setSaving] = useState(false)

  const isEditing = !!category
  const title = isEditing ? 'Edit Category' : 'Create Category'

  useEffect(() => {
    if (isOpen) {
      if (category) {
        // Editing existing category
        setName(category.name)
        setSelectedParentId(category.parent_id)
      } else {
        // Creating new category
        setName('')
        setSelectedParentId(parentId)
      }
    }
  }, [isOpen, category, parentId])

  // Filter out current category and its descendants to prevent circular references
  const availableParentCategories = useMemo(() => {
    if (!isEditing || !category) return categories

    const getDescendantIds = (categoryId: string): string[] => {
      const children = categories.filter((c) => c.parent_id === categoryId)
      const descendants = [categoryId]
      for (const child of children) {
        descendants.push(...getDescendantIds(child.id))
      }
      return descendants
    }

    const excludedIds = getDescendantIds(category.id)
    return categories.filter((c) => !excludedIds.includes(c.id))
  }, [categories, category, isEditing])

  if (!isOpen) return null

  const handleSave = async () => {
    const trimmedName = name.trim()
    if (!trimmedName) return

    if (selectedParentId) {
      const selectedParent = categories.find((c) => c.id === selectedParentId)
      if (selectedParent?.parent_id) {
        alert('Cannot select a subcategory as parent. Only top-level categories can be parents.')
        return
      }
    }

    const duplicateExists = categories.some(
      (c) =>
        c.name.toLowerCase() === trimmedName.toLowerCase() && c.parent_id === selectedParentId && c.id !== category?.id
    )

    if (duplicateExists) {
      throw new Error('A category with this name already exists at this level. Please choose a different name.')
    }

    setSaving(true)
    try {
      await onSave(trimmedName, selectedParentId, category?.id)
    } catch (error) {
      console.error('Failed to save category:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !saving && name.trim()) {
      handleSave()
    } else if (e.key === 'Escape') {
      onClose()
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label htmlFor="category-name">Category Name</label>
            <input
              id="category-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Enter category name"
              autoFocus
              maxLength={100}
            />
          </div>

          <div className="form-group">
            <label htmlFor="parent-category">Parent Category (Optional)</label>
            <CategorySelector
              categories={availableParentCategories}
              selectedCategoryId={selectedParentId}
              onCategoryChange={(id) => setSelectedParentId(id)}
              placeholder="Select a parent category (leave empty for root category)"
              allowClear={true}
              variant="form"
              allowParentCategories={true}
            />
            {selectedParentId && (
              <div className="form-help-text">
                This category will be created as a subcategory of the selected parent.
              </div>
            )}
          </div>

          {isEditing && category && (
            <div className="form-group">
              <div className="category-info">
                <strong>Current Path:</strong>
                <div className="category-path">
                  {category.parent_id ? (
                    <>
                      {categories.find((c) => c.id === category.parent_id)?.name || 'Unknown Parent'} → {category.name}
                    </>
                  ) : (
                    <>Root → {category.name}</>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="button-secondary" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button className="button-primary" onClick={handleSave} disabled={saving || !name.trim()}>
            {saving ? 'Saving...' : isEditing ? 'Update Category' : 'Create Category'}
          </button>
        </div>
      </div>
    </div>
  )
}
