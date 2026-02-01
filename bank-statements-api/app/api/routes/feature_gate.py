from uuid import UUID

from app.api.errors import PaymentRequiredError
from app.services.subscription import Feature, SubscriptionService


def require_feature(subscription_service: SubscriptionService, user_id: UUID, feature: Feature) -> None:
    result = subscription_service.check_feature_access(user_id, feature)
    if not result.allowed:
        raise PaymentRequiredError(
            message=result.reason,
            details={
                "feature": feature.value,
                "limit": result.limit,
                "used": result.used,
            },
        )
