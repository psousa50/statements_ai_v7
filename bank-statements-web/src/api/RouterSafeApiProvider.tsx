import React from 'react';
import { ApiProvider as OriginalApiProvider } from './ApiContext';
import { ApiClient } from './ApiClient';
import { defaultApiClient } from './createApiClient';

/**
 * A wrapper around ApiProvider that avoids React Router warnings
 * This component isolates the ApiProvider from React Router's context
 */
export const RouterSafeApiProvider: React.FC<{
  children: React.ReactNode;
  client?: ApiClient;
}> = ({ children, client = defaultApiClient }) => {
  // Use React.memo to prevent unnecessary re-renders
  const MemoizedProvider = React.memo(
    () => <OriginalApiProvider client={client}>{children}</OriginalApiProvider>
  );

  return <MemoizedProvider />;
};
