import { useState, useMemo, useCallback } from 'react'
import { CATEGORY_KIND_LABELS, Category, CategoryKind } from '../types/Transaction'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import AddIcon from '@mui/icons-material/Add'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import ExpandLessIcon from '@mui/icons-material/ExpandLess'
import { ActionIconButton } from './ActionIconButton'
import { IconButton, Tooltip } from '@mui/material'
import { getCategoryColor } from '../utils/categoryColors'

interface CategoryTreeProps {
  categories: Category[]
  rootCategories: Category[]
  loading: boolean
  onEdit: (category: Category) => void
  onDelete: (category: Category) => void
  onCreateSubcategory: (parentId: string) => void
  onToggleExcludeFromSpending: (category: Category) => void
  onChangeKind: (category: Category, kind: CategoryKind) => void
  forceExpandedCategories?: Set<string>
}

interface CategoryTreeNodeProps {
  category: Category
  allCategories: Category[]
  level: number
  onEdit: (category: Category) => void
  onDelete: (category: Category) => void
  onCreateSubcategory: (parentId: string) => void
  onToggleExcludeFromSpending: (category: Category) => void
  onChangeKind: (category: Category, kind: CategoryKind) => void
  expandedCategories: Set<string>
  onToggleExpand: (categoryId: string) => void
}

