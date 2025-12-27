import { Category } from '../types/Transaction'

export interface CategoryListResponse {
  categories: Category[]
  total: number
}

export interface SubcategorySuggestion {
  name: string
  is_new: boolean
}

export interface CategorySuggestion {
  parent_name: string
  parent_id: string | null
  parent_is_new: boolean
  subcategories: SubcategorySuggestion[]
  confidence: number
  matched_descriptions: string[]
}

export interface GenerateCategoriesResponse {
  suggestions: CategorySuggestion[]
  total_descriptions_analysed: number
}

export interface CategorySelectionItem {
  parent_name: string
  parent_id: string | null
  subcategory_names: string[]
}

export interface CreateSelectedCategoriesRequest {
  selections: CategorySelectionItem[]
}

export interface CreateSelectedCategoriesResponse {
  categories_created: number
  categories: Category[]
}

export interface CategoryClient {
  getAll(): Promise<CategoryListResponse>
  getRootCategories(): Promise<CategoryListResponse>
  getById(id: string): Promise<Category>
  getSubcategories(parentId: string): Promise<CategoryListResponse>
  create(category: { name: string; parent_id?: string }): Promise<Category>
  update(id: string, category: { name: string; parent_id?: string }): Promise<Category>
  delete(id: string): Promise<void>
  generateSuggestions(): Promise<GenerateCategoriesResponse>
  createSelectedCategories(request: CreateSelectedCategoriesRequest): Promise<CreateSelectedCategoriesResponse>
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

  async generateSuggestions() {
    const response = await axios.post<GenerateCategoriesResponse>(`${API_URL}/ai/generate-suggestions`)
    return response.data
  },

  async createSelectedCategories(request: CreateSelectedCategoriesRequest) {
    const response = await axios.post<CreateSelectedCategoriesResponse>(`${API_URL}/ai/create-selected`, request)
    return response.data
  },
}
