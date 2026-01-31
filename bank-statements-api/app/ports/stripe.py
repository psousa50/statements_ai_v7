from typing import Any, Protocol


class StripeClient(Protocol):
    def create_customer(self, email: str, name: str, user_id: str) -> str: ...

    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        user_id: str,
        tier: str,
    ) -> str: ...

    def create_portal_session(self, customer_id: str) -> str: ...

    def retrieve_subscription(self, subscription_id: str) -> dict: ...

    def construct_webhook_event(self, payload: bytes, signature: str) -> Any: ...

    def get_price_id_for_tier(self, tier: str) -> str | None: ...
