import axios from 'axios'
import { User } from '../types/Auth'

const BASE_URL = import.meta.env.VITE_API_URL || ''
const AUTH_URL = `${BASE_URL}/api/v1/auth`

axios.defaults.withCredentials = true

export interface RegisterRequest {
  email: string
  password: string
  name?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface AuthClient {
  getCurrentUser(): Promise<User>
  refreshToken(): Promise<void>
  logout(): Promise<void>
  register(data: RegisterRequest): Promise<User>
  login(data: LoginRequest): Promise<User>
  getGoogleAuthUrl(): string
  getGithubAuthUrl(): string
}

export const authClient: AuthClient = {
  async getCurrentUser() {
    const response = await axios.get<User>(`${AUTH_URL}/me`)
    return response.data
  },

  async refreshToken() {
    await axios.post(`${AUTH_URL}/refresh`)
  },

  async logout() {
    await axios.post(`${AUTH_URL}/logout`)
  },

  async register(data: RegisterRequest) {
    const response = await axios.post<User>(`${AUTH_URL}/register`, data)
    return response.data
  },

  async login(data: LoginRequest) {
    const response = await axios.post<User>(`${AUTH_URL}/login`, data)
    return response.data
  },

  getGoogleAuthUrl() {
    return `${AUTH_URL}/google`
  },

  getGithubAuthUrl() {
    return `${AUTH_URL}/github`
  },
}
