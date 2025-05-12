import React, { createContext, useContext } from 'react'
import { ApiClient } from './ApiClient'
import { defaultApiClient } from './createApiClient'

const ApiContext = createContext<ApiClient | undefined>(undefined)

export const ApiProvider = ({
  children,
  client = defaultApiClient,
}: {
  children: React.ReactNode
  client?: ApiClient
}) => <ApiContext.Provider value={client}>{children}</ApiContext.Provider>

export const useApi = (): ApiClient => {
  const ctx = useContext(ApiContext)
  if (!ctx) throw new Error('useApi must be used within ApiProvider')
  return ctx
}
