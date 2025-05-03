import { useState, useEffect, useCallback } from 'react';
import { Category } from '../../types/Transaction';
import { useApiClients } from '../../api/ApiClientsContext';
import { CategoryListResponse } from '../../api/CategoryClient';

export const useCategories = () => {
  const { categoryClient } = useApiClients();
  const [categories, setCategories] = useState<Category[]>([]);
  const [rootCategories, setRootCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await categoryClient.getAll();
      setCategories(response.categories);
    } catch (err) {
      console.error('Error fetching categories:', err);
      setError('Failed to fetch categories. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [categoryClient]);

  const fetchRootCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await categoryClient.getRootCategories();
      setRootCategories(response.categories);
    } catch (err) {
      console.error('Error fetching root categories:', err);
      setError('Failed to fetch root categories. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [categoryClient]);

  const fetchSubcategories = useCallback(
    async (parentId: string) => {
      setLoading(true);
      setError(null);
      try {
        const response = await categoryClient.getSubcategories(parentId);
        return response.categories;
      } catch (err) {
        console.error('Error fetching subcategories:', err);
        setError('Failed to fetch subcategories. Please try again later.');
        return [];
      } finally {
        setLoading(false);
      }
    },
    [categoryClient]
  );

  const addCategory = useCallback(
    async (name: string, parentId?: string) => {
      setLoading(true);
      setError(null);
      try {
        const newCategory = await categoryClient.create({
          name,
          parent_id: parentId,
        });
        setCategories((prev) => [...prev, newCategory]);
        if (!parentId) {
          setRootCategories((prev) => [...prev, newCategory]);
        }
        return newCategory;
      } catch (err) {
        console.error('Error adding category:', err);
        setError('Failed to add category. Please try again later.');
        return null;
      } finally {
        setLoading(false);
      }
    },
    [categoryClient]
  );

  const updateCategory = useCallback(
    async (id: string, name: string, parentId?: string) => {
      setLoading(true);
      setError(null);
      try {
        const updatedCategory = await categoryClient.update(id, {
          name,
          parent_id: parentId,
        });
        setCategories((prev) =>
          prev.map((category) =>
            category.id === id ? updatedCategory : category
          )
        );
        setRootCategories((prev) => {
          // If the category was a root category and now has a parent, remove it from root categories
          if (parentId && !prev.find((c) => c.id === id)?.parent_id) {
            return prev.filter((category) => category.id !== id);
          }
          // If the category was not a root category and now has no parent, add it to root categories
          if (!parentId && prev.find((c) => c.id === id)?.parent_id) {
            return [...prev, updatedCategory];
          }
          // Otherwise, just update it if it's in the root categories
          return prev.map((category) =>
            category.id === id ? updatedCategory : category
          );
        });
        return updatedCategory;
      } catch (err) {
        console.error('Error updating category:', err);
        setError('Failed to update category. Please try again later.');
        return null;
      } finally {
        setLoading(false);
      }
    },
    [categoryClient]
  );

  const deleteCategory = useCallback(
    async (id: string) => {
      setLoading(true);
      setError(null);
      try {
        await categoryClient.delete(id);
        setCategories((prev) => prev.filter((category) => category.id !== id));
        setRootCategories((prev) =>
          prev.filter((category) => category.id !== id)
        );
        return true;
      } catch (err) {
        console.error('Error deleting category:', err);
        setError('Failed to delete category. Please try again later.');
        return false;
      } finally {
        setLoading(false);
      }
    },
    [categoryClient]
  );

  useEffect(() => {
    fetchCategories();
    fetchRootCategories();
  }, [fetchCategories, fetchRootCategories]);

  return {
    categories,
    rootCategories,
    loading,
    error,
    fetchCategories,
    fetchRootCategories,
    fetchSubcategories,
    addCategory,
    updateCategory,
    deleteCategory,
  };
};
