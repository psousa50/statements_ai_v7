import { useState, useCallback, useRef } from 'react'
import { useCategories } from '../services/hooks/useCategories'
import { useCategorySuggestions } from '../services/hooks/useCategorySuggestions'
import { CategoryTree } from '../components/CategoryTree'
import { CategoryModal } from '../components/CategoryModal'
import { CategorySuggestionPanel } from '../components/CategorySuggestionPanel'
import { ConfirmationModal } from '../components/ConfirmationModal'
import { Toast, ToastProps } from '../components/Toast'
import { Category } from '../types/Transaction'
import { Button, Dialog, DialogTitle, DialogContent } from '@mui/material'
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
  const [toast, setToast] = useState<Omit<ToastProps, 'onClose'> | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<Category | null>(null)
  const [suggestionModalOpen, setSuggestionModalOpen] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const {
    categories,
    rootCategories,
    loading,
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

  const filteredCategories = !searchTerm
    ? categories
    : (() => {
        const searchLower = searchTerm.toLowerCase()
        const matchingIds = new Set<string>()

        categories.forEach((category) => {
          const categoryNameMatch = category.name.toLowerCase().includes(searchLower)

          if (categoryNameMatch) {
            matchingIds.add(category.id)
            getCategoryHierarchy(category.id).forEach((id) => matchingIds.add(id))
          }
        })

        return categories.filter((c) => matchingIds.has(c.id)).sort((a, b) => a.name.localeCompare(b.name))
      })()

  const filteredRootCategories = !searchTerm
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
    async (name: string, parentId?: string, categoryId?: string) => {
      try {
        if (categoryId) {
          // Updating existing category
          const updatedCategory = await updateCategory(categoryId, name, parentId)
          if (updatedCategory) {
            setToast({
              message: `Category "${name}" updated successfully`,
              type: 'success',
            })
            setEditingCategory(null)
          }
        } else {
          // Creating new category
          const newCategory = await addCategory(name, parentId)
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

  const handleCloseModal = useCallback(() => {
    setEditingCategory(null)
    setIsCreating(false)
    setSelectedParentId(undefined)
  }, [])

  const handleCloseToast = useCallback(() => {
    setToast(null)
  }, [])

  const handleOpenSuggestionModal = useCallback(async () => {
    setSuggestionModalOpen(true)
    await generateSuggestions()
  }, [generateSuggestions])

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
              disabled={loading}
              startIcon={<DownloadIcon />}
              sx={{ textTransform: 'none', mr: 1 }}
            >
              Download
            </Button>
            <Button
              onClick={handleUploadClick}
              variant="outlined"
              disabled={loading}
              startIcon={<UploadIcon />}
              sx={{ textTransform: 'none', mr: 1 }}
            >
              Upload
            </Button>
            <Button
              onClick={handleOpenSuggestionModal}
              variant="outlined"
              disabled={loading}
              startIcon={<AutoAwesomeIcon />}
              sx={{ textTransform: 'none', mr: 1 }}
            >
              Generate from Transactions
            </Button>
            <Button
              onClick={() => handleCreateCategory()}
              variant="contained"
              disabled={loading}
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
              {searchTerm ? `${filteredCategories.length} of ${totalCategories}` : totalCategories} categories
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
