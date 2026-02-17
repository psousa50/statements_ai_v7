import { Tag, Transaction } from '../types/Transaction'
import { axiosInstance } from './ApiClient'

export interface TagListResponse {
  tags: Tag[]
  total: number
}

export interface TagClient {
  getAll(): Promise<TagListResponse>
  create(name: string): Promise<Tag>
  addToTransaction(transactionId: string, tagId: string): Promise<Transaction>
  removeFromTransaction(transactionId: string, tagId: string): Promise<Transaction>
}

const BASE_URL = import.meta.env.VITE_API_URL || ''
const TAGS_URL = `${BASE_URL}/api/v1/tags`
const TRANSACTIONS_URL = `${BASE_URL}/api/v1/transactions`

export const tagClient: TagClient = {
  async getAll() {
    const response = await axiosInstance.get<TagListResponse>(TAGS_URL)
    return response.data
  },

  async create(name: string) {
    const response = await axiosInstance.post<Tag>(TAGS_URL, { name })
    return response.data
  },

  async addToTransaction(transactionId: string, tagId: string) {
    const response = await axiosInstance.post<Transaction>(`${TRANSACTIONS_URL}/${transactionId}/tags/${tagId}`)
    return response.data
  },

  async removeFromTransaction(transactionId: string, tagId: string) {
    const response = await axiosInstance.delete<Transaction>(`${TRANSACTIONS_URL}/${transactionId}/tags/${tagId}`)
    return response.data
  },
}
