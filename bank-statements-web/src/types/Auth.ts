export interface User {
  id: string
  email: string
  name?: string
  avatar_url?: string
  oauth_provider: 'google' | 'github'
}

export interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
}
