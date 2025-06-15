import { useState, useMemo } from 'react'
import { Category } from '../types/Transaction'

interface CategoryTreeProps {
  categories: Category[]
  rootCategories: Category[]
  loading: boolean
  onEdit: (category: Category) => void
  onDelete: (category: Category) => void
  onCreateSubcategory: (parentId: string) => void
}

interface CategoryTreeNodeProps {
  category: Category
  allCategories: Category[]
  level: number
  onEdit: (category: Category) => void
  onDelete: (category: Category) => void
  onCreateSubcategory: (parentId: string) => void
}

const CategoryTreeNode = ({ 
  category, 
  allCategories, 
  level, 
  onEdit, 
  onDelete, 
  onCreateSubcategory 
}: CategoryTreeNodeProps) => {
  const [isExpanded, setIsExpanded] = useState(true)

  // Get subcategories for this category
  const subcategories = useMemo(() => 
    allCategories.filter(c => c.parent_id === category.id)
  , [allCategories, category.id])

  const hasSubcategories = subcategories.length > 0

  const handleToggleExpand = () => {
    if (hasSubcategories) {
      setIsExpanded(!isExpanded)
    }
  }

  const indentLevel = level * 20

  return (
    <div className="category-tree-node">
      <div 
        className="category-row"
        style={{ paddingLeft: `${indentLevel}px` }}
      >
        <div className="category-info">
          <div className="category-expand">
            {hasSubcategories ? (
              <button 
                onClick={handleToggleExpand}
                className="expand-button"
                aria-label={isExpanded ? 'Collapse' : 'Expand'}
              >
                {isExpanded ? '▼' : '▶'}
              </button>
            ) : (
              <span className="expand-spacer">•</span>
            )}
          </div>
          <div className="category-name">{category.name}</div>
          <div className="category-stats">
            {hasSubcategories && (
              <span className="subcategory-count">
                {subcategories.length} subcategories
              </span>
            )}
          </div>
        </div>
        <div className="category-actions">
          <button
            onClick={() => onCreateSubcategory(category.id)}
            className="action-button create-button"
            title="Add subcategory"
          >
            +
          </button>
          <button
            onClick={() => onEdit(category)}
            className="action-button edit-button"
            title="Edit category"
          >
            ✏️
          </button>
          <button
            onClick={() => onDelete(category)}
            className="action-button delete-button"
            title="Delete category"
          >
            🗑️
          </button>
        </div>
      </div>

      {/* Render subcategories if expanded */}
      {hasSubcategories && isExpanded && (
        <div className="category-children">
          {subcategories.map(subcategory => (
            <CategoryTreeNode
              key={subcategory.id}
              category={subcategory}
              allCategories={allCategories}
              level={level + 1}
              onEdit={onEdit}
              onDelete={onDelete}
              onCreateSubcategory={onCreateSubcategory}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export const CategoryTree = ({ 
  categories, 
  rootCategories, 
  loading, 
  onEdit, 
  onDelete, 
  onCreateSubcategory 
}: CategoryTreeProps) => {
  if (loading) {
    return (
      <div className="category-tree-loading">
        <div className="loading-spinner"></div>
        <p>Loading categories...</p>
      </div>
    )
  }

  if (categories.length === 0) {
    return (
      <div className="category-tree-empty">
        <p>No categories found.</p>
        <p>Create your first category to get started.</p>
      </div>
    )
  }

  if (rootCategories.length === 0) {
    return (
      <div className="category-tree-empty">
        <p>No categories match your search.</p>
      </div>
    )
  }

  return (
    <div className="category-tree">
      {rootCategories.map(rootCategory => (
        <CategoryTreeNode
          key={rootCategory.id}
          category={rootCategory}
          allCategories={categories}
          level={0}
          onEdit={onEdit}
          onDelete={onDelete}
          onCreateSubcategory={onCreateSubcategory}
        />
      ))}
    </div>
  )
}