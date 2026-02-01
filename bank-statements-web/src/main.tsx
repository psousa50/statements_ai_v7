import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider, MutationCache } from '@tanstack/react-query'
import { AuthProvider } from './auth/AuthContext'
import { ThemeProvider } from './theme/ThemeContext'
import { ErrorProvider } from './context/ErrorContext'
import { getGlobalErrorHandler } from './context/globalErrorHandler'
import { isApiError } from './types/ApiError'
import App from './App'
import './index.css'

const mutationCache = new MutationCache({
  onError: (error) => {
    const handler = getGlobalErrorHandler()
    if (handler && isApiError(error)) {
      handler(error)
    }
  },
})

const queryClient = new QueryClient({
  mutationCache,
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ErrorProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </ErrorProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>
)
