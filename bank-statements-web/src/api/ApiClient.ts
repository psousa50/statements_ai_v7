import axios, { AxiosError, AxiosInstance } from 'axios'
import { ApiError, ErrorType } from '../types/ApiError'
import { CategoryClient } from './CategoryClient'
import { AccountClient } from './AccountClient'
import { StatementClient } from './StatementClient'
import { TransactionClient } from './TransactionClient'
import { TransactionCategorizationClient } from './TransactionCategorizationClient'
import { EnhancementRuleClient } from './EnhancementRuleClient'
import { DescriptionGroupClient } from './DescriptionGroupClient'
import { SubscriptionClient } from './SubscriptionClient'

interface BackendErrorResponse {
  code: string
  message: string
  details: Record<string, unknown>
}

function mapCodeToType(code: string, status: number): ErrorType {
  switch (code) {
    case 'NOT_FOUND':
      return 'not_found'
    case 'CONFLICT':
      return 'conflict'
    case 'VALIDATION_ERROR':
      return 'validation'
    case 'FORBIDDEN':
      return 'auth'
    case 'UNAUTHORIZED':
      return 'auth'
    case 'PAYMENT_REQUIRED':
      return 'payment'
    case 'INTERNAL_ERROR':
      return 'server'
    default:
      if (status >= 500) return 'server'
      if (status === 401 || status === 403) return 'auth'
      if (status === 402) return 'payment'
      if (status === 404) return 'not_found'
      if (status === 409) return 'conflict'
      return 'validation'
  }
}

function transformError(error: AxiosError): ApiError {
  if (!error.response) {
    return {
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to the server',
      details: {},
      status: 0,
      type: 'network',
    }
  }

  const status = error.response.status
  const data = error.response.data as BackendErrorResponse | { detail: string } | undefined

  if (data && 'code' in data) {
    return {
      code: data.code,
      message: data.message,
      details: data.details || {},
      status,
      type: mapCodeToType(data.code, status),
    }
  }

  if (data && 'detail' in data) {
    return {
      code: mapCodeToType('', status).toUpperCase(),
      message: typeof data.detail === 'string' ? data.detail : 'An error occurred',
      details: typeof data.detail === 'object' ? (data.detail as Record<string, unknown>) : {},
      status,
      type: mapCodeToType('', status),
    }
  }

  return {
    code: 'UNKNOWN_ERROR',
    message: 'An unexpected error occurred',
    details: {},
    status,
    type: status >= 500 ? 'server' : 'validation',
  }
}

const BASE_URL = import.meta.env.VITE_API_URL || ''

export const axiosInstance: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
})

axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const apiError = transformError(error)
    return Promise.reject(apiError)
  }
)

export interface ApiClient {
  transactions: TransactionClient
  transactionCategorizations: TransactionCategorizationClient
  enhancementRules: EnhancementRuleClient
  categories: CategoryClient
  statements: StatementClient
  accounts: AccountClient
  descriptionGroups: DescriptionGroupClient
  subscription: SubscriptionClient
}
