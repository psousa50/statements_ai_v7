export type ErrorType = 'network' | 'validation' | 'auth' | 'payment' | 'conflict' | 'not_found' | 'server'

export interface ApiError {
  code: string
  message: string
  details: Record<string, unknown>
  status: number
  type: ErrorType
}

export function isApiError(error: unknown): error is ApiError {
  return typeof error === 'object' && error !== null && 'code' in error && 'message' in error && 'type' in error
}

export function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unexpected error occurred'
}
