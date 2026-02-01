import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { ApiError, isApiError } from '../types/ApiError'
import { Toast } from '../components/Toast'
import { SubscriptionErrorDialog } from '../components/SubscriptionErrorDialog'
import { setGlobalErrorHandler } from './globalErrorHandler'

interface ErrorContextValue {
  showError: (error: ApiError | Error | unknown) => void
  clearError: () => void
}

const ErrorContext = createContext<ErrorContextValue | undefined>(undefined)

export const ErrorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toastError, setToastError] = useState<ApiError | null>(null)
  const [subscriptionError, setSubscriptionError] = useState<ApiError | null>(null)

  const showError = useCallback((error: ApiError | Error | unknown) => {
    if (isApiError(error)) {
      if (error.type === 'payment') {
        setSubscriptionError(error)
      } else {
        setToastError(error)
      }
    } else if (error instanceof Error) {
      setToastError({
        code: 'UNKNOWN_ERROR',
        message: error.message,
        details: {},
        status: 0,
        type: 'validation',
      })
    }
  }, [])

  const clearError = useCallback(() => {
    setToastError(null)
    setSubscriptionError(null)
  }, [])

  useEffect(() => {
    setGlobalErrorHandler(showError)
    return () => setGlobalErrorHandler(() => {})
  }, [showError])

  return (
    <ErrorContext.Provider value={{ showError, clearError }}>
      {children}
      {toastError && <Toast message={toastError.message} type="error" onClose={() => setToastError(null)} />}
      {subscriptionError && (
        <SubscriptionErrorDialog error={subscriptionError} onClose={() => setSubscriptionError(null)} />
      )}
    </ErrorContext.Provider>
  )
}

export const useError = (): ErrorContextValue => {
  const context = useContext(ErrorContext)
  if (!context) {
    throw new Error('useError must be used within ErrorProvider')
  }
  return context
}
