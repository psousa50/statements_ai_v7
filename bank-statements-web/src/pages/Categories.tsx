import { useState, useCallback, useRef, useMemo } from 'react'
import { useCategories } from '../services/hooks/useCategories'
import { useCategorySuggestions } from '../services/hooks/useCategorySuggestions'
import { useSubscription } from '../services/hooks/useSubscription'
import { useError } from '../context/ErrorContext'
import { CategoryTree } from '../components/CategoryTree'
import { CategoryModal } from '../components/CategoryModal'
import { CategorySuggestionPanel } from '../components/CategorySuggestionPanel'
import { ConfirmationModal } from '../components/ConfirmationModal'
import { Toast, ToastProps } from '../components/Toast'
import { Category } from '../types/Transaction'
import { Button, Dialog, DialogTitle, DialogContent, Chip } from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import DownloadIcon from '@mui/icons-material/Download'
import UploadIcon from '@mui/icons-material/Upload'
import './CategoriesPage.css'

export const CategoriesPage = () => {
  const [editingCategory, setEditingCategory] = useState<Category | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [selectedParentId, setSelectedParentId] = useState<string | undefined>(undefined)
  const [searchTerm, setSearchTerm] = useState('')
  const [excludedFilter, setExcludedFilter] = useState<'any' | 'on' | 'off'>('any')
  const [irregularFilter, setIrregularFilter] = useState<'any' | 'on' | 'off'>('any')

  const cycleFilter = (current: 'any' | 'on' | 'off'): 'any' | 'on' | 'off' =>
    current === 'any' ? 'on' : current === 'on' ? 'off' : 'any'
  const [toast, setToast] = useState<Omit<ToastProps, 'onClose'> | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<Category | null>(null)
  const [suggestionModalOpen, setSuggestionModalOpen] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { hasAIAccess } = useSubscription()
  const { showError } = useError()
  const hasAICategorisation = hasAIAccess('categorisation')

  const {
    categories,
    rootCategories,
    loading,
    mutating,
    error,
    addCategory,
    updateCategory,
    deleteCategory,
    fetchCategories,
    fetchRootCategories,
    exportCategories,
    uploadCategories,
  } = useCategories()

  const {
    suggestions,
    selectedItems,
    loading: suggestionsLoading,
    creating: suggestionsCreating,
    error: suggestionsError,
    totalDescriptionsAnalysed,
    generateSuggestions,
    toggleParent,
    toggleSubcategory,
    createSelected,
    reset: resetSuggestions,
    getSelectedCount,
  } = useCategorySuggestions()

  const getCategoryHierarchy = (categoryId: string): string[] => {
    const hierarchy: string[] = [categoryId]
    let current = categories.find((c) => c.id === categoryId)
    while (current?.parent_id) {
      hierarchy.unshift(current.parent_id)
      current = categories.find((c) => c.id === current?.parent_id)
    }
    return hierarchy
  }

  const hasActiveFilter = !!searchTerm || excludedFilter !== 'any' || irregularFilter !== 'any'

  const filteredCategories = !hasActiveFilter
    ? categories
    : (() => {
        const searchLower = searchTerm.toLowerCase()
        const matchingIds = new Set<string>()

        const matchesFlag = (value: boolean, filter: 'any' | 'on' | 'off') =>
          filter === 'any' || (filter === 'on' ? value : !value)

        categories.forEach((category) => {
          const nameMatches = !searchTerm || category.name.toLowerCase().includes(searchLower)
          const excludedMatches = matchesFlag(category.exclude_from_spending, excludedFilter)
          const irregularMatches = matchesFlag(category.is_irregular, irregularFilter)

          if (nameMatches && excludedMatches && irregularMatches) {
            matchingIds.add(category.id)
            getCategoryHierarchy(category.id).forEach((id) => matchingIds.add(id))
          }
        })

        return categories.filter((c) => matchingIds.has(c.id)).sort((a, b) => a.name.localeCompare(b.name))
      })()

  const forceExpandedCategories = useMemo(() => {
    if (!hasActiveFilter) return undefined
    const expanded = new Set<string>()
    filteredCategories.forEach((c) => {
      if (filteredCategories.some((other) => other.parent_id === c.id)) expanded.add(c.id)
    })
    return expanded
  }, [hasActiveFilter, filteredCategories])

  const filteredRootCategories = !hasActiveFilter
    ? rootCategories
    : rootCategories
        .filter((c) => filteredCategories.some((fc) => fc.id === c.id))
        .sort((a, b) => a.name.localeCompare(b.name))

  const handleCreateCategory = useCallback((parentId?: string) => {
    setSelectedParentId(parentId)
    setIsCreating(true)
  }, [])

  const handleEditCategory = useCallback((category: Category) => {
    setEditingCategory(category)
  }, [])

  const handleDeleteCategory = useCallback(
    (category: Category) => {
      // Check if category has subcategories
      const hasSubcategories = categories.some((c) => c.parent_id === category.id)

      if (hasSubcategories) {
        setToast({
          message: 'Cannot delete category with subcategories. Please delete or move subcategories first.',
          type: 'error',
        })
        return
      }

      setConfirmDelete(category)
    },
    [categories]
  )

  const handleConfirmDelete = useCallback(async () => {
    if (!confirmDelete) return

    const success = await deleteCategory(confirmDelete.id)
    if (success) {
      setToast({
        message: `Category "${confirmDelete.name}" deleted successfully`,
        type: 'success',
      })
    } else {
      setToast({
        message: `Failed to delete category "${confirmDelete.name}". It may be in use by transactions.`,
        type: 'error',
      })
    }

    setConfirmDelete(null)
  }, [confirmDelete, deleteCategory])

  const handleCancelDelete = useCallback(() => {
    setConfirmDelete(null)
  }, [])

  const handleSaveCategory = useCallback(
    async (
      name: string,
      parentId?: string,
      categoryId?: string,
      color?: string,
      excludeFromSpending?: boolean,
      isIrregular?: boolean
    ) => {
      try {
        if (categoryId) {
          const updatedCategory = await updateCategory(
            categoryId,
            name,
            parentId,
            color,
            excludeFromSpending,
            isIrregular
          )
          if (updatedCategory) {
            setToast({
              message: `Category "${name}" updated successfully`,
              type: 'success',
            })
            setEditingCategory(null)
          }
        } else {
          const newCategory = await addCategory(name, parentId, color, excludeFromSpending, isIrregular)
          if (newCategory) {
            setToast({
              message: `Category "${name}" created successfully`,
              type: 'success',
            })
            setIsCreating(false)
            setSelectedParentId(undefined)
          }
        }
      } catch (error) {
        console.error('Failed to save category:', error)
        setToast({
          message: 'Failed to save category. Please try again.',
          type: 'error',
        })
      }
    },
    [addCategory, updateCategory]
  )

  const handleToggleExcludeFromSpending = useCallback(
    async (category: Category) => {
      await updateCategory(
        category.id,
        category.name,
        category.parent_id,
        category.color,
        !category.exclude_from_spending,
        category.is_irregular
      )
    },
    [updateCategory]
  )

  const handleToggleIrregular = useCallback(
    async (category: Category) => {
      await updateCategory(
        category.id,
        category.name,
        category.parent_id,
        category.color,
        category.exclude_from_spending,
        !category.is_irregular
      )
    },
    [updateCategory]
  )

  const handleCloseModal = useCallback(() => {
    setEditingCategory(null)
    setIsCreating(false)
    setSelectedParentId(undefined)
  }, [])

  const handleCloseToast = useCallback(() => {
    setToast(null)
  }, [])

  const handleOpenSuggestionModal = useCallback(async () => {
    if (!hasAICategorisation) {
      showError({
        code: 'PAYMENT_REQUIRED',
        message: 'AI category generation requires a paid subscription.',
        details: { feature: 'ai_categorisation' },
        status: 402,
        type: 'payment',
      })
      return
    }
    setSuggestionModalOpen(true)
    const success = await generateSuggestions()
    if (!success) {
      setSuggestionModalOpen(false)
    }
  }, [generateSuggestions, hasAICategorisation, showError])

  const handleCloseSuggestionModal = useCallback(() => {
    setSuggestionModalOpen(false)
    resetSuggestions()
  }, [resetSuggestions])

  const handleCreateSuggestedCategories = useCallback(async () => {
    const result = await createSelected()
    if (result && result.categories_created > 0) {
      setToast({
        message: `Created ${result.categories_created} categories successfully`,
        type: 'success',
      })
      setSuggestionModalOpen(false)
      resetSuggestions()
      await Promise.all([fetchCategories(), fetchRootCategories()])
    } else if (result && result.categories_created === 0) {
      setToast({
        message: 'No new categories to create',
        type: 'info',
      })
    }
  }, [createSelected, resetSuggestions, fetchCategories, fetchRootCategories])

  const handleExportCategories = useCallback(async () => {
    const success = await exportCategories()
    if (success) {
      setToast({ message: 'Categories exported successfully', type: 'success' })
    } else {
      setToast({ message: 'Failed to export categories', type: 'error' })
    }
  }, [exportCategories])

  const handleUploadClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file) return

      const result = await uploadCategories(file)
      if (result) {
        setToast({
          message: `Imported ${result.categories_created} new categories (${result.categories_found} already existed)`,
          type: 'success',
        })
      } else {
        setToast({ message: 'Failed to import categories', type: 'error' })
      }

      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    },
    [uploadCategories]
  )

  // Get category stats
  const totalCategories = categories.length
  const rootCategoriesCount = rootCategories.length
  const subcategoriesCount = totalCategories - rootCategoriesCount

  return (
    <div className="categories-page">
      <header className="page-header">
        <h1>Category Management</h1>
        <p className="page-description">Create, edit, and organize your transaction categories</p>
      </header>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-value">{totalCategories}</div>
          <div className="card-label">Total Categories</div>
        </div>
        <div className="summary-card">
          <div className="card-value">{rootCategoriesCount}</div>
          <div className="card-label">Root Categories</div>
        </div>
        <div className="summary-card">
          <div className="card-value">{subcategoriesCount}</div>
          <div className="card-label">Subcategories</div>
        </div>
      </div>

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
              placeholder="Search categories..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            <button
              type="button"
              className={`category-filter-chip filter-${excludedFilter}`}
              onClick={() => setExcludedFilter(cycleFilter(excludedFilter))}
              title={
                excludedFilter === 'any'
                  ? 'Showing all. Click to show only excluded.'
                  : excludedFilter === 'on'
                    ? 'Showing only excluded. Click to show only non-excluded.'
                    : 'Showing only non-excluded. Click to show all.'
              }
            >
              {excludedFilter === 'any' ? 'Excluded: any' : excludedFilter === 'on' ? 'Excluded: only' : 'Excluded: none'}
            </button>
            <button
              type="button"
              className={`category-filter-chip filter-${irregularFilter}`}
              onClick={() => setIrregularFilter(cycleFilter(irregularFilter))}
              title={
                irregularFilter === 'any'
                  ? 'Showing all. Click to show only irregular.'
                  : irregularFilter === 'on'
                    ? 'Showing only irregular. Click to show only regular.'
                    : 'Showing only regular. Click to show all.'
              }
            >
              {irregularFilter === 'any'
                ? 'Irregular: any'
                : irregularFilter === 'on'
                  ? 'Irregular: only'
                  : 'Irregular: none'}
            </button>
            {hasActiveFilter && (
              <button
                type="button"
                className="category-filter-reset"
                onClick={() => {
                  setSearchTerm('')
                  setExcludedFilter('any')
                  setIrregularFilter('any')
                }}
                title="Clear search and filters"
              >
                Reset
              </button>
            )}
          </div>
          <div className="action-buttons">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".csv"
              style={{ display: 'none' }}
            />
            <Button
              onClick={handleExportCategories}
              variant="outlined"
              disabled={loading || mutating}
              startIcon={<DownloadIcon />}
              sx={{ textTransform: 'none', mr: 1 }}
            >
              Download
            </Button>
            <Button
              onClick={handleUploadClick}
              variant="outlined"
              disabled={loading || mutating}
              startIcon={<UploadIcon />}
              sx={{ textTransform: 'none', mr: 1 }}
            >
              Upload
            </Button>
            <Button
              onClick={handleOpenSuggestionModal}
              variant="outlined"
              disabled={loading || mutating}
              startIcon={<AutoAwesomeIcon />}
              endIcon={
                !hasAICategorisation ? (
                  <Chip label="PRO" size="small" color="warning" sx={{ height: 20, fontSize: '0.7rem' }} />
                ) : undefined
              }
              sx={{ textTransform: 'none', mr: 1 }}
            >
              Generate from Transactions
            </Button>
            <Button
              onClick={() => handleCreateCategory()}
              variant="contained"
              disabled={loading || mutating}
              startIcon={<AddIcon />}
              sx={{ textTransform: 'none' }}
            >
              Create Root Category
            </Button>
          </div>
        </div>
      </div>

      <div className="categories-content">
        <div className="categories-header">
          <h2>Categories</h2>
          {!loading && (
            <span className="category-count">
              {hasActiveFilter ? `${filteredCategories.length} of ${totalCategories}` : totalCategories} categories
            </span>
          )}
        </div>

        <div className="categories-tree-container">
          <CategoryTree
            categories={filteredCategories}
            rootCategories={filteredRootCategories}
            loading={loading}
            onEdit={handleEditCategory}
            onDelete={handleDeleteCategory}
            onCreateSubcategory={handleCreateCategory}
            onToggleExcludeFromSpending={handleToggleExcludeFromSpending}
            onToggleIrregular={handleToggleIrregular}
            forceExpandedCategories={forceExpandedCategories}
          />
        </div>
      </div>

      <CategoryModal
        isOpen={isCreating || !!editingCategory}
        category={editingCategory}
        parentId={selectedParentId}
        categories={categories}
        onSave={handleSaveCategory}
        onClose={handleCloseModal}
      />

      <ConfirmationModal
        isOpen={!!confirmDelete}
        title="Delete Category"
        message={`Are you sure you want to delete "${confirmDelete?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        dangerous={true}
      />

      {toast && <Toast message={toast.message} type={toast.type} onClose={handleCloseToast} />}

      <Dialog open={suggestionModalOpen} onClose={handleCloseSuggestionModal} maxWidth="md" fullWidth>
        <DialogTitle>Generate Categories from Transactions</DialogTitle>
        <DialogContent>
          <CategorySuggestionPanel
            suggestions={suggestions}
            selectedItems={selectedItems}
            loading={suggestionsLoading}
            creating={suggestionsCreating}
            error={suggestionsError}
            totalDescriptionsAnalysed={totalDescriptionsAnalysed}
            onToggleParent={toggleParent}
            onToggleSubcategory={toggleSubcategory}
            onCreateSelected={handleCreateSuggestedCategories}
            onClose={handleCloseSuggestionModal}
            selectedCount={getSelectedCount()}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}
