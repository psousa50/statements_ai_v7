import { Category } from '../types/Transaction'

export interface CategoryListResponse {
  categories: Category[]
  total: number
}

export interface CategoryClient {
  getAll(): Promise<CategoryListResponse>
  getRootCategories(): Promise<CategoryListResponse>
  getById(id: string): Promise<Category>
  getSubcategories(parentId: string): Promise<CategoryListResponse>
  create(category: { name: string; parent_id?: string }): Promise<Category>
  update(id: string, category: { name: string; parent_id?: string }): Promise<Category>
  delete(id: string): Promise<void>
}

// Use the VITE_API_URL environment variable for the base URL, or default to '' for local development
const BASE_URL = import.meta.env.VITE_API_URL || ''
const API_URL = `${BASE_URL}/api/v1/categories`

import axios from 'axios'

export const categoryClient: CategoryClient = {
  async getAll() {
    const response = await axios.get<CategoryListResponse>(API_URL)
    return response.data
  },

  async getRootCategories() {
    const response = await axios.get<CategoryListResponse>(`${API_URL}/root`)
    return response.data
  },

  async getById(id: string) {
    const response = await axios.get<Category>(`${API_URL}/${id}`)
    return response.data
  },

  async getSubcategories(parentId: string) {
    const response = await axios.get<CategoryListResponse>(`${API_URL}/${parentId}/subcategories`)
    return response.data
  },

  async create(category: { name: string; parent_id?: string }) {
    const response = await axios.post<Category>(API_URL, category)
    return response.data
  },

  async update(id: string, category: { name: string; parent_id?: string }) {
    const response = await axios.put<Category>(`${API_URL}/${id}`, category)
    return response.data
  },

  async delete(id: string) {
    await axios.delete(`${API_URL}/${id}`)
  },
}
