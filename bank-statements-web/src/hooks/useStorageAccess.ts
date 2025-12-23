import { useState, useEffect, useCallback } from 'react'

const isIOS = (): boolean => {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent
  return (
    /iPad|iPhone|iPod/.test(ua) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
  )
}

const hasStorageAccessAPI = (): boolean => {
  return typeof document !== 'undefined' && 'hasStorageAccess' in document
}

interface StorageAccessState {
  needsPrompt: boolean
  isReady: boolean
  isChecking: boolean
  requestAccess: () => Promise<void>
}

export const useStorageAccess = (): StorageAccessState => {
  const [needsPrompt, setNeedsPrompt] = useState(false)
  const [isReady, setIsReady] = useState(false)
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    const checkAccess = async () => {
      if (!isIOS() || !hasStorageAccessAPI()) {
        setIsReady(true)
        setIsChecking(false)
        return
      }

      try {
        const hasAccess = await document.hasStorageAccess()
        if (hasAccess) {
          setIsReady(true)
        } else {
          setNeedsPrompt(true)
        }
      } catch {
        setIsReady(true)
      }
      setIsChecking(false)
    }

    checkAccess()
  }, [])

  const requestAccess = useCallback(async () => {
    if (!hasStorageAccessAPI()) {
      setIsReady(true)
      setNeedsPrompt(false)
      return
    }

    try {
      await document.requestStorageAccess()
    } catch {
      // User denied or API failed - proceed anyway
    }
    setIsReady(true)
    setNeedsPrompt(false)
  }, [])

  return { needsPrompt, isReady, isChecking, requestAccess }
}
