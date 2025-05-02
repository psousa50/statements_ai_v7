import React, { createContext, useContext } from 'react';
import { apiClients, ApiClients } from './clients';

const ApiClientsContext = createContext<ApiClients | undefined>(undefined);

export const ApiClientsProvider = ({
  children,
  clients = apiClients,
}: {
  children: React.ReactNode;
  clients?: ApiClients;
}) => (
  <ApiClientsContext.Provider value={clients}>
    {children}
  </ApiClientsContext.Provider>
);

export const useApiClients = (): ApiClients => {
  const ctx = useContext(ApiClientsContext);
  if (!ctx)
    throw new Error('useApiClients must be used within ApiClientsProvider');
  return ctx;
};
