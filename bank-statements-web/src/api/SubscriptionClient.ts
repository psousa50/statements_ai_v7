import axios from 'axios'

export type SubscriptionTier = 'free' | 'basic' | 'pro'
export type SubscriptionStatus = 'active' | 'cancelled' | 'past_due' | 'expired'

export interface SubscriptionLimits {
  statements_per_month: number | null
  statements_total: number | null
  ai_categorisation: boolean
  ai_rules: boolean
  ai_patterns: boolean
  ai_insights: boolean
}

export interface SubscriptionUsage {
  statements_this_month: number
  statements_total: number
  ai_calls_this_month: number
  ai_calls_total: number
}

export interface SubscriptionResponse {
  tier: SubscriptionTier
  status: SubscriptionStatus
  is_active: boolean
  limits: SubscriptionLimits
  usage: SubscriptionUsage
  current_period_end: string | null
  cancel_at_period_end: boolean
}

export interface CheckoutRequest {
  tier: SubscriptionTier
}

export interface CheckoutResponse {
  checkout_url: string
}

export interface PortalResponse {
  portal_url: string
}

export interface FeatureAccessResponse {
  allowed: boolean
  reason: string | null
  limit: number | null
  used: number | null
}

export interface SubscriptionClient {
  getSubscription(): Promise<SubscriptionResponse>
  checkFeatureAccess(feature: string): Promise<FeatureAccessResponse>
  createCheckoutSession(tier: SubscriptionTier): Promise<CheckoutResponse>
  createPortalSession(): Promise<PortalResponse>
}

const BASE_URL = import.meta.env.VITE_API_URL || ''
const API_URL = `${BASE_URL}/api/v1/subscription`

export const subscriptionClient: SubscriptionClient = {
  async getSubscription() {
    const response = await axios.get<SubscriptionResponse>(API_URL)
    return response.data
  },

  async checkFeatureAccess(feature: string) {
    const response = await axios.get<FeatureAccessResponse>(`${API_URL}/check/${feature}`)
    return response.data
  },

  async createCheckoutSession(tier: SubscriptionTier) {
    const response = await axios.post<CheckoutResponse>(`${API_URL}/checkout`, { tier })
    return response.data
  },

  async createPortalSession() {
    const response = await axios.post<PortalResponse>(`${API_URL}/portal`)
    return response.data
  },
}
