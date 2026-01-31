from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utc_now():
    return datetime.now(timezone.utc)


class SubscriptionTier(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"

    def __str__(self):
        return self.value


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    EXPIRED = "expired"

    def __str__(self):
        return self.value


TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "statements_per_month": 3,
        "statements_total": 10,
        "ai_categorisation": False,
        "ai_rules": False,
        "ai_patterns": False,
        "ai_insights": False,
    },
    SubscriptionTier.BASIC: {
        "statements_per_month": 50,
        "statements_total": None,
        "ai_categorisation": True,
        "ai_rules": False,
        "ai_patterns": False,
        "ai_insights": False,
    },
    SubscriptionTier.PRO: {
        "statements_per_month": None,
        "statements_total": None,
        "ai_categorisation": True,
        "ai_rules": True,
        "ai_patterns": True,
        "ai_insights": True,
    },
}


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    tier = Column(
        SQLAlchemyEnum(SubscriptionTier, name="subscriptiontier", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=SubscriptionTier.FREE,
    )
    status = Column(
        SQLAlchemyEnum(SubscriptionStatus, name="subscriptionstatus", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=SubscriptionStatus.ACTIVE,
    )

    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True)
    stripe_price_id = Column(String(255), nullable=True)

    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False)

    user = relationship("User", back_populates="subscription")
    usage = relationship("SubscriptionUsage", back_populates="subscription", uselist=False, cascade="all, delete-orphan")

    @property
    def is_active(self) -> bool:
        return self.status == SubscriptionStatus.ACTIVE

    @property
    def limits(self) -> dict:
        return TIER_LIMITS.get(self.tier, TIER_LIMITS[SubscriptionTier.FREE])

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier={self.tier}, status={self.status})>"


class SubscriptionUsage(Base):
    __tablename__ = "subscription_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    statements_this_month = Column(Integer, default=0, nullable=False)
    statements_total = Column(Integer, default=0, nullable=False)
    ai_calls_this_month = Column(Integer, default=0, nullable=False)
    ai_calls_total = Column(Integer, default=0, nullable=False)

    current_period_start = Column(DateTime(timezone=True), default=_utc_now, nullable=False)

    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False)

    subscription = relationship("Subscription", back_populates="usage")

    def reset_monthly_counters(self):
        self.statements_this_month = 0
        self.ai_calls_this_month = 0
        self.current_period_start = _utc_now()

    def increment_statements(self, count: int = 1):
        self.statements_this_month += count
        self.statements_total += count

    def increment_ai_calls(self, count: int = 1):
        self.ai_calls_this_month += count
        self.ai_calls_total += count

    def __repr__(self):
        return f"<SubscriptionUsage(id={self.id}, statements_this_month={self.statements_this_month}, statements_total={self.statements_total})>"
