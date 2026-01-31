from typing import Any, Optional

import stripe

from app.ports.stripe import StripeClient


class StripeSDKClient(StripeClient):
    def __init__(
        self,
        api_key: str,
        webhook_secret: Optional[str],
        web_base_url: str,
        price_id_basic: Optional[str],
        price_id_pro: Optional[str],
    ):
        self.webhook_secret = webhook_secret
        self.web_base_url = web_base_url
        self.price_id_basic = price_id_basic
        self.price_id_pro = price_id_pro
        stripe.api_key = api_key

    def create_customer(self, email: str, name: str, user_id: str) -> str:
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"user_id": user_id},
        )
        return customer.id

    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        user_id: str,
        tier: str,
    ) -> str:
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{self.web_base_url}/settings/billing?success=true",
            cancel_url=f"{self.web_base_url}/settings/billing?cancelled=true",
            metadata={"user_id": user_id, "tier": tier},
        )
        return checkout_session.url

    def create_portal_session(self, customer_id: str) -> str:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{self.web_base_url}/settings/billing",
        )
        return portal_session.url

    def retrieve_subscription(self, subscription_id: str) -> dict:
        return stripe.Subscription.retrieve(subscription_id)

    def construct_webhook_event(self, payload: bytes, signature: str) -> Any:
        if not self.webhook_secret:
            raise ValueError("Stripe webhook secret not configured")
        return stripe.Webhook.construct_event(payload, signature, self.webhook_secret)

    def get_price_id_for_tier(self, tier: str) -> Optional[str]:
        if tier == "basic":
            return self.price_id_basic
        elif tier == "pro":
            return self.price_id_pro
        return None