const CategoryTreeNode = ({
  category,
  allCategories,
  level,
  onEdit,
  onDelete,
  onCreateSubcategory,
  onToggleExcludeFromSpending,
  onChangeKind,
  expandedCategories,
  onToggleExpand,
}: CategoryTreeNodeProps) => {
  // Get subcategories for this category, sorted alphabetically
  const subcategories = useMemo(
    () => allCategories.filter((c) => c.parent_id === category.id).sort((a, b) => a.name.localeCompare(b.name)),
    [allCategories, category.id]
  )

  const hasSubcategories = subcategories.length > 0
  const isExpanded = expandedCategories.has(category.id)

  const handleToggleExpand = () => {
    if (hasSubcategories) {
      onToggleExpand(category.id)
    }
  }

  const indentLevel = level * 20

  const handleRowClick = () => {
    if (hasSubcategories) {
      onToggleExpand(category.id)
    } else {
      onEdit(category)
    }
  }

  const stop = (e: React.MouseEvent) => e.stopPropagation()

  return (
    <div className="category-tree-node">
      <div
        className="category-row"
        style={{ paddingLeft: `${indentLevel}px`, cursor: 'pointer' }}
        onClick={handleRowClick}
      >
        <div className="category-info">
          <div className="category-expand">
            {hasSubcategories ? (
              <IconButton
                onClick={(e) => {
                  stop(e)
                  handleToggleExpand()
                }}
                size="small"
                aria-label={isExpanded ? 'Collapse' : 'Expand'}
                sx={{
                  padding: '2px',
                  color: 'var(--text-muted)',
                  '&:hover': {
                    backgroundColor: 'var(--bg-hover)',
                    color: 'var(--text-primary)',
                  },
                }}
              >
                {isExpanded ? <ExpandMoreIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
              </IconButton>
            ) : (
              <span className="expand-spacer" style={{ width: '28px', display: 'inline-block' }}></span>
            )}
          </div>
          <span
            className="category-color-swatch"
            style={{ backgroundColor: getCategoryColor(category, allCategories).solid }}
          />
          <div className="category-name">{category.name}</div>
          <Tooltip
            title={
              category.exclude_from_spending
                ? 'Transactions in this category are excluded from spending/income analytics. Click to include them.'
                : 'Include this category in spending/income analytics. Toggle off for things like internal transfers or reimbursable expenses.'
            }
            arrow
          >
            <button
              type="button"
              className={`category-flag-toggle ${category.exclude_from_spending ? 'is-on' : ''}`}
              onClick={(e) => {
                stop(e)
                onToggleExcludeFromSpending(category)
              }}
            >
              {category.exclude_from_spending ? 'Excluded' : '+ Exclude'}
            </button>
          </Tooltip>
          <select
            className={`category-kind-select kind-${category.kind}`}
            value={category.kind}
            onClick={stop}
            onChange={(e) => onChangeKind(category, e.target.value as CategoryKind)}
            title="Spending kind"
          >
            {(Object.keys(CATEGORY_KIND_LABELS) as CategoryKind[]).map((k) => (
              <option key={k} value={k}>
                {CATEGORY_KIND_LABELS[k]}
              </option>
            ))}
          </select>
          <div className="category-stats">
            {hasSubcategories && <span className="subcategory-count">{subcategories.length} subcategories</span>}
          </div>
        </div>
        <div className="category-actions" onClick={stop}>
          <ActionIconButton
            onClick={() => onCreateSubcategory(category.id)}
            title="Add subcategory"
            icon={<AddIcon fontSize="small" />}
            color="success"
          />
          <ActionIconButton
            onClick={() => onEdit(category)}
            title="Edit category"
            icon={<EditIcon fontSize="small" />}
            color="primary"
          />
          <ActionIconButton
            onClick={() => onDelete(category)}
            title="Delete category"
            icon={<DeleteIcon fontSize="small" />}
            color="error"
          />
        </div>
      </div>

      {/* Render subcategories if expanded */}
      {hasSubcategories && isExpanded && (
        <div className="category-children">
          {subcategories.map((subcategory) => (
            <CategoryTreeNode
              key={subcategory.id}
              category={subcategory}
              allCategories={allCategories}
              level={level + 1}
              onEdit={onEdit}
              onDelete={onDelete}
              onCreateSubcategory={onCreateSubcategory}
              onToggleExcludeFromSpending={onToggleExcludeFromSpending}
              onChangeKind={onChangeKind}
              expandedCategories={expandedCategories}
              onToggleExpand={onToggleExpand}
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
  onCreateSubcategory,
  onToggleExcludeFromSpending,
  onChangeKind,
  forceExpandedCategories,
}: CategoryTreeProps) => {
  const [userExpandedCategories, setUserExpandedCategories] = useState<Set<string>>(new Set())
  const expandedCategories = useMemo(() => {
    if (!forceExpandedCategories || forceExpandedCategories.size === 0) return userExpandedCategories
    const merged = new Set(userExpandedCategories)
    forceExpandedCategories.forEach((id) => merged.add(id))
    return merged
  }, [userExpandedCategories, forceExpandedCategories])
  const setExpandedCategories = setUserExpandedCategories

  const handleToggleExpand = useCallback((categoryId: string) => {
    setExpandedCategories((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId)
      } else {
        newSet.add(categoryId)
      }
      return newSet
    })
  }, [])

  const handleExpandAll = useCallback(() => {
    const allParentCategories = new Set<string>()
    categories.forEach((category) => {
      const hasSubcategories = categories.some((c) => c.parent_id === category.id)
      if (hasSubcategories) {
        allParentCategories.add(category.id)
      }
    })
    setExpandedCategories(allParentCategories)
  }, [categories])

  const handleCollapseAll = useCallback(() => {
    setExpandedCategories(new Set())
  }, [])

  // Count expanded vs total expandable categories
  const totalExpandableCategories = categories.filter((category) =>
    categories.some((c) => c.parent_id === category.id)
  ).length
  const expandedCount = expandedCategories.size
  const allExpanded = expandedCount === totalExpandableCategories
  const allCollapsed = expandedCount === 0
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
      {totalExpandableCategories > 0 && (
        <div className="category-tree-controls">
          <div className="expand-collapse-controls">
            <button
              onClick={handleExpandAll}
              disabled={allExpanded}
              className="control-button expand-all-button"
              title="Expand all categories"
            >
              <ExpandMoreIcon sx={{ fontSize: '16px', mr: 0.5 }} /> Expand All
            </button>
            <button
              onClick={handleCollapseAll}
              disabled={allCollapsed}
              className="control-button collapse-all-button"
              title="Collapse all categories"
            >
              <ExpandLessIcon sx={{ fontSize: '16px', mr: 0.5 }} /> Collapse All
            </button>
          </div>
          <div className="expand-status">
            {expandedCount} of {totalExpandableCategories} expanded
          </div>
        </div>
      )}

      <div className="category-tree-content">
        {rootCategories.map((rootCategory) => (
          <CategoryTreeNode
            key={rootCategory.id}
            category={rootCategory}
            allCategories={categories}
            level={0}
            onEdit={onEdit}
            onDelete={onDelete}
            onCreateSubcategory={onCreateSubcategory}
            onToggleExcludeFromSpending={onToggleExcludeFromSpending}
            onChangeKind={onChangeKind}
            expandedCategories={expandedCategories}
            onToggleExpand={handleToggleExpand}
          />
        ))}
      </div>
    </div>
  )
}
