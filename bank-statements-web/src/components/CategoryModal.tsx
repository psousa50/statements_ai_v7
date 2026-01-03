import { useState, useEffect, useMemo } from 'react'
import { Category } from '../types/Transaction'
import { CategorySelector } from './CategorySelector'
import { ColorSwatchPicker } from './ColorSwatchPicker'
import { PRESET_COLORS } from '../utils/categoryColors'

interface CategoryModalProps {
  isOpen: boolean
  category: Category | null
  parentId?: string
  categories: Category[]
  onSave: (name: string, parentId?: string, categoryId?: string, color?: string) => Promise<void>
  onClose: () => void
}

export const CategoryModal = ({ isOpen, category, parentId, categories, onSave, onClose }: CategoryModalProps) => {
  const [name, setName] = useState('')
  const [selectedParentId, setSelectedParentId] = useState<string | undefined>(undefined)
  const [selectedColor, setSelectedColor] = useState<string | undefined>(undefined)
  const [saving, setSaving] = useState(false)

  const isEditing = !!category
  const parentCategory = parentId ? categories.find((c) => c.id === parentId) : null
  const title = isEditing
    ? 'Edit Category'
    : parentId
      ? `Create Subcategory under ${parentCategory?.name || 'Unknown'}`
      : 'Create Root Category'
  const isRootCategory = !selectedParentId

  useEffect(() => {
    if (isOpen) {
      if (category) {
        setName(category.name)
        setSelectedParentId(category.parent_id)
        setSelectedColor(category.color)
      } else {
        setName('')
        setSelectedParentId(parentId)
        setSelectedColor(parentId ? undefined : PRESET_COLORS[0])
      }
    }
  }, [isOpen, category, parentId])

  useEffect(() => {
    if (selectedParentId) {
      setSelectedColor(undefined)
    } else if (!selectedColor && !category?.parent_id) {
      setSelectedColor(PRESET_COLORS[0])
    }
  }, [selectedParentId, selectedColor, category?.parent_id])

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

  const usedColors = useMemo(() => {
    const colorMap = new Map<string, string[]>()
    const parentCategories = categories.filter((c) => !c.parent_id && c.id !== category?.id)
    for (const cat of parentCategories) {
      if (cat.color) {
        const existing = colorMap.get(cat.color) || []
        existing.push(cat.name)
        colorMap.set(cat.color, existing)
      }
    }
    return colorMap
  }, [categories, category?.id])

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
      await onSave(trimmedName, selectedParentId, category?.id, isRootCategory ? selectedColor : undefined)
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

          {isEditing && (
            <div className="form-group">
              <label htmlFor="parent-category">Parent Category</label>
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
                  This category will be moved as a subcategory of the selected parent.
                </div>
              )}
            </div>
          )}

          {isRootCategory && (
            <div className="form-group">
              <label>Colour</label>
              <ColorSwatchPicker value={selectedColor} onChange={setSelectedColor} usedColors={usedColors} />
            </div>
          )}

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
