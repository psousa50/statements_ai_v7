from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.models.subscription import Subscription, SubscriptionUsage


class SubscriptionRepository(ABC):
    @abstractmethod
    def create(self, subscription: Subscription) -> Subscription:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: UUID) -> Optional[Subscription]:
        pass

    @abstractmethod
    def get_by_stripe_customer_id(self, stripe_customer_id: str) -> Optional[Subscription]:
        pass

    @abstractmethod
    def get_by_stripe_subscription_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        pass

    @abstractmethod
    def update(self, subscription: Subscription) -> Subscription:
        pass

    @abstractmethod
    def delete(self, user_id: UUID) -> bool:
        pass


class SubscriptionUsageRepository(ABC):
    @abstractmethod
    def create(self, usage: SubscriptionUsage) -> SubscriptionUsage:
        pass

    @abstractmethod
    def get_by_subscription_id(self, subscription_id: UUID) -> Optional[SubscriptionUsage]:
        pass

    @abstractmethod
    def update(self, usage: SubscriptionUsage) -> SubscriptionUsage:
        pass
