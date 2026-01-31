import { useState, useCallback, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useSubscription } from '../services/hooks/useSubscription'
import { Toast, ToastProps } from '../components/Toast'
import { Button, LinearProgress, Chip } from '@mui/material'
import CheckIcon from '@mui/icons-material/Check'
import CloseIcon from '@mui/icons-material/Close'
import './BillingPage.css'

const TIER_INFO = {
  free: {
    name: 'Free',
    price: '€0',
    period: 'forever',
    features: [
      { name: '10 statements total', included: true },
      { name: '3 statements per month', included: true },
      { name: 'AI categorisation', included: false },
      { name: 'AI rule suggestions', included: false },
      { name: 'Recurring pattern detection', included: false },
    ],
  },
  basic: {
    name: 'Basic Plan',
    price: '€5',
    period: 'per month',
    features: [
      { name: '50 statements per month', included: true },
      { name: 'Unlimited total statements', included: true },
      { name: 'AI categorisation', included: true },
      { name: 'AI rule suggestions', included: false },
      { name: 'Recurring pattern detection', included: false },
    ],
  },
  pro: {
    name: 'Pro Plan',
    price: '€9',
    period: 'per month',
    features: [
      { name: 'Unlimited statements', included: true },
      { name: 'Unlimited total statements', included: true },
      { name: 'AI categorisation', included: true },
      { name: 'AI rule suggestions', included: true },
      { name: 'Recurring pattern detection', included: true },
    ],
  },
}

export const BillingPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [toast, setToast] = useState<Omit<ToastProps, 'onClose'> | null>(null)
  const { subscription, loading, error, startCheckout, openBillingPortal, refreshSubscription } = useSubscription()

  useEffect(() => {
    if (searchParams.get('success') === 'true') {
      setToast({ message: 'Subscription updated successfully!', type: 'success' })
      setSearchParams({})
      refreshSubscription()
    } else if (searchParams.get('cancelled') === 'true') {
      setToast({ message: 'Checkout cancelled', type: 'info' })
      setSearchParams({})
    }
  }, [searchParams, setSearchParams, refreshSubscription])

  const handleUpgrade = useCallback(
    async (tier: 'basic' | 'pro') => {
      const success = await startCheckout(tier)
      if (!success) {
        setToast({ message: 'Failed to start checkout. Please try again.', type: 'error' })
      }
    },
    [startCheckout]
  )

  const handleManageBilling = useCallback(async () => {
    const success = await openBillingPortal()
    if (!success) {
      setToast({ message: 'Failed to open billing portal. Please try again.', type: 'error' })
    }
  }, [openBillingPortal])

  const handleCloseToast = useCallback(() => {
    setToast(null)
  }, [])

  const currentTier = subscription?.tier ?? 'free'
  const currentTierInfo = TIER_INFO[currentTier]

  const getUsagePercent = (used: number, limit: number | null) => {
    if (limit === null) return 0
    return Math.min((used / limit) * 100, 100)
  }

  return (
    <div className="billing-page">
      <header className="page-header">
        <h1>Billing & Subscription</h1>
        <p className="page-description">Manage your subscription plan and usage</p>
      </header>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading ? (
        <div className="loading-message">Loading subscription...</div>
      ) : (
        <>
          <section className="current-plan-section">
            <h2>Current Plan</h2>
            <div className="current-plan-card">
              <div className="plan-info">
                <div className="plan-name-row">
                  <span className="plan-name">{currentTierInfo.name}</span>
                  {subscription?.cancel_at_period_end && <Chip label="Cancelling" size="small" color="warning" />}
                </div>
                <span className="plan-price">
                  {currentTierInfo.price} <span className="price-period">{currentTierInfo.period}</span>
                </span>
              </div>

              {subscription && currentTier !== 'free' && (
                <div className="billing-actions">
                  <Button variant="outlined" onClick={handleManageBilling} sx={{ textTransform: 'none' }}>
                    Manage Billing
                  </Button>
                </div>
              )}
            </div>

            {subscription?.cancel_at_period_end && subscription.current_period_end && (
              <div className="cancellation-notice">
                Your subscription is cancelled. You'll have access until{' '}
                {new Date(subscription.current_period_end).toLocaleDateString('en-GB', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric',
                })}
                .
              </div>
            )}
          </section>

          {subscription && (
            <section className="usage-section">
              <h2>Usage</h2>
              <div className="usage-cards">
                <div className="usage-card">
                  <div className="usage-header">
                    <span className="usage-label">Statements this month</span>
                    <span className="usage-value">
                      {subscription.usage.statements_this_month}
                      {subscription.limits.statements_per_month !== null &&
                        ` / ${subscription.limits.statements_per_month}`}
                    </span>
                  </div>
                  {subscription.limits.statements_per_month !== null && (
                    <LinearProgress
                      variant="determinate"
                      value={getUsagePercent(
                        subscription.usage.statements_this_month,
                        subscription.limits.statements_per_month
                      )}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  )}
                </div>

                {subscription.limits.statements_total !== null && (
                  <div className="usage-card">
                    <div className="usage-header">
                      <span className="usage-label">Total statements</span>
                      <span className="usage-value">
                        {subscription.usage.statements_total} / {subscription.limits.statements_total}
                      </span>
                    </div>
                    <LinearProgress
                      variant="determinate"
                      value={getUsagePercent(subscription.usage.statements_total, subscription.limits.statements_total)}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </div>
                )}
              </div>
            </section>
          )}

          <section className="plans-section">
            <h2>Available Plans</h2>
            <div className="plans-grid">
              {(
                Object.entries(TIER_INFO) as [keyof typeof TIER_INFO, (typeof TIER_INFO)[keyof typeof TIER_INFO]][]
              ).map(([tier, info]) => (
                <div key={tier} className={`plan-card ${tier === currentTier ? 'current' : ''}`}>
                  <div className="plan-card-header">
                    <h3>{info.name}</h3>
                    <div className="plan-price-block">
                      <span className="price">{info.price}</span>
                      <span className="period">{info.period}</span>
                    </div>
                  </div>
                  <ul className="plan-features">
                    {info.features.map((feature, idx) => (
                      <li key={idx} className={feature.included ? 'included' : 'excluded'}>
                        {feature.included ? (
                          <CheckIcon fontSize="small" className="feature-icon included" />
                        ) : (
                          <CloseIcon fontSize="small" className="feature-icon excluded" />
                        )}
                        {feature.name}
                      </li>
                    ))}
                  </ul>
                  <div className="plan-card-footer">
                    {tier === currentTier ? (
                      <Button variant="outlined" disabled sx={{ textTransform: 'none' }}>
                        Current Plan
                      </Button>
                    ) : tier === 'free' ? (
                      currentTier !== 'free' && (
                        <Button variant="outlined" onClick={handleManageBilling} sx={{ textTransform: 'none' }}>
                          Downgrade
                        </Button>
                      )
                    ) : (
                      <Button
                        variant="contained"
                        onClick={() => handleUpgrade(tier as 'basic' | 'pro')}
                        sx={{ textTransform: 'none' }}
                      >
                        {currentTier === 'free' ? 'Upgrade' : tier === 'pro' ? 'Upgrade' : 'Downgrade'}
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}

      {toast && <Toast message={toast.message} type={toast.type} onClose={handleCloseToast} />}
    </div>
  )
}
