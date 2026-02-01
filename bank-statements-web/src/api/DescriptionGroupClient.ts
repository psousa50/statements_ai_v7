import { axiosInstance } from './ApiClient'

export interface DescriptionGroupMember {
  id: string
  normalized_description: string
}

export interface DescriptionGroup {
  id: string
  name: string
  members: DescriptionGroupMember[]
  created_at: string
  updated_at: string
}

export interface DescriptionGroupListResponse {
  groups: DescriptionGroup[]
  total: number
}

export interface DescriptionGroupCreate {
  name: string
  normalized_descriptions: string[]
}

export interface DescriptionGroupClient {
  getAll(): Promise<DescriptionGroupListResponse>
  getById(id: string): Promise<DescriptionGroup>
  create(group: DescriptionGroupCreate): Promise<DescriptionGroup>
  update(id: string, group: DescriptionGroupCreate): Promise<DescriptionGroup>
  delete(id: string): Promise<void>
}

const BASE_URL = import.meta.env.VITE_API_URL || ''
const API_URL = `${BASE_URL}/api/v1/description-groups`

export const descriptionGroupClient: DescriptionGroupClient = {
  async getAll() {
    const response = await axiosInstance.get<DescriptionGroupListResponse>(API_URL)
    return response.data
  },

  async getById(id: string) {
    const response = await axiosInstance.get<DescriptionGroup>(`${API_URL}/${id}`)
    return response.data
  },

  async create(group: DescriptionGroupCreate) {
    const response = await axiosInstance.post<DescriptionGroup>(API_URL, group)
    return response.data
  },

  async update(id: string, group: DescriptionGroupCreate) {
    const response = await axiosInstance.put<DescriptionGroup>(`${API_URL}/${id}`, group)
    return response.data
  },

  async delete(id: string) {
    await axiosInstance.delete(`${API_URL}/${id}`)
  },
}
