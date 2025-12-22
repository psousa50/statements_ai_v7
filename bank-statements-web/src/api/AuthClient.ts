import axios from 'axios'
import { User } from '../types/Auth'

const BASE_URL = import.meta.env.VITE_API_URL || ''
const AUTH_URL = `${BASE_URL}/api/v1/auth`

axios.defaults.withCredentials = true

export interface AuthClient {
  getCurrentUser(): Promise<User>
  refreshToken(): Promise<void>
  logout(): Promise<void>
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

  getGoogleAuthUrl() {
    return `${AUTH_URL}/google`
  },

  getGithubAuthUrl() {
    return `${AUTH_URL}/github`
  },
}
