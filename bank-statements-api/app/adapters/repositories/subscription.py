from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.subscription import Subscription, SubscriptionUsage
from app.ports.repositories.subscription import SubscriptionRepository, SubscriptionUsageRepository


class SQLAlchemySubscriptionRepository(SubscriptionRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, subscription: Subscription) -> Subscription:
        self.db_session.add(subscription)
        self.db_session.commit()
        self.db_session.refresh(subscription)
        return subscription

    def get_by_user_id(self, user_id: UUID) -> Optional[Subscription]:
        return self.db_session.query(Subscription).filter(Subscription.user_id == user_id).first()

    def get_by_stripe_customer_id(self, stripe_customer_id: str) -> Optional[Subscription]:
        return self.db_session.query(Subscription).filter(Subscription.stripe_customer_id == stripe_customer_id).first()

    def get_by_stripe_subscription_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        return self.db_session.query(Subscription).filter(Subscription.stripe_subscription_id == stripe_subscription_id).first()

    def update(self, subscription: Subscription) -> Subscription:
        self.db_session.commit()
        self.db_session.refresh(subscription)
        return subscription

    def delete(self, user_id: UUID) -> bool:
        subscription = self.get_by_user_id(user_id)
        if subscription:
            self.db_session.delete(subscription)
            self.db_session.commit()
            return True
        return False


class SQLAlchemySubscriptionUsageRepository(SubscriptionUsageRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, usage: SubscriptionUsage) -> SubscriptionUsage:
        self.db_session.add(usage)
        self.db_session.commit()
        self.db_session.refresh(usage)
        return usage

    def get_by_subscription_id(self, subscription_id: UUID) -> Optional[SubscriptionUsage]:
        return self.db_session.query(SubscriptionUsage).filter(SubscriptionUsage.subscription_id == subscription_id).first()

    def update(self, usage: SubscriptionUsage) -> SubscriptionUsage:
        self.db_session.commit()
        self.db_session.refresh(usage)
        return usage
