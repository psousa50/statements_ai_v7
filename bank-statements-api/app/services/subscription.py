from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID

from app.domain.models.subscription import (
    TIER_LIMITS,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    SubscriptionUsage,
)
from app.domain.models.user import User
from app.ports.repositories.subscription import SubscriptionRepository, SubscriptionUsageRepository
from app.ports.repositories.user import UserRepository
from app.ports.stripe import StripeClient


class Feature(str, Enum):
    STATEMENT_UPLOAD = "statement_upload"
    AI_CATEGORISATION = "ai_categorisation"
    AI_RULES = "ai_rules"
    AI_PATTERNS = "ai_patterns"
    AI_INSIGHTS = "ai_insights"


@dataclass
class FeatureAccessResult:
    allowed: bool
    reason: Optional[str] = None
    limit: Optional[int] = None
    used: Optional[int] = None


@dataclass
class SubscriptionInfo:
    tier: SubscriptionTier
    status: SubscriptionStatus
    is_active: bool
    limits: dict
    usage: dict
    stripe_customer_id: Optional[str]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool


class SubscriptionService:
    def __init__(
        self,
        subscription_repository: SubscriptionRepository,
        subscription_usage_repository: SubscriptionUsageRepository,
        user_repository: UserRepository,
        stripe_client: StripeClient,
    ):
        self.subscription_repository = subscription_repository
        self.subscription_usage_repository = subscription_usage_repository
        self.user_repository = user_repository
        self.stripe_client = stripe_client

    def get_or_create_subscription(self, user_id: UUID) -> Subscription:
        subscription = self.subscription_repository.get_by_user_id(user_id)
        if subscription:
            return subscription

        subscription = Subscription(
            user_id=user_id,
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
        )
        subscription = self.subscription_repository.create(subscription)

        usage = SubscriptionUsage(subscription_id=subscription.id)
        self.subscription_usage_repository.create(usage)

        return subscription

    def get_subscription_info(self, user_id: UUID) -> SubscriptionInfo:
        user = self.user_repository.get_by_id(user_id)
        subscription = self.get_or_create_subscription(user_id)
        usage = self.subscription_usage_repository.get_by_subscription_id(subscription.id)

        effective_tier = self._get_effective_tier(user, subscription)
        limits = TIER_LIMITS.get(effective_tier, TIER_LIMITS[SubscriptionTier.FREE])

        return SubscriptionInfo(
            tier=effective_tier,
            status=subscription.status,
            is_active=subscription.is_active,
            limits=limits,
            usage={
                "statements_this_month": usage.statements_this_month if usage else 0,
                "statements_total": usage.statements_total if usage else 0,
                "ai_calls_this_month": usage.ai_calls_this_month if usage else 0,
                "ai_calls_total": usage.ai_calls_total if usage else 0,
            },
            stripe_customer_id=subscription.stripe_customer_id,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancelled_at is not None,
        )

    def _get_effective_tier(self, user: User, subscription: Subscription) -> SubscriptionTier:
        if user.tier_override:
            try:
                return SubscriptionTier(user.tier_override)
            except ValueError:
                pass
        return subscription.tier

    def check_feature_access(self, user_id: UUID, feature: Feature) -> FeatureAccessResult:
        user = self.user_repository.get_by_id(user_id)
        subscription = self.get_or_create_subscription(user_id)
        usage = self.subscription_usage_repository.get_by_subscription_id(subscription.id)

        self._maybe_reset_monthly_counters(usage)

        effective_tier = self._get_effective_tier(user, subscription)
        limits = TIER_LIMITS.get(effective_tier, TIER_LIMITS[SubscriptionTier.FREE])

        if feature == Feature.STATEMENT_UPLOAD:
            return self._check_statement_upload_access(limits, usage)

        return self._check_ai_feature_access(limits, feature.value)

    def _check_statement_upload_access(self, limits: dict, usage: SubscriptionUsage) -> FeatureAccessResult:
        statements_per_month = limits.get("statements_per_month")
        statements_total = limits.get("statements_total")

        if statements_total is not None and usage.statements_total >= statements_total:
            return FeatureAccessResult(
                allowed=False,
                reason="You've reached your total statement limit. Upgrade to upload more.",
                limit=statements_total,
                used=usage.statements_total,
            )

        if statements_per_month is not None and usage.statements_this_month >= statements_per_month:
            return FeatureAccessResult(
                allowed=False,
                reason="You've reached your monthly statement limit. Upgrade or wait until next month.",
                limit=statements_per_month,
                used=usage.statements_this_month,
            )

        return FeatureAccessResult(allowed=True)

    def _check_ai_feature_access(self, limits: dict, feature_key: str) -> FeatureAccessResult:
        if not limits.get(feature_key, False):
            return FeatureAccessResult(
                allowed=False,
                reason="This feature requires a paid subscription. Upgrade to access AI features.",
            )
        return FeatureAccessResult(allowed=True)

    def _maybe_reset_monthly_counters(self, usage: SubscriptionUsage) -> None:
        if not usage:
            return

        now = datetime.now(timezone.utc)
        period_start = usage.current_period_start

        if period_start.month != now.month or period_start.year != now.year:
            usage.reset_monthly_counters()
            self.subscription_usage_repository.update(usage)

    def increment_statement_usage(self, user_id: UUID, count: int = 1) -> None:
        subscription = self.get_or_create_subscription(user_id)
        usage = self.subscription_usage_repository.get_by_subscription_id(subscription.id)
        if usage:
            self._maybe_reset_monthly_counters(usage)
            usage.increment_statements(count)
            self.subscription_usage_repository.update(usage)

    def increment_ai_usage(self, user_id: UUID, count: int = 1) -> None:
        subscription = self.get_or_create_subscription(user_id)
        usage = self.subscription_usage_repository.get_by_subscription_id(subscription.id)
        if usage:
            self._maybe_reset_monthly_counters(usage)
            usage.increment_ai_calls(count)
            self.subscription_usage_repository.update(usage)

    def create_checkout_session(self, user_id: UUID, tier: SubscriptionTier) -> str:
        user = self.user_repository.get_by_id(user_id)
        subscription = self.get_or_create_subscription(user_id)

        price_id = self.stripe_client.get_price_id_for_tier(tier.value)
        if not price_id:
            raise ValueError(f"No price configured for tier {tier}")

        if not subscription.stripe_customer_id:
            customer_id = self.stripe_client.create_customer(
                email=user.email,
                name=user.name,
                user_id=str(user_id),
            )
            subscription.stripe_customer_id = customer_id
            self.subscription_repository.update(subscription)

        checkout_url = self.stripe_client.create_checkout_session(
            customer_id=subscription.stripe_customer_id,
            price_id=price_id,
            user_id=str(user_id),
            tier=tier.value,
        )

        return checkout_url

    def create_portal_session(self, user_id: UUID) -> str:
        subscription = self.get_or_create_subscription(user_id)

        if not subscription.stripe_customer_id:
            raise ValueError("No billing account found. Please subscribe first.")

        portal_url = self.stripe_client.create_portal_session(subscription.stripe_customer_id)
        return portal_url

    def handle_webhook_event(self, payload: bytes, signature: str) -> None:
        event = self.stripe_client.construct_webhook_event(payload, signature)

        if event.type == "checkout.session.completed":
            self._handle_checkout_completed(event.data.object)
        elif event.type == "customer.subscription.updated":
            self._handle_subscription_updated(event.data.object)
        elif event.type == "customer.subscription.deleted":
            self._handle_subscription_deleted(event.data.object)
        elif event.type == "invoice.payment_failed":
            self._handle_payment_failed(event.data.object)

    def _handle_checkout_completed(self, session) -> None:
        stripe_subscription_id = session.subscription
        customer_id = session.customer
        metadata = session.metadata or {}
        tier_value = metadata.get("tier", "basic")

        try:
            tier = SubscriptionTier(tier_value)
        except ValueError:
            tier = SubscriptionTier.BASIC

        subscription = self.subscription_repository.get_by_stripe_customer_id(customer_id)
        if not subscription:
            return

        stripe_sub = self.stripe_client.retrieve_subscription(stripe_subscription_id)

        subscription.stripe_subscription_id = stripe_subscription_id
        subscription.tier = tier
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.cancelled_at = None

        try:
            if stripe_sub.get("items") and stripe_sub["items"].get("data"):
                subscription.stripe_price_id = stripe_sub["items"]["data"][0]["price"]["id"]
        except (KeyError, TypeError, IndexError):
            pass

        try:
            period_start = stripe_sub.get("current_period_start")
            period_end = stripe_sub.get("current_period_end")
            if period_start:
                subscription.current_period_start = datetime.fromtimestamp(period_start, tz=timezone.utc)
            if period_end:
                subscription.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
        except (KeyError, TypeError):
            pass

        self.subscription_repository.update(subscription)

    def _handle_subscription_updated(self, stripe_sub) -> None:
        sub_id = stripe_sub.get("id") if isinstance(stripe_sub, dict) else getattr(stripe_sub, "id", None)
        if not sub_id:
            return

        subscription = self.subscription_repository.get_by_stripe_subscription_id(sub_id)
        if not subscription:
            return

        try:
            if isinstance(stripe_sub, dict):
                period_start = stripe_sub.get("current_period_start")
                period_end = stripe_sub.get("current_period_end")
                status = stripe_sub.get("status")
                cancel_at_period_end = stripe_sub.get("cancel_at_period_end", False)
            else:
                period_start = getattr(stripe_sub, "current_period_start", None)
                period_end = getattr(stripe_sub, "current_period_end", None)
                status = getattr(stripe_sub, "status", None)
                cancel_at_period_end = getattr(stripe_sub, "cancel_at_period_end", False)

            if period_start:
                subscription.current_period_start = datetime.fromtimestamp(period_start, tz=timezone.utc)
            if period_end:
                subscription.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)

            if status == "active":
                subscription.status = SubscriptionStatus.ACTIVE
            elif status == "past_due":
                subscription.status = SubscriptionStatus.PAST_DUE
            elif status in ("canceled", "unpaid"):
                subscription.status = SubscriptionStatus.CANCELLED

            if cancel_at_period_end:
                subscription.cancelled_at = datetime.now(timezone.utc)
            else:
                subscription.cancelled_at = None

            if isinstance(stripe_sub, dict):
                items = stripe_sub.get("items", {})
                data = items.get("data", []) if isinstance(items, dict) else []
            else:
                items = getattr(stripe_sub, "items", None)
                data = getattr(items, "data", []) if items else []

            if data:
                price_info = data[0]
                if isinstance(price_info, dict):
                    new_price_id = price_info.get("price", {}).get("id")
                else:
                    new_price_id = getattr(getattr(price_info, "price", None), "id", None)
                if new_price_id:
                    subscription.stripe_price_id = new_price_id
                    subscription.tier = self._get_tier_for_price_id(new_price_id)
        except Exception:
            pass

        self.subscription_repository.update(subscription)

    def _handle_subscription_deleted(self, stripe_sub) -> None:
        subscription = self.subscription_repository.get_by_stripe_subscription_id(stripe_sub.id)
        if not subscription:
            return

        subscription.tier = SubscriptionTier.FREE
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.stripe_subscription_id = None
        subscription.stripe_price_id = None
        subscription.current_period_start = None
        subscription.current_period_end = None
        subscription.cancelled_at = datetime.now(timezone.utc)

        self.subscription_repository.update(subscription)

    def _handle_payment_failed(self, invoice) -> None:
        customer_id = invoice.customer
        subscription = self.subscription_repository.get_by_stripe_customer_id(customer_id)
        if not subscription:
            return

        subscription.status = SubscriptionStatus.PAST_DUE
        self.subscription_repository.update(subscription)

    def _get_tier_for_price_id(self, price_id: str) -> SubscriptionTier:
        basic_price = self.stripe_client.get_price_id_for_tier("basic")
        pro_price = self.stripe_client.get_price_id_for_tier("pro")
        if price_id == basic_price:
            return SubscriptionTier.BASIC
        elif price_id == pro_price:
            return SubscriptionTier.PRO
        return SubscriptionTier.FREE

    def sync_from_stripe(self, user_id: UUID) -> None:
        subscription = self.subscription_repository.get_by_user_id(user_id)
        if not subscription or not subscription.stripe_subscription_id:
            return

        try:
            stripe_sub = self.stripe_client.retrieve_subscription(subscription.stripe_subscription_id)
            self._handle_subscription_updated(stripe_sub)
        except Exception:
            subscription.tier = SubscriptionTier.FREE
            subscription.status = SubscriptionStatus.EXPIRED
            subscription.stripe_subscription_id = None
            self.subscription_repository.update(subscription)
