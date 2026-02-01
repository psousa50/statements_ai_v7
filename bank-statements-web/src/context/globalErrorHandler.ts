let globalErrorHandler: ((error: unknown) => void) | null = null

export const setGlobalErrorHandler = (handler: (error: unknown) => void) => {
  globalErrorHandler = handler
}

export const getGlobalErrorHandler = () => globalErrorHandler
