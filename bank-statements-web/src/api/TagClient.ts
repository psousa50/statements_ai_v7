import { Tag, TagWithUsage, Transaction } from '../types/Transaction'
import { axiosInstance } from './ApiClient'

export interface TagListResponse {
  tags: TagWithUsage[]
  total: number
}

export interface BulkTagResponse {
  tagged_count: number
  message: string
}

export interface TagClient {
  getAll(): Promise<TagListResponse>
  create(name: string): Promise<Tag>
  rename(tagId: string, name: string): Promise<Tag>
  delete(tagId: string): Promise<void>
  addToTransaction(transactionId: string, tagId: string): Promise<Transaction>
  removeFromTransaction(transactionId: string, tagId: string): Promise<Transaction>
  bulkAddToTransactions(transactionIds: string[], tagId: string): Promise<BulkTagResponse>
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

  async rename(tagId: string, name: string) {
    const response = await axiosInstance.patch<Tag>(`${TAGS_URL}/${tagId}`, { name })
    return response.data
  },

  async delete(tagId: string) {
    await axiosInstance.delete(`${TAGS_URL}/${tagId}`)
  },

  async addToTransaction(transactionId: string, tagId: string) {
    const response = await axiosInstance.post<Transaction>(`${TRANSACTIONS_URL}/${transactionId}/tags/${tagId}`)
    return response.data
  },

  async removeFromTransaction(transactionId: string, tagId: string) {
    const response = await axiosInstance.delete<Transaction>(`${TRANSACTIONS_URL}/${transactionId}/tags/${tagId}`)
    return response.data
  },

  async bulkAddToTransactions(transactionIds: string[], tagId: string) {
    const response = await axiosInstance.post<BulkTagResponse>(`${TAGS_URL}/bulk-add`, {
      transaction_ids: transactionIds,
      tag_id: tagId,
    })
    return response.data
  },
}
