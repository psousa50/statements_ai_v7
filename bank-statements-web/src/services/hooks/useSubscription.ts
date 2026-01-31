import { useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useApi } from '../../api/ApiContext'
import { SubscriptionTier } from '../../api/SubscriptionClient'

export const SUBSCRIPTION_QUERY_KEYS = {
  all: ['subscription'] as const,
  subscription: ['subscription', 'details'] as const,
}

export const useSubscription = () => {
  const api = useApi()
  const queryClient = useQueryClient()

  const subscriptionQuery = useQuery({
    queryKey: SUBSCRIPTION_QUERY_KEYS.subscription,
    queryFn: async () => api.subscription.getSubscription(),
  })

  const checkoutMutation = useMutation({
    mutationFn: async (tier: SubscriptionTier) => {
      return api.subscription.createCheckoutSession(tier)
    },
  })

  const portalMutation = useMutation({
    mutationFn: async () => {
      return api.subscription.createPortalSession()
    },
  })

  const startCheckout = useCallback(
    async (tier: SubscriptionTier) => {
      try {
        const result = await checkoutMutation.mutateAsync(tier)
        window.location.href = result.checkout_url
        return true
      } catch {
        return false
      }
    },
    [checkoutMutation]
  )

  const openBillingPortal = useCallback(async () => {
    try {
      const result = await portalMutation.mutateAsync()
      window.location.href = result.portal_url
      return true
    } catch {
      return false
    }
  }, [portalMutation])

  const refreshSubscription = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: SUBSCRIPTION_QUERY_KEYS.subscription })
  }, [queryClient])

  const loading = subscriptionQuery.isLoading || checkoutMutation.isPending || portalMutation.isPending

  const error =
    subscriptionQuery.error?.message || checkoutMutation.error?.message || portalMutation.error?.message || null

  const subscription = subscriptionQuery.data

  const canUploadStatements = useCallback(() => {
    if (!subscription) return true
    const { limits, usage } = subscription
    if (limits.statements_total !== null && usage.statements_total >= limits.statements_total) {
      return false
    }
    if (limits.statements_per_month !== null && usage.statements_this_month >= limits.statements_per_month) {
      return false
    }
    return true
  }, [subscription])

  const hasAIAccess = useCallback(
    (feature: 'categorisation' | 'rules' | 'patterns' | 'insights') => {
      if (!subscription) return false
      const featureKey = `ai_${feature}` as keyof typeof subscription.limits
      return subscription.limits[featureKey] === true
    },
    [subscription]
  )

  return {
    subscription,
    loading,
    error,
    startCheckout,
    openBillingPortal,
    refreshSubscription,
    canUploadStatements,
    hasAIAccess,
    isLoaded: !subscriptionQuery.isLoading,
  }
}
