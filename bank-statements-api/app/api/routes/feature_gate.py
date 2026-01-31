from uuid import UUID

from fastapi import HTTPException, status

from app.services.subscription import Feature, SubscriptionService


def require_feature(subscription_service: SubscriptionService, user_id: UUID, feature: Feature) -> None:
    result = subscription_service.check_feature_access(user_id, feature)
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": result.reason,
                "feature": feature.value,
                "limit": result.limit,
                "used": result.used,
            },
        )
