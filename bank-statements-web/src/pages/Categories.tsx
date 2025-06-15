import { useState, useCallback, useEffect } from 'react'
import { useCategories } from '../services/hooks/useCategories'
import { CategoryTree } from '../components/CategoryTree'
import { CategoryModal } from '../components/CategoryModal'
import { ConfirmationModal } from '../components/ConfirmationModal'
import { Toast, ToastProps } from '../components/Toast'
import { Category } from '../types/Transaction'
import './CategoriesPage.css'

export const CategoriesPage = () => {
  const [editingCategory, setEditingCategory] = useState<Category | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [selectedParentId, setSelectedParentId] = useState<string | undefined>(undefined)
  const [searchTerm, setSearchTerm] = useState('')
  const [toast, setToast] = useState<Omit<ToastProps, 'onClose'> | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<Category | null>(null)

  const {
    categories,
    rootCategories,
    loading,
    error,
    fetchCategories,
    addCategory,
    updateCategory,
    deleteCategory,
  } = useCategories()

  // Filter categories based on search term
  const filteredCategories = categories.filter(category =>
    category.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const filteredRootCategories = rootCategories.filter(category =>
    category.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleCreateCategory = useCallback((parentId?: string) => {
    setSelectedParentId(parentId)
    setIsCreating(true)
  }, [])

  const handleEditCategory = useCallback((category: Category) => {
    setEditingCategory(category)
  }, [])

  const handleDeleteCategory = useCallback((category: Category) => {
    // Check if category has subcategories
    const hasSubcategories = categories.some(c => c.parent_id === category.id)
    
    if (hasSubcategories) {
      setToast({
        message: 'Cannot delete category with subcategories. Please delete or move subcategories first.',
        type: 'error'
      })
      return
    }

    setConfirmDelete(category)
  }, [categories])

  const handleConfirmDelete = useCallback(async () => {
    if (!confirmDelete) return

    const success = await deleteCategory(confirmDelete.id)
    if (success) {
      setToast({
        message: `Category "${confirmDelete.name}" deleted successfully`,
        type: 'success'
      })
    } else {
      setToast({
        message: `Failed to delete category "${confirmDelete.name}". It may be in use by transactions.`,
        type: 'error'
      })
    }
    
    setConfirmDelete(null)
  }, [confirmDelete, deleteCategory])

  const handleCancelDelete = useCallback(() => {
    setConfirmDelete(null)
  }, [])

  const handleSaveCategory = useCallback(async (
    name: string,
    parentId?: string,
    categoryId?: string
  ) => {
    try {
      if (categoryId) {
        // Updating existing category
        const updatedCategory = await updateCategory(categoryId, name, parentId)
        if (updatedCategory) {
          setToast({
            message: `Category "${name}" updated successfully`,
            type: 'success'
          })
          setEditingCategory(null)
        }
      } else {
        // Creating new category
        const newCategory = await addCategory(name, parentId)
        if (newCategory) {
          setToast({
            message: `Category "${name}" created successfully`,
            type: 'success'
          })
          setIsCreating(false)
          setSelectedParentId(undefined)
        }
      }
    } catch (error) {
      console.error('Failed to save category:', error)
      setToast({
        message: 'Failed to save category. Please try again.',
        type: 'error'
      })
    }
  }, [addCategory, updateCategory])

  const handleCloseModal = useCallback(() => {
    setEditingCategory(null)
    setIsCreating(false)
    setSelectedParentId(undefined)
  }, [])

  const handleCloseToast = useCallback(() => {
    setToast(null)
  }, [])

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
            <button
              onClick={() => handleCreateCategory()}
              className="button-primary"
              disabled={loading}
            >
              + Create Root Category
            </button>
            <button
              onClick={() => fetchCategories()}
              className="button-secondary"
              disabled={loading}
              title="Refresh categories"
            >
              🔄 Refresh
            </button>
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

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={handleCloseToast}
        />
      )}
    </div>
  )
}